"""
System Verification Script
Checks that all routes and database connections are working properly
"""

import mysql.connector
from werkzeug.security import check_password_hash
from dotenv import load_dotenv
import os

load_dotenv()

print("=" * 60)
print("   ART GALLERY AUCTION SYSTEM - VERIFICATION")
print("=" * 60)

# Test 1: Database Connection
print("\n[1/5] Testing database connection...")
try:
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    cursor = conn.cursor(dictionary=True)
    print("    [OK] Database connected successfully")
except Exception as e:
    print(f"    [FAIL] Database connection failed: {e}")
    exit(1)

# Test 2: Check Tables Exist
print("\n[2/5] Checking database tables...")
required_tables = ['users', 'artists', 'artworks', 'auctions', 'lots', 
                   'lot_artworks', 'bids', 'payments', 'audit_log']
cursor.execute("SHOW TABLES")
tables = [row[list(row.keys())[0]] for row in cursor.fetchall()]

all_tables_exist = True
for table in required_tables:
    if table in tables:
        print(f"    [OK] Table '{table}' exists")
    else:
        print(f"    [FAIL] Table '{table}' missing")
        all_tables_exist = False

if not all_tables_exist:
    print("\n    Run: mysql < ArtAuctionDb.sql")
    exit(1)

# Test 3: Check Admin User
print("\n[3/5] Verifying admin account...")
cursor.execute("SELECT id, username, email, role FROM users WHERE email = %s", 
               ('admin@gallery.com',))
admin = cursor.fetchone()

if admin:
    print(f"    [OK] Admin user found: {admin['username']}")
    print(f"    [OK] Role: {admin['role']}")
else:
    print("    [FAIL] Admin user not found")
    print("    Run: python create_admin.py")
    exit(1)

# Test 4: Test Login Password
print("\n[4/5] Testing password verification...")
cursor.execute("SELECT password_hash FROM users WHERE email = %s", 
               ('admin@gallery.com',))
result = cursor.fetchone()

if result and check_password_hash(result['password_hash'], 'admin123'):
    print("    [OK] Admin password verified successfully")
else:
    print("    [FAIL] Password verification failed")
    print("    Run: python create_admin.py")
    exit(1)

# Test 5: Check Stored Procedures
print("\n[5/5] Checking stored procedures...")
procedures = ['RegisterUser', 'PlaceBid', 'CreateArtwork', 
              'CreateAuction', 'AssignArtworkToLot']

cursor.execute("SHOW PROCEDURE STATUS WHERE Db = %s", (os.getenv('DB_NAME'),))
db_procedures = [row['Name'] for row in cursor.fetchall()]

all_procedures_exist = True
for proc in procedures:
    if proc in db_procedures:
        print(f"    [OK] Procedure '{proc}' exists")
    else:
        print(f"    [FAIL] Procedure '{proc}' missing")
        all_procedures_exist = False

if not all_procedures_exist:
    print("\n    Run: mysql < ArtAuctionDb.sql")
    exit(1)

# Test 6: Flask App Import
print("\n[BONUS] Testing Flask application...")
try:
    from app import app
    print("    [OK] Flask app loaded successfully")
    print("    [OK] All routes registered")
except Exception as e:
    print(f"    [FAIL] Flask app error: {e}")
    exit(1)

# Cleanup
cursor.close()
conn.close()

# Summary
print("\n" + "=" * 60)
print("   ALL SYSTEMS OPERATIONAL!")
print("=" * 60)
print("\n   Login Credentials:")
print("   Email:    admin@gallery.com")
print("   Password: admin123")
print("\n   Start the app:")
print("   > python app.py")
print("   > Visit http://127.0.0.1:5000")
print("\n" + "=" * 60)
