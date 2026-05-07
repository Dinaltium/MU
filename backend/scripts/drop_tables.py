
import asyncio
from sqlalchemy import text
from app.db.database import engine

async def drop_tables():
    tables = [
        "audit_logs", "calendar_events", "patient_consents", "diagnoses",
        "doctor_profiles", "doctor_patient_associations", "lab_profiles",
        "lab_orders", "lab_reports", "medications", "notifications",
        "patient_profiles", "pipeline_runs", "recovery_scores", "reports",
        "sos_alerts", "users"
    ]
    async with engine.begin() as conn:
        for table in tables:
            try:
                await conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
                print(f"Dropped {table}")
            except Exception as e:
                print(f"Error dropping {table}: {e}")
        
        # Also drop types/enums if they exist
        try:
            await conn.execute(text("DROP TYPE IF EXISTS user_role_enum CASCADE;"))
            print("Dropped user_role_enum")
        except Exception:
            pass

if __name__ == "__main__":
    asyncio.run(drop_tables())
