import asyncio
import os
from utils.db import get_pool

async def check_users():
    pool = await get_pool()
    async with pool.acquire() as conn:
        users = await conn.fetch("SELECT id, email, name, role FROM users")
        print(f"Found {len(users)} users:")
        for u in users:
            print(f" - {u['email']} ({u['role']})")

if __name__ == "__main__":
    # Ensure DATABASE_URL is set (it should be in .env)
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(check_users())
