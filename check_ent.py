import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'tanzhisu.db')
db = sqlite3.connect(db_path)
cursor = db.cursor()

# 检查通知的user_id分布
cursor.execute('SELECT user_id, type_name, COUNT(*) FROM notifications GROUP BY user_id, type_name')
rows = cursor.fetchall()
print('通知分布:')
for r in rows:
    print(f'  user_id={r[0]}, type={r[1]}, count={r[2]}')

# 检查企业用户ID
cursor.execute("SELECT id, username FROM users WHERE role='enterprise'")
ent = cursor.fetchall()
print('\n企业用户:')
for e in ent:
    print(f'  id={e[0]}, username={e[1]}')

# 检查购买订单的enterprise_id
print('\n采购订单分布:')
cursor.execute("SELECT enterprise_id, status, COUNT(*) FROM purchase_orders GROUP BY enterprise_id, status")
for r in cursor.fetchall():
    print(f'  enterprise_id={r[0]}, status={r[1]}, count={r[2]}')

# 检查溯源码的用户关联
print('\n溯源码分布:')
cursor.execute("SELECT user_id, product_name, COUNT(*) FROM traceability_nodes GROUP BY user_id, product_name")
for r in cursor.fetchall():
    print(f'  user_id={r[0]}, product={r[1]}, count={r[2]}')

db.close()
