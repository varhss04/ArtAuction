import mysql.connector
from werkzeug.security import check_password_hash
from dotenv import load_dotenv
import os

load_dotenv()

# Test database connection and login
conn = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)

cursor = conn.cursor(dictionary=True)
query = "SELECT id, username, password_hash, role FROM users WHERE email = %s"
cursor.execute(query, ('admin@gallery.com',))
user = cursor.fetchone()

print(f"User found: {user['username']}")
print(f"Role: {user['role']}")

# Test password verification
test_password = 'admin123'
if user and user.get('password_hash') and check_password_hash(user['password_hash'], test_password):
    print(f"[OK] Password verification SUCCESS!")
    print(f"Login credentials are working correctly.")
else:
    print(f"[FAIL] Password verification FAILED!")

cursor.close()
conn.close()
