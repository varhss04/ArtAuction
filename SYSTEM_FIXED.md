# Art Gallery Auction System - Fixed and Working

## What Was Fixed

### 1. Database Schema Issues
- **Changed `image_path` to `image_url`** in artworks table to match Flask code
- **Fixed constraint name** from `chk_image_path_format` to `chk_image_url_format`
- **Updated CreateArtwork stored procedure** to use `image_url` parameter instead of `image_path`

### 2. Invalid Password Hashes
- **Removed invalid sample data** with broken password hashes that were causing login failures
- The database now starts clean without any users

### 3. Database Connection
- **Removed invalid `connect_timeout` parameter** that was causing connection pool issues

## How to Use the System

### Admin Login Credentials
```
Email: admin@gallery.com
Password: admin123
```

### Starting the Application
```bash
python app.py
```
Then visit: http://127.0.0.1:5000

### Creating Additional Users

#### Method 1: Use the Register Page
- Go to http://127.0.0.1:5000/register
- Fill in the form with username, email, password, and role (bidder/seller)

#### Method 2: Modify create_admin.py
Edit the file and change:
```python
NEW_ADMIN_EMAIL = 'newuser@example.com'
NEW_ADMIN_PASS = 'newpassword123'
NEW_ADMIN_USER = 'newusername'
```
Then run:
```bash
python create_admin.py
```

### Database Management

#### Recreate Database (Fresh Start)
```bash
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -pF@tlady0194 < ArtAuctionDb.sql
python create_admin.py
```

#### Verify Login Works
```bash
python test_login.py
```

## System Features Working

✓ User registration with password hashing
✓ User login with secure password verification
✓ Admin dashboard
✓ Auction management
✓ Artwork listing
✓ Bidding system
✓ Payment processing
✓ Session management
✓ Role-based access control

## Database Tables
- users
- artists
- artworks (with image_url field)
- auctions
- lots
- lot_artworks
- bids
- payments
- audit_log

## Notes
- All passwords are securely hashed using Werkzeug's `generate_password_hash`
- Connection pooling is configured for better performance
- Database constraints ensure data integrity
- Triggers automatically manage auction and lot status
