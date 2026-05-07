
import asyncio
from sqlalchemy import text
from app.db.database import engine

async def cleanup_indexes():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("DROP INDEX IF EXISTS ix_audit_logs_timestamp;"))
            await conn.execute(text("DROP INDEX IF EXISTS ix_users_email;"))
            await conn.execute(text("DROP INDEX IF EXISTS ix_users_role;"))
            print("Cleaned up lingering indexes.")
        except Exception as e:
            print(f"Error cleaning up indexes: {e}")

if __name__ == "__main__":
    asyncio.run(cleanup_indexes())
