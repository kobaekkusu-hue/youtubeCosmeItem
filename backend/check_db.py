import sqlite3

conn = sqlite3.connect('test.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

# 商品一覧（詳細情報付き）
c.execute('SELECT name, brand, category, description, features, volume, ingredients, how_to_use FROM products ORDER BY name')
rows = c.fetchall()
print(f'=== 登録商品: {len(rows)}件 ===\n')
for i, r in enumerate(rows):
    print(f'{i+1}. [{r["category"]}] {r["brand"]} / {r["name"][:60]}')
    print(f'   説明: {(r["description"] or "-")[:80]}')
    print(f'   特徴: {(r["features"] or "-")[:80]}')
    print(f'   容量: {r["volume"] or "-"}')
    print(f'   成分: {(r["ingredients"] or "-")[:60]}')
    print(f'   使い方: {(r["how_to_use"] or "-")[:60]}')
    print()

# レビュー一覧
c.execute('SELECT r.summary, r.sentiment, p.name as pname FROM reviews r JOIN products p ON r.product_id = p.id')
reviews = c.fetchall()
print(f'=== レビュー: {len(reviews)}件 ===')
for r in reviews:
    print(f'  [{r["sentiment"]}] {r["pname"][:35]} - {r["summary"][:60]}')

conn.close()
