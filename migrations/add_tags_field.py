"""添加 tags 字段到 projects 表"""
import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'bdc_ai',
    'user': 'admin',
    'password': 'password'
}

sql = """
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS tags JSONB;
"""

conn = psycopg2.connect(**DB_CONFIG)
try:
    with conn.cursor() as cursor:
        cursor.execute(sql)
    conn.commit()
    print("[OK] 添加 tags 字段成功！")
except Exception as e:
    conn.rollback()
    print(f"[ERROR] 添加失败: {e}")
finally:
    conn.close()
