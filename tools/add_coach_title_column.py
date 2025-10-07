import sqlite3

DB_PATH = "../app.db"

ALTER_SQL = """
ALTER TABLE coaches ADD COLUMN coach_title TEXT DEFAULT 'Mr';
"""

def main():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(ALTER_SQL)
        conn.commit()
        print("✅ coach_title column added to coaches table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column already exists.")
        else:
            print(f"❌ Migration error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
