
import asyncio
from sqlalchemy import text
from app.db.database import engine

async def inspect_db():
    async with engine.connect() as conn:
        print("Checking tables in public schema:")
        result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"))
        for row in result:
            print(f" Table: {row[0]}")
            
        print("\nChecking indexes in public schema:")
        result = await conn.execute(text("SELECT indexname, tablename FROM pg_indexes WHERE schemaname = 'public';"))
        for row in result:
            print(f" Index: {row[0]} on table {row[1]}")

if __name__ == "__main__":
    asyncio.run(inspect_db())
