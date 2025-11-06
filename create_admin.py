import os
import uuid
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# This script creates or updates an admin account
# so you can log in securely.

# --- DEFINE YOUR NEW ADMIN LOGIN ---
NEW_ADMIN_EMAIL = 'admin@gallery.com'
NEW_ADMIN_PASS = 'admin123'
NEW_ADMIN_USER = 'gallery_admin'
# ------------------------------------

def create_admin_account():
    """
    Connects to the DB and creates/updates the admin user
    with a properly hashed password.
    """
    print(f"Attempting to create/update admin user: {NEW_ADMIN_EMAIL}...")
    
    # 1. Load database credentials from .env file
    load_dotenv()
    db_host = os.getenv('DB_HOST')
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_NAME')
    
    conn = None
    cursor = None
    
    try:
        # 2. Generate the new, SECURE password hash
        # This is what your login page expects
        hashed_password = generate_password_hash(NEW_ADMIN_PASS)
        print(f"Generated new secure hash: {hashed_password[:30]}...") # Show partial hash

        # 3. Connect to the database
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_pass,
            database=db_name
        )
        
        if conn.is_connected():
            print("Database connection successful.")
            cursor = conn.cursor()
            
            # 4. Use "INSERT ... ON DUPLICATE KEY UPDATE"
            # This is a powerful command:
            # - It tries to INSERT the new user.
            # - If it fails because the email (UNIQUE key) already exists...
            # - ...it will UPDATE that user's password_hash and role instead.
            # This fixes your login problem either way.
            
            query = """
                INSERT INTO users (id, username, email, password_hash, role)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    password_hash = %s,
                    role = %s,
                    username = %s
            """
            
            user_id = str(uuid.uuid4())
            
            # Arguments for the query
            # (user_id, username, email, hash, role,  <-- for INSERT
            #  hash, role, username)                  <-- for UPDATE
            args = (user_id, NEW_ADMIN_USER, NEW_ADMIN_EMAIL, hashed_password, 'admin',
                    hashed_password, 'admin', NEW_ADMIN_USER)
            
            cursor.execute(query, args)
            conn.commit()
            
            print(f"\nSUCCESS!")
            print(f"Admin account '{NEW_ADMIN_EMAIL}' is ready.")
            print(f"You can now log in with these credentials:")
            print(f"  Email: {NEW_ADMIN_EMAIL}")
            print(f"  Password: {NEW_ADMIN_PASS}")

    except Error as e:
        if conn:
            conn.rollback() # Undo changes if something went wrong
        print(f"\nERROR: Could not create admin account.")
        print(f"Details: {e}")
        if "Access denied" in str(e):
            print(">>> HINT: Check your DB_PASSWORD in the .env file.")
        if "Unknown database" in str(e):
            print(f">>> HINT: Is your DB_NAME '{db_name}' correct in .env?")
            
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
            print("Database connection closed.")

# --- Run the script ---
if __name__ == "__main__":
    create_admin_account()