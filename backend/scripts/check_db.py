
import asyncio
from sqlalchemy import text
from app.db.database import engine, init_db

async def check_db():
    print("Checking database connection...")
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT current_database();"))
            db_name = result.scalar()
            print(f"Connected to database: {db_name}")
            
            # Check if tables exist
            result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"))
            tables = result.fetchall()
            print("Existing tables:")
            for table in tables:
                print(f" - {table[0]}")
                
            if not any(t[0] == 'users' for t in tables):
                print("Users table not found. Initializing database...")
                await init_db()
                print("Database initialized.")
            else:
                print("Users table found.")
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    asyncio.run(check_db())
