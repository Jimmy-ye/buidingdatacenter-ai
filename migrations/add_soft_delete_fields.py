"""添加软删除字段到 projects 表"""
from sqlalchemy import text
from shared.db.session import engine


def add_soft_delete_fields():
    """添加软删除字段到 projects 表"""
    with engine.begin() as conn:
        # 检查字段是否已存在
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'projects'
            AND column_name IN ('is_deleted', 'deleted_at', 'deleted_by', 'deletion_reason')
        """))
        existing_columns = [row[0] for row in result]

        # 添加 is_deleted 字段
        if 'is_deleted' not in existing_columns:
            conn.execute(text("""
                ALTER TABLE projects
                ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT FALSE
            """))
            print("[OK] 添加 is_deleted 字段")
        else:
            print("[SKIP] is_deleted 字段已存在")

        # 添加 deleted_at 字段
        if 'deleted_at' not in existing_columns:
            conn.execute(text("""
                ALTER TABLE projects
                ADD COLUMN deleted_at TIMESTAMP
            """))
            print("[OK] 添加 deleted_at 字段")
        else:
            print("[SKIP] deleted_at 字段已存在")

        # 添加 deleted_by 字段
        if 'deleted_by' not in existing_columns:
            conn.execute(text("""
                ALTER TABLE projects
                ADD COLUMN deleted_by VARCHAR(100)
            """))
            print("[OK] 添加 deleted_by 字段")
        else:
            print("[SKIP] deleted_by 字段已存在")

        # 添加 deletion_reason 字段
        if 'deletion_reason' not in existing_columns:
            conn.execute(text("""
                ALTER TABLE projects
                ADD COLUMN deletion_reason VARCHAR(500)
            """))
            print("[OK] 添加 deletion_reason 字段")
        else:
            print("[SKIP] deletion_reason 字段已存在")

        # 创建索引
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_projects_is_deleted
            ON projects(is_deleted)
        """))
        print("[OK] 创建 is_deleted 索引")

    print("\n迁移完成！")


if __name__ == "__main__":
    add_soft_delete_fields()
