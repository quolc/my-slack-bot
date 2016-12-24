import sqlite3

dbname = 'database.db'
conn = sqlite3.connect(dbname)
c = conn.cursor()

create_table = 'create table reminders (id INTEGER PRIMARY KEY, created_at datetime, remind_at datetime, message text, channel text)'
c.execute(create_table)


