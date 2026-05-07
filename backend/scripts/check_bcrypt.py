
import bcrypt
password = b"password123"
hashed = bcrypt.hashpw(password, bcrypt.gensalt())
print(f"Hashed: {hashed}")
matches = bcrypt.checkpw(password, hashed)
print(f"Matches: {matches}")
