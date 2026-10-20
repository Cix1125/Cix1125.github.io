# -*- coding: utf-8 -*-
"""
进销存 · SQL 练习环境
运行：python 练习.py
它会做两件事：① 建一个真实的 SQLite 数据库（进销存.db） ② 跑一遍所有查询并打印结果
"""
import sqlite3, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, '进销存.db')

# ── 建表 ────────────────────────────────────────────────
SCHEMA = """
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS stock_moves;
DROP TABLE IF EXISTS orders;

CREATE TABLE products (
    id           INTEGER PRIMARY KEY,
    name         TEXT,      -- 品名
    sku          TEXT,      -- 货号
    price        REAL,      -- 单价
    stock        INTEGER,   -- 账面库存（手填的，会出错）
    safety_stock INTEGER    -- 安全库存（低于这个数就该补货）
);

CREATE TABLE stock_moves (
    id         INTEGER PRIMARY KEY,
    move_date  TEXT,        -- 日期
    product_id INTEGER,     -- 商品 id（外键，指向 products.id）
    move_type  TEXT,        -- 'in' 入库 / 'out' 出库
    qty        INTEGER,     -- 数量
    note       TEXT
);

CREATE TABLE orders (
    id         INTEGER PRIMARY KEY,
    customer   TEXT,        -- 客户
    product_id INTEGER,
    qty        INTEGER,
    status     TEXT,        -- 待处理 / 已发货 / 已完成 / 已取消
    order_date TEXT
);
"""

PRODUCTS = [
    (1, '纯棉圆领T恤', 'TX001',  59.0, 42, 20),
    (2, '牛仔直筒裤', 'JZ002', 129.0,  8, 15),   # 低于安全库存
    (3, '针织开衫',   'KZ003', 159.0, 25, 10),
    (4, '帆布单肩包', 'FB004',  89.0,  3, 12),   # 低于安全库存，且账面数错
    (5, '运动短裤',   'YD005',  69.0, 60, 20),
]

MOVES = [
    # ── 入库 ──
    ('2026-08-01', 1, 'in',  50, '首批进货'),
    ('2026-09-02', 1, 'in',  20, '补货'),
    ('2026-08-01', 2, 'in',  30, '首批进货'),
    ('2026-08-01', 3, 'in',  40, '首批进货'),
    ('2026-08-01', 4, 'in',  20, '首批进货'),
    ('2026-08-01', 5, 'in', 100, '首批进货'),
    # ── 出库（对应下面的订单）──
    ('2026-08-05', 1, 'out',  3, '订单1'),
    ('2026-08-12', 1, 'out',  5, '订单5'),
    ('2026-09-15', 1, 'out', 20, '订单12'),
    ('2026-08-08', 2, 'out', 10, '订单2'),
    ('2026-08-20', 2, 'out',  8, '订单7'),
    ('2026-09-05', 2, 'out',  4, '订单10'),
    ('2026-08-15', 3, 'out', 12, '订单6'),
    ('2026-09-10', 3, 'out',  3, '订单11'),
    ('2026-08-09', 4, 'out',  6, '订单3'),
    ('2026-08-25', 4, 'out',  5, '订单8'),
    ('2026-09-18', 4, 'out',  4, '订单13'),
    ('2026-08-11', 5, 'out', 15, '订单4'),
    ('2026-09-01', 5, 'out', 25, '订单9'),
]

ORDERS = [
    (1,  '张小满',   1,  3, '已完成', '2026-08-05'),
    (2,  '李记服饰', 2, 10, '已发货', '2026-08-08'),
    (3,  '散客',     4,  6, '已完成', '2026-08-09'),
    (4,  '张小满',   5, 15, '已完成', '2026-08-11'),
    (5,  '李记服饰', 1,  5, '已完成', '2026-08-12'),
    (6,  '网店客户A', 3, 12, '已完成', '2026-08-15'),
    (7,  '李记服饰', 2,  8, '已完成', '2026-08-20'),
    (8,  '散客',     4,  5, '已完成', '2026-08-25'),
    (9,  '网店客户A', 5, 25, '已完成', '2026-09-01'),
    (10, '张小满',   2,  4, '已发货', '2026-09-05'),
    (11, '散客',     3,  3, '已完成', '2026-09-10'),
    (12, '网店客户A', 1, 20, '已完成', '2026-09-15'),
    (13, '李记服饰', 4,  4, '已完成', '2026-09-18'),
    (14, '散客',     1,  2, '待处理', '2026-09-20'),   # 还没发货，所以不扣库存
]


# ── 打印工具 ────────────────────────────────────────────
def show(idx, question, sql, cur):
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description] if cur.description else []
    print('\n' + '═' * 66)
    print(f'Q{idx} · {question}')
    print('─' * 66)
    print(sql.strip())
    print('─' * 66)
    if not rows:
        print('（没有结果）')
        return
    w = [max(len(str(c)), max(len(str(r[i])) for r in rows)) for i, c in enumerate(cols)]
    print(' | '.join(str(c).ljust(w[i]) for i, c in enumerate(cols)))
    print('-+-'.join('-' * x for x in w))
    for r in rows:
        print(' | '.join(str(v).ljust(w[i]) for i, v in enumerate(r)))


def main():
    if os.path.exists(DB):
        os.remove(DB)
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.executescript(SCHEMA)
    cur.executemany('INSERT INTO products VALUES (?,?,?,?,?,?)', PRODUCTS)
    cur.executemany('INSERT INTO stock_moves (move_date,product_id,move_type,qty,note) VALUES (?,?,?,?,?)', MOVES)
    cur.executemany('INSERT INTO orders VALUES (?,?,?,?,?,?)', ORDERS)
    conn.commit()

    print('\n数据库已建好：', DB)
    print('三张表：products（商品） · stock_moves（出入库流水） · orders（订单）')
    print('数据：5 个商品 · %d 条流水 · %d 张订单' % (len(MOVES), len(ORDERS)))

    # ═══════════════════════════════════════════════════
    # 第 1 步：最简单的查询 —— SELECT / FROM / WHERE
    # ═══════════════════════════════════════════════════
    cur.execute("SELECT name, sku, price, stock FROM products")
    show(1, '把商品表整个看一遍（SELECT + FROM）',
         "SELECT name, sku, price, stock\nFROM products;", cur)

    cur.execute("SELECT name, stock, safety_stock FROM products WHERE stock < safety_stock")
    show(2, '哪些货快没了？（加一个 WHERE 做筛选）',
         "SELECT name, stock, safety_stock\nFROM products\nWHERE stock < safety_stock;", cur)

    # ═══════════════════════════════════════════════════
    # 第 2 步：排序和取前几名 —— ORDER BY / LIMIT
    # ═══════════════════════════════════════════════════
    cur.execute("""
        SELECT o.customer, p.name, o.qty, o.qty * p.price AS amount, o.order_date, o.status
        FROM orders o
        JOIN products p ON p.id = o.product_id
        ORDER BY amount DESC
        LIMIT 5
    """)
    show(3, '金额最大的 5 张订单（JOIN 把订单和商品连起来 + ORDER BY + LIMIT）',
         """SELECT o.customer, p.name, o.qty, o.qty * p.price AS amount, o.order_date, o.status
FROM orders o
JOIN products p ON p.id = o.product_id
ORDER BY amount DESC
LIMIT 5;""", cur)

    # ═══════════════════════════════════════════════════
    # 第 3 步：分组统计 —— GROUP BY + SUM / COUNT
    # ═══════════════════════════════════════════════════
    cur.execute("""
        SELECT p.name, SUM(m.qty) AS out_total
        FROM stock_moves m
        JOIN products p ON p.id = m.product_id
        WHERE m.move_type = 'out'
        GROUP BY p.name
        ORDER BY out_total DESC
    """)
    show(4, '每个商品总共出库了多少件？（GROUP BY + SUM）',
         """SELECT p.name, SUM(m.qty) AS out_total
FROM stock_moves m
JOIN products p ON p.id = m.product_id
WHERE m.move_type = 'out'
GROUP BY p.name
ORDER BY out_total DESC;""", cur)

    cur.execute("""
        SELECT p.name, SUM(o.qty) AS sold
        FROM orders o
        JOIN products p ON p.id = o.product_id
        WHERE o.order_date >= '2026-08-01' AND o.order_date < '2026-09-01'
          AND o.status <> '已取消'
        GROUP BY p.name
        ORDER BY sold DESC
        LIMIT 1
    """)
    show(5, '8 月份哪个商品卖得最好？（WHERE 限时间 + GROUP BY + ORDER BY + LIMIT）',
         """SELECT p.name, SUM(o.qty) AS sold
FROM orders o
JOIN products p ON p.id = o.product_id
WHERE o.order_date >= '2026-08-01' AND o.order_date < '2026-09-01'
  AND o.status <> '已取消'
GROUP BY p.name
ORDER BY sold DESC
LIMIT 1;""", cur)

    # ═══════════════════════════════════════════════════
    # 第 4 步：⭐ 对账 —— 这条最有价值
    # ═══════════════════════════════════════════════════
    cur.execute("""
        SELECT p.name,
               p.stock AS stock_on_record,
               IFNULL(SUM(CASE WHEN m.move_type = 'in' THEN m.qty ELSE -m.qty END), 0) AS stock_from_moves
        FROM products p
        LEFT JOIN stock_moves m ON m.product_id = p.id
        GROUP BY p.id, p.name, p.stock
        HAVING p.stock <> stock_from_moves
    """)
    show(6, '⭐ 对账：账面库存 和 流水算出来的库存 对不上的商品',
         """SELECT p.name,
       p.stock AS stock_on_record,
       IFNULL(SUM(CASE WHEN m.move_type = 'in' THEN m.qty ELSE -m.qty END), 0) AS stock_from_moves
FROM products p
LEFT JOIN stock_moves m ON m.product_id = p.id
GROUP BY p.id, p.name, p.stock
HAVING p.stock <> stock_from_moves;""", cur)

    cur.execute("""
        SELECT p.name, p.stock,
               IFNULL(SUM(CASE WHEN m.move_type = 'in' THEN m.qty ELSE -m.qty END), 0) AS stock_from_moves
        FROM products p
        LEFT JOIN stock_moves m ON m.product_id = p.id
        GROUP BY p.id, p.name, p.stock
        ORDER BY p.name
    """)
    show(7, '对照：全部商品的账面库存 vs 流水库存（上面那条只是把对得上的过滤掉了）',
         """SELECT p.name, p.stock,
       IFNULL(SUM(CASE WHEN m.move_type = 'in' THEN m.qty ELSE -m.qty END), 0) AS stock_from_moves
FROM products p
LEFT JOIN stock_moves m ON m.product_id = p.id
GROUP BY p.id, p.name, p.stock
ORDER BY p.name;""", cur)

    # ═══════════════════════════════════════════════════
    # 第 5 步：演示那条业务规则
    # ═══════════════════════════════════════════════════
    cur.execute("SELECT id, customer, product_id, qty, status FROM orders WHERE status = '待处理'")
    show(8, '待处理的订单 —— 它没有对应的出库流水，因为「发货才扣库存」',
         "SELECT id, customer, product_id, qty, status\nFROM orders\nWHERE status = '待处理';", cur)

    cur.execute("""
        SELECT o.customer, SUM(o.qty * p.price) AS total
        FROM orders o
        JOIN products p ON p.id = o.product_id
        WHERE o.status = '已完成'
        GROUP BY o.customer
        ORDER BY total DESC
    """)
    show(9, '每个客户成交了多少（三处 JOIN + GROUP BY + 过滤状态）',
         """SELECT o.customer, SUM(o.qty * p.price) AS total
FROM orders o
JOIN products p ON p.id = o.product_id
WHERE o.status = '已完成'
GROUP BY o.customer
ORDER BY total DESC;""", cur)

    conn.close()
    print('\n' + '═' * 66)
    print('跑完了。想改查询、加数据，直接改这个文件里的 SQL 再运行一次。')
    print('数据库文件：进销存.db（可以用 DB Browser for SQLite 打开看）')
    print('═' * 66 + '\n')


if __name__ == '__main__':
    main()
