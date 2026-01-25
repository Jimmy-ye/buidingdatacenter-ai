# PostgreSQL + SQLAlchemy 与 Python 代码关系详解

## 📖 概述

本文档详细说明 PostgreSQL、SQLAlchemy 和您的 Python 代码之间的关系，以及它们是如何协同工作的。

---

## 三层架构关系

### 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                    Python 应用层                          │
│            (FastAPI + 业务逻辑代码)                        │
│  services/backend/app/api/v1/*.py                       │
│                                                         │
│  使用 Python 对象操作，不需要写 SQL                       │
│  例如: building.name = "新名称"                         │
└────────────────────┬────────────────────────────────────┘
                     │ 调用
                     ↓
┌─────────────────────────────────────────────────────────┐
│                  SQLAlchemy ORM 层                       │
│              (对象关系映射框架)                           │
│  shared/db/models_project.py                            │
│                                                         │
│  将 Python 对象映射到数据库表                            │
│  自动生成 SQL 语句                                       │
└────────────────────┬────────────────────────────────────┘
                     │ 翻译成 SQL
                     ↓
┌─────────────────────────────────────────────────────────┐
│                PostgreSQL 数据库层                        │
│              (实际存储数据的地方)                         │
│                                                         │
│  执行 SQL 语句，存储和检索数据                            │
│  例如: SELECT * FROM buildings WHERE id = '...'        │
└─────────────────────────────────────────────────────────┘
```

---

## 各层详细说明

### 1. 数据库层（PostgreSQL）

**职责**: 实际存储和管理数据

**位置**: PostgreSQL 服务器（localhost:5432）

**核心功能**:
- 数据持久化（数据不会丢失）
- 事务支持（ACID 特性）
- 并发控制（多用户同时访问）
- 数据完整性约束（外键、唯一性等）

**实际表结构**:

```sql
-- 这是 PostgreSQL 中的实际表结构
CREATE TABLE buildings (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    usage_type VARCHAR(100),
    floor_area DOUBLE PRECISION,
    gfa_area DOUBLE PRECISION,      -- 新增列
    year_built DOUBLE PRECISION,
    tags JSONB
);

CREATE INDEX ix_buildings_project_id ON buildings(project_id);
```

**高级特性**:

| 特性 | 说明 | 应用场景 |
|------|------|----------|
| UUID 类型 | 原生支持 UUID，自动生成主键 | 所有表的主键 |
| JSONB 类型 | 存储 JSON 数据，支持索引查询 | tags 字段、配置信息 |
| 外键约束 | 保证数据引用完整性 | project_id → projects.id |
| 级联删除 | 删除父记录时自动删除子记录 | ON DELETE CASCADE |
| 事务支持 | 保证一组操作的原子性 | 金融转账、批量更新 |

---

### 2. ORM 层（SQLAlchemy）

**职责**: Python 对象与数据库之间的翻译官

**位置**: `shared/db/models_project.py`

**核心文件**:

```
shared/db/
├── base.py              # SQLAlchemy 声明式基类（引擎配置）
├── session.py           # 数据库会话管理（连接池）
└── models_project.py    # 项目相关模型定义
```

**ORM 模型示例**:

```python
# shared/db/models_project.py

from sqlalchemy import Column, Float, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import Base

class Building(Base):  # ← Python 类
    __tablename__ = "buildings"  # ← 映射到 PostgreSQL 的表

    # Python 属性 ← 映射到 → 数据库列
    id = Column(UUID(as_uuid=True), primary_key=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    name = Column(String(200), nullable=False)  # ← VARCHAR(200)
    usage_type = Column(String(100))           # ← VARCHAR(100)
    floor_area = Column(Float)                  # ← DOUBLE PRECISION
    gfa_area = Column(Float)                    # ← DOUBLE PRECISION (新增)
    year_built = Column(Float)                  # ← DOUBLE PRECISION
    tags = Column(JSONB)                        # ← JSONB 类型

    # 关系映射
    project = relationship("Project", back_populates="buildings")
    zones = relationship("Zone", back_populates="building")
    systems = relationship("BuildingSystem", back_populates="building")
```

**SQLAlchemy 如何工作**:

```python
# 您写的代码（Python）
building = Building(name="A座办公楼", floor_area=50000.0)
db.add(building)
db.commit()

# SQLAlchemy 自动翻译成
BEGIN;
INSERT INTO buildings (name, floor_area, id)
VALUES ('A座办公楼', 50000.0, gen_random_uuid())
RETURNING id;
COMMIT;
```

**核心组件**:

| 组件 | 文件 | 作用 |
|------|------|------|
| Base | base.py | 所有模型的基类，提供元数据 |
| engine | session.py | 数据库连接引擎，维护连接池 |
| SessionLocal | session.py | 会话工厂，创建数据库会话 |
| get_db() | session.py | FastAPI 依赖注入，提供会话 |

**连接池工作原理**:

```python
# session.py
engine = create_engine(
    "postgresql://...",
    pool_size=5,           # 连接池大小
    max_overflow=10        # 最大溢出连接数
)

# 引擎维护的连接池:
# ┌─────────┬─────────┬─────────┬─────────┬─────────┐
# │ 连接1   │ 连接2   │ 连接3   │ 连接4   │ 连接5   │
# └─────────┴─────────┴─────────┴─────────┴─────────┘
#                    ↑
#          调用 SessionLocal() 时从池中取一个连接
#                    ↓
#          db.close() 时归还连接池
```

---

### 3. 应用层（Python 业务代码）

**职责**: 业务逻辑，操作 Python 对象

**位置**: `services/backend/app/api/v1/engineering.py`

**实际使用示例**:

```python
# services/backend/app/api/v1/engineering.py

from sqlalchemy.orm import Session
from shared.db.models_project import Building

@router.post("/projects/{project_id}/buildings")
async def create_building(
    project_id: uuid.UUID,
    payload: BuildingCreate,
    db: Session = Depends(get_db),
):
    # ┌─────────────────────────────────────────┐
    # │ 您的代码操作 Python 对象                  │
    # └─────────────────────────────────────────┘

    # 创建 Python 对象
    building = Building(
        project_id=project_id,
        name=payload.name,         # ← Python 属性
        usage_type=payload.usage_type,
        floor_area=payload.floor_area,
        gfa_area=payload.gfa_area,  # ← 新字段
        year_built=payload.year_built,
        tags=payload.tags,
    )

    # 添加到会话（此时还没写入数据库）
    db.add(building)

    # ┌─────────────────────────────────────────┐
    # │ SQLAlchemy 自动做这些事：                 │
    # └─────────────────────────────────────────┘
    # 1. 生成 SQL: INSERT INTO buildings (...)
    # 2. 连接到 PostgreSQL
    # 3. 执行 SQL
    # 4. 获取返回的 ID

    db.commit()  # ← 这里才真正写入数据库
    db.refresh(building)  # ← 刷新对象（获取数据库生成的值）

    return building  # ← 返回 Python 对象
```

---

## 完整执行流程

### 场景：创建一个建筑

**您的代码**:
```python
# services/backend/app/api/v1/engineering.py

building = Building(
    name="A座办公楼",
    floor_area=50000.0,
    gfa_area=52000.0,
)
db.add(building)
db.commit()
```

**SQLAlchemy 自动转换为**:
```sql
-- PostgreSQL 执行的 SQL
INSERT INTO buildings (
    name, floor_area, gfa_area, id
) VALUES (
    'A座办公楼', 50000.0, 52000.0, gen_random_uuid()
) RETURNING id;
```

**PostgreSQL 执行**:
- 在 `buildings` 表中插入一行数据
- 返回生成的 UUID

**流程图**:

```
┌─────────────────────────────────────────────────────────────┐
│  您的代码 (engineering.py)                                  │
│                                                             │
│  building = Building(name="A座办公楼", ...)                │
│  db.add(building)                                          │
└──────────────────────┬──────────────────────────────────────┘
                       ↓ SQLAlchemy 翻译
┌──────────────────────────────────────────────────────────────┐
│  ORM 层 (models_project.py)                                 │
│                                                             │
│  Building 类 → buildings 表                                 │
│  Python 对象 → SQL INSERT 语句                              │
└──────────────────────┬──────────────────────────────────────┘
                       ↓ 发送 SQL
┌──────────────────────────────────────────────────────────────┐
│  数据库层 (PostgreSQL)                                      │
│                                                             │
│  执行 INSERT 语句                                           │
│  存储数据到磁盘                                              │
│  返回生成的 UUID                                            │
└──────────────────────┬──────────────────────────────────────┘
                       ↓ 返回结果
┌──────────────────────────────────────────────────────────────┐
│  ORM 层                                                     │
│                                                             │
│  将返回的 UUID 赋值给 building.id                           │
└──────────────────────┬──────────────────────────────────────┘
                       ↓ 返回对象
┌──────────────────────────────────────────────────────────────┐
│  您的代码                                                   │
│                                                             │
│  building.id → "550e8400-e29b-41d4-a716-446655440000"      │
└──────────────────────────────────────────────────────────────┘
```

---

## 为什么需要三层架构？

### ❌ 没有 ORM 的方式（直接写 SQL）

```python
# 您需要手动写 SQL
import psycopg2

def create_building(name, floor_area, gfa_area):
    conn = psycopg2.connect(...)
    cursor = conn.cursor()

    # 手写 SQL（容易出错）
    sql = """
        INSERT INTO buildings (id, name, floor_area, gfa_area, created_at)
        VALUES (gen_random_uuid(), %s, %s, %s, NOW())
        RETURNING id
    """
    cursor.execute(sql, (name, floor_area, gfa_area))
    building_id = cursor.fetchone()[0]
    conn.commit()
    return building_id
```

**缺点**:
- ❌ 容易出错（字段顺序、类型转换）
- ❌ 不安全（SQL 注入风险）
- ❌ 难以维护（数据库结构改变后要改很多地方）
- ❌ 没有类型提示（IDE 无法自动补全）
- ❌ 重复代码多（每个查询都要写类似代码）

---

### ✅ 使用 ORM 的方式

```python
# 像操作普通 Python 对象一样
from shared.db.models_project import Building
from sqlalchemy.orm import Session

def create_building(name: str, floor_area: float, gfa_area: float, db: Session):
    building = Building(
        name=name,
        floor_area=floor_area,
        gfa_area=gfa_area,
    )
    db.add(building)
    db.commit()
    db.refresh(building)
    return building
```

**优点**:
- ✅ 类型安全（IDE 自动补全、类型检查）
- ✅ 防止 SQL 注入（自动转义）
- ✅ 数据库无关（可以轻松切换到 MySQL、SQLite）
- ✅ 代码可读性好（像操作普通对象）
- ✅ 自动处理类型转换（Python ↔ PostgreSQL）
- ✅ 代码复用（关系映射、验证逻辑）
- ✅ 易于测试（可以 Mock 对象）

---

## 数据库变更最佳实践

### 数据库变更流程

当您需要修改数据库结构时（例如今天添加 `gfa_area` 列），需要确保三层同步：

#### 步骤 1: 修改数据库表结构

```sql
-- 直接在 PostgreSQL 上执行
ALTER TABLE buildings ADD COLUMN gfa_area double precision;
ALTER TABLE buildings DROP COLUMN energy_grade;
```

**执行方式**:
```bash
# 方式 1: 使用 psql
psql -h localhost -U admin -d bdc_ai -f migration.sql

# 方式 2: 使用 Python（推荐）
python -c "
from sqlalchemy import create_engine, text
engine = create_engine('postgresql://admin:password@localhost:5432/bdc_ai')

with engine.connect() as conn:
    trans = conn.begin()
    try:
        conn.execute(text('ALTER TABLE buildings ADD COLUMN gfa_area double precision'))
        conn.execute(text('ALTER TABLE buildings DROP COLUMN energy_grade'))
        trans.commit()
        print('数据库变更成功')
    except Exception as e:
        trans.rollback()
        print(f'数据库变更失败: {e}')
"
```

#### 步骤 2: 更新 ORM 模型

```python
# shared/db/models_project.py

class Building(Base):
    __tablename__ = "buildings"

    # ... 其他字段

    gfa_area = Column(Float, nullable=True)  # ← 添加新字段
    # energy_grade 已被删除  # ← 删除旧行
```

#### 步骤 3: 更新 API Schemas

```python
# services/backend/app/schemas/engineering.py

class BuildingBase(BaseModel):
    name: str
    usage_type: Optional[str] = None
    floor_area: Optional[float] = None
    gfa_area: Optional[float] = None  # ← 添加新字段
    year_built: Optional[float] = None
    tags: Optional[List[str]] = None
    # energy_grade 已被删除  # ← 删除旧行
```

#### 步骤 4: 验证同步

```python
# 测试脚本
from shared.db.models_project import Building
from shared.db.session import SessionLocal

db = SessionLocal()
try:
    # 创建测试对象
    building = Building(name="测试", gfa_area=1000.0)
    db.add(building)
    db.commit()

    # 查询验证
    result = db.query(Building).first()
    assert hasattr(result, 'gfa_area'), "缺少 gfa_area 字段"
    assert not hasattr(result, 'energy_grade'), "energy_grade 字段仍然存在"

    print("✓ 三层同步成功")
finally:
    db.close()
```

---

## 项目中的文件关系

### 目录结构

```
program-bdc-ai/
│
├── shared/
│   └── db/
│       ├── base.py              # ← ORM 基类（引擎配置）
│       ├── session.py           # ← 数据库会话（连接池）
│       └── models_project.py    # ← ORM 模型定义（Building 等）
│
├── services/backend/
│   └── app/
│       ├── api/v1/
│       │   └── engineering.py   # ← 使用 ORM 的业务代码
│       └── schemas/
│           └── engineering.py   # ← Pydantic 数据验证模型
│
└── .env                          # ← 数据库连接配置
    BDC_DATABASE_URL=postgresql://admin:password@localhost:5432/bdc_ai
```

### 数据流向图

```
┌─────────────────────────────────────────────────────────────┐
│  配置层 (.env)                                              │
│                                                             │
│  BDC_DATABASE_URL=postgresql://user:pass@localhost:5432/bdc │
└──────────────────────┬──────────────────────────────────────┘
                       ↓ 读取配置
┌──────────────────────────────────────────────────────────────┐
│  Settings (shared/config/settings.py)                       │
│                                                             │
│  settings.database_url → "postgresql://..."                 │
└──────────────────────┬──────────────────────────────────────┘
                       ↓ 创建引擎
┌──────────────────────────────────────────────────────────────┐
│  Engine (shared/db/session.py)                              │
│                                                             │
│  engine = create_engine(settings.database_url)              │
│  SessionLocal = sessionmaker(bind=engine)                   │
└──────────────────────┬──────────────────────────────────────┘
                       ↓ 提供会话
┌──────────────────────────────────────────────────────────────┐
│  FastAPI Dependency Injection                                │
│                                                             │
│  def get_db():                                             │
│      db = SessionLocal()                                    │
│      yield db                                               │
│      db.close()                                             │
└──────────────────────┬──────────────────────────────────────┘
                       ↓ 注入到路由
┌──────────────────────────────────────────────────────────────┐
│  API Route (services/backend/app/api/v1/engineering.py)    │
│                                                             │
│  @router.post("/buildings")                                 │
│  async def create_building(                                │
│      ...,                                                  │
│      db: Session = Depends(get_db)  # ← 注入会话            │
│  ):                                                         │
│      building = Building(...)  # ← 使用模型                 │
│      db.add(building)                                       │
│      db.commit()                                            │
└──────────────────────┬──────────────────────────────────────┘
                       ↓ SQL
┌──────────────────────────────────────────────────────────────┐
│  PostgreSQL (localhost:5432)                               │
│                                                             │
│  执行 SQL，存储数据                                          │
└──────────────────────────────────────────────────────────────┘
```

---

## 常见问题

### ❌ 问题 1: 修改了模型但数据库报错

**错误信息**:
```
sqlalchemy.exc.ProgrammingError: column "gfa_area" does not exist
```

**原因**: 只修改了 ORM 模型，但没有修改数据库表结构

**解决**:
```bash
# 1. 执行数据库变更
python -c "
from sqlalchemy import create_engine, text
engine = create_engine('postgresql://admin:password@localhost:5432/bdc_ai')
with engine.connect() as conn:
    conn.execute(text('ALTER TABLE buildings ADD COLUMN gfa_area double precision'))
    conn.commit()
"

# 2. 重启后端服务（让模型变更生效）
```

---

### ❌ 问题 2: 修改了数据库但代码报错

**错误信息**:
```
AttributeError: 'Building' object has no attribute 'gfa_area'
```

**原因**: 只修改了数据库，但没有更新 ORM 模型

**解决**:
```python
# shared/db/models_project.py
class Building(Base):
    gfa_area = Column(Float, nullable=True)  # ← 添加这一行
```

---

### ❌ 问题 3: Schema 验证失败

**错误信息**:
```
pydantic.v1.error_wrappers.ValidationError: 1 validation error for BuildingCreate
```

**原因**: ORM 模型更新了，但 Pydantic schema 没有更新

**解决**:
```python
# services/backend/app/schemas/engineering.py
class BuildingBase(BaseModel):
    gfa_area: Optional[float] = None  # ← 添加这一行
```

---

## 最佳实践

### 1. 始终保持三层同步

```
数据库层      ORM 层        API Schema 层
PostgreSQL  ←  SQLAlchemy  ←  Pydantic
  表结构        模型定义         数据验证
    ↓             ↓                ↓
  先修改       再修改          最后修改
```

**推荐的变更顺序**:
1. 先备份数据库
2. 执行数据库变更（SQL）
3. 更新 ORM 模型（models_project.py）
4. 更新 API Schemas（engineering.py）
5. 测试验证
6. 重启服务

---

### 2. 使用类型提示

```python
# ✓ 推荐：明确类型
def create_building(
    name: str,
    floor_area: Optional[float],
    db: Session
) -> Building:
    ...

# ✗ 不推荐：没有类型
def create_building(name, floor_area, db):
    ...
```

---

### 3. 使用依赖注入

```python
# ✓ 推荐：FastAPI 依赖注入
@router.post("/buildings")
async def create_building(
    ...,
    db: Session = Depends(get_db)  # ← 自动管理会话
):
    ...

# ✗ 不推荐：手动创建会话
@router.post("/buildings")
async def create_building(...):
    db = SessionLocal()
    try:
        ...
    finally:
        db.close()  # 容易忘记关闭
```

---

### 4. 使用事务

```python
# ✓ 推荐：使用事务回滚
def create_building_with_zones(building_data, zones_data, db):
    try:
        building = Building(**building_data)
        db.add(building)
        db.flush()  # 获取 ID 但不提交

        for zone_data in zones_data:
            zone = Zone(building_id=building.id, **zone_data)
            db.add(zone)

        db.commit()  # ← 全部成功才提交
    except Exception:
        db.rollback()  # ← 失败则回滚
        raise

# ✗ 不推荐：逐个提交
db.add(building)
db.commit()  # ← 如果这里成功，后面失败怎么办？

db.add(zone)
db.commit()
```

---

## 总结

### 三层架构对比

| 层级 | 技术 | 作用 | 优点 | 维护方式 |
|------|------|------|------|----------|
| **数据库层** | PostgreSQL | 实际存储数据 | 数据持久化、事务支持 | SQL 脚本 |
| **ORM 层** | SQLAlchemy | Python 对象 ↔ 数据库表 | 类型安全、自动 SQL | 修改模型类 |
| **应用层** | FastAPI + Python | 业务逻辑操作 | 易读、易维护 | 修改业务代码 |

### 关键点

1. **分离关注点**: 每层只关注自己的职责
2. **自动翻译**: SQLAlchemy 自动生成 SQL
3. **类型安全**: Python 类型提示，IDE 自动补全
4. **易于维护**: 修改业务逻辑不影响数据库层
5. **数据库无关**: 可以轻松切换数据库

### 数据库变更检查清单

- [ ] 执行数据库变更 SQL
- [ ] 更新 ORM 模型（models_project.py）
- [ ] 更新 API Schemas（engineering.py）
- [ ] 更新业务代码（如需要）
- [ ] 测试验证
- [ ] 重启服务

---

## 相关文档

- [技术指南](./技术指南.md) - 详细的技术栈说明
- [工程结构 API 设计](./工程结构API设计.md) - API 设计文档
- [PostgreSQL 迁移总结](../04-迁移记录/PostgreSQL迁移总结.md) - 迁移历史

---

**文档版本**: v1.0
**最后更新**: 2026-01-21
**维护者**: BDC-AI 开发团队
