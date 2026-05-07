"""
backend/scripts/seed.py
Seeds a default doctor account for development.
"""
import asyncio
import os
import sys
from datetime import datetime
import asyncpg
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()

async def seed():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not found in environment.")
        return

    print(f"Connecting to database...")
    sys.path.append(os.path.join(os.getcwd(), "backend"))
    from utils.db import get_pool
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        try:
            email = "dr.admin@rxbridge.com"
            password = "AdminPassword123" # Secure enough for local dev
            hashed = hash_password(password)
            name = "Dr. Admin"
            role = "doctor"

            print(f"Checking if user {email} exists...")
            row = await conn.fetchrow("SELECT id FROM users WHERE email = $1", email)
            
            if row:
                print("User already exists. Updating password...")
                await conn.execute(
                    "UPDATE users SET password_hash = $1 WHERE email = $2",
                    hashed, email
                )
            else:
                print("Creating new doctor user...")
                await conn.execute(
                    """
                    INSERT INTO users (email, password_hash, name, role)
                    VALUES ($1, $2, $3, $4)
                    """,
                    email, hashed, name, role
                )
            
            print("\n" + "="*40)
            print("SEED SUCCESSFUL")
            print(f"Email:    {email}")
            print(f"Password: {password}")
            print("="*40)

        except Exception as e:
            print(f"Seed failed: {e}")

if __name__ == "__main__":
    asyncio.run(seed())
