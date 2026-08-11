import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'tanzhisu.db')
db = sqlite3.connect(db_path)
cursor = db.cursor()

# 检查所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('数据库表:', [t[0] for t in tables])

# 检查users表结构
cursor.execute("PRAGMA table_info(users)")
cols = cursor.fetchall()
print('\nusers表结构:')
for c in cols:
    print(f'  {c[1]} ({c[2]})')

# 检查企业用户
cursor.execute('SELECT id, username, role FROM users')
all_users = cursor.fetchall()
print('\n所有用户:')
for u in all_users:
    print(f'  {u}')

# 检查各表数据量
for table in ['users', 'purchase_orders', 'traceability_nodes', 'notifications', 
              'water_quality_data', 'alert_records', 'transaction_posts']:
    try:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f'\n{table}: {count} 条记录')
        if count > 0:
            cursor.execute(f'SELECT * FROM {table} LIMIT 3')
            rows = cursor.fetchall()
            for r in rows:
                print(f'  {r}')
    except Exception as e:
        print(f'\n{table}: {str(e)}')

# 检查tidal_flats（滩涂）
print('\n=== 滩涂数据 ===')
cursor.execute('SELECT * FROM tidal_flats LIMIT 5')
for t in cursor.fetchall():
    print(f'  {t}')

db.close()
