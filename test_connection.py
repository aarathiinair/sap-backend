from app.db import engine
from sqlalchemy import text
 
def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            for row in result:
                print("Connected! PostgreSQL version:", row[0])
    except Exception as e:
        print("Connection failed:", e)
 
if __name__ == "__main__":
    test_connection()