import asyncio
import os
import uuid
from datetime import datetime, timedelta
from utils.db import get_pool
from utils.security import hash_password

async def seed():
    print("Seeding database...")
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        # 1. Create a default doctor
        doctor_id = str(uuid.uuid4())
        doctor_email = "dr.test@rxbridge.com"
        doctor_password = "Password123" # compliant: 11 chars, 1 upper, 1 digit
        
        try:
            await conn.execute("""
                INSERT INTO users (id, email, password_hash, name, role)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (email) DO NOTHING
            """, doctor_id, doctor_email, hash_password(doctor_password), "Dr. Test Practitioner", "doctor")
            print(f"Created Doctor: {doctor_email} / {doctor_password}")
            
            # Fetch the actual doctor_id if it already existed
            doctor_row = await conn.fetchrow("SELECT id FROM users WHERE email = $1", doctor_email)
            doctor_id = doctor_row['id']
        except Exception as e:
            print(f"Failed to create doctor: {e}")
            return

        # 2. Create a test patient
        patient_id = str(uuid.uuid4())
        try:
            await conn.execute("""
                INSERT INTO patients (id, doctor_id, name, age, gender, location, weight_kg, conditions, allergies, medications)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT DO NOTHING
            """, patient_id, doctor_id, "John Doe", 45, "male", "Nairobi", 72.5, 
            '["Hypertension"]', '["Penicillin"]', '["Amlodipine"]')
            print(f"Created Patient: John Doe")
        except Exception as e:
            print(f"Failed to create patient: {e}")

        # 3. Create a consultation
        cons_id = str(uuid.uuid4())
        try:
            await conn.execute("""
                INSERT INTO consultations (id, doctor_id, patient_id, symptoms, status, pipeline_output)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT DO NOTHING
            """, cons_id, doctor_id, patient_id, '["fever", "cough"]', "complete", 
            '{"top_diagnosis": "Pneumonia", "top_drug": "Amoxicillin", "doctor_summary": "Patient presenting with respiratory distress. Recommended course of Amoxicillin."}')
            print(f"Created Consultation for John Doe")
        except Exception as e:
            print(f"Failed to create consultation: {e}")

    print("Seeding complete!")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(seed())
