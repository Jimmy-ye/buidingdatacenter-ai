# 测试文档

## 测试目录结构

```
tests/
├── integration/          # 集成测试
│   ├── test_project_creation.py      # 项目创建测试
│   ├── test_paddleocr_pipeline.py    # PaddleOCR 完整流水线测试
│   ├── test_paddleocr_standalone.py  # PaddleOCR 独立测试
│   └── test_full_pipeline.py         # 完整业务流程测试
├── unit/                 # 单元测试（待添加）
└── api/                  # API 测试（待添加）
```

## 运行测试

### 运行所有测试
```bash
pytest tests/ -v
```

### 运行特定类型测试
```bash
# 集成测试
pytest tests/integration/ -v

# 单元测试
pytest tests/unit/ -v

# API 测试
pytest tests/api/ -v
```

### 运行特定测试文件
```bash
pytest tests/integration/test_project_creation.py -v
```

## 测试覆盖范围

### ✅ 已完成测试

1. **test_project_creation.py**
   - 项目创建 API
   - Asset 上传 API
   - 数据库持久化验证

2. **test_paddleocr_pipeline.py**
   - PaddleOCR 本地测试
   - 图片文字识别
   - 置信度评估

3. **test_full_pipeline.py**
   - 完整业务流程：创建项目 → 上传图片 → OCR 解析 → 查看结果

### 📝 待添加测试

- [ ] 单元测试：service 层业务逻辑
- [ ] API 测试：所有端点的请求/响应验证
- [ ] 性能测试：OCR 处理速度
- [ ] 错误处理测试：异常情况覆盖

## 测试数据

测试使用的数据文件：
- `C:\Users\86152\Downloads\设备铭牌\` - 设备铭牌图片（用于 OCR 测试）

## 注意事项

1. 测试前确保后端服务已启动：
   ```bash
   python -m uvicorn services.backend.app.main:app --reload
   ```

2. 某些测试需要本地环境变量：
   ```bash
   export BDC_DATABASE_URL=sqlite:///./data/bdc_ai.db
   ```

3. OCR 测试会下载 PaddleOCR 模型（首次运行较慢）
