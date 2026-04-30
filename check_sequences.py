from db.database import SessionLocal, engine
from sqlalchemy import text

session = SessionLocal()

# Check the current sequence values
result = session.execute(text('SELECT name FROM sqlite_master WHERE type="table"')).fetchall()
print('Tables:', [r[0] for r in result])

# Check the sqlite_sequence table (SQLite autoincrement)
try:
    result = session.execute(text('SELECT * FROM sqlite_sequence')).fetchall()
    print('Sequences:', result)
except Exception as e:
    print('No sqlite_sequence table yet:', e)

session.close()
