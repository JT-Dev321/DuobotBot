import sqlite3

conn = sqlite3.connect('db/db.sqlite')
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        discord_id TEXT PRIMARY KEY,
        steam_id TEXT,
        steam_name TEXT,
        steam_level INTEGER,
        last_updated TEXT
    )
''')

conn.commit()
conn.close()
