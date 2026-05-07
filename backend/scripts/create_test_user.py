
import asyncio
from app.db.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import hash_password
from sqlalchemy import select

async def create_test_user():
    print("Creating test user...")
    async with AsyncSessionLocal() as db:
        try:
            # Check if user exists
            stmt = select(User).where(User.email == "test@rxbridge.com")
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if not user:
                user = User(
                    email="test@rxbridge.com",
                    hashed_password=hash_password("password123"),
                    role="doctor",
                    is_active=True
                )
                db.add(user)
                await db.flush() # Get user.id
                print("User created.")
            else:
                print("User already exists.")

            from app.models.doctor import DoctorProfile
            stmt = select(DoctorProfile).where(DoctorProfile.user_id == user.id)
            profile_res = await db.execute(stmt)
            if not profile_res.scalar_one_or_none():
                profile = DoctorProfile(
                    user_id=user.id,
                    full_name="Dr. Test User",
                    specialization="General Medicine",
                    medical_registration_number="MD12345",
                    hospital_affiliation="RxBridge General Hospital"
                )
                db.add(profile)
                print("Profile created.")
            else:
                print("Profile already exists.")
            
            await db.commit()
            print("Test account verification complete.")
        except Exception as e:
            print(f"Error creating user: {e}")

if __name__ == "__main__":
    asyncio.run(create_test_user())
