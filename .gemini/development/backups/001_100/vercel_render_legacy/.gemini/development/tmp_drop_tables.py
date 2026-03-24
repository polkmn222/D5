import sqlite3
import os

db_path = "/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/crm.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS tasks;")
cursor.execute("DROP TABLE IF EXISTS campaigns;")

conn.commit()
conn.close()
print("Tables 'tasks' and 'campaigns' dropped successfully.")
