
import asyncio
from sqlalchemy import text
from app.db.database import engine, init_db

async def reset_db():
    print("Resetting database...")
    try:
        async with engine.begin() as conn:
            # Drop all tables in public schema
            await conn.execute(text("DROP SCHEMA public CASCADE;"))
            await conn.execute(text("CREATE SCHEMA public;"))
            await conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
            print("Dropped all tables and recreated schema.")
            
        print("Initializing database with new schema...")
        await init_db()
        print("Database schema reset and initialized successfully.")
    except Exception as e:
        print(f"Error resetting database: {e}")

if __name__ == "__main__":
    asyncio.run(reset_db())
