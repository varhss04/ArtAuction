# Quick Start Guide

## 🚀 Starting the Application

### Option 1: Double-click
```
START_APP.bat
```

### Option 2: Command line
```bash
python app.py
```

Then visit: **http://127.0.0.1:5000**

---

## 🔐 Login Credentials

### Admin Account (Full Access)
```
Email: admin@gallery.com
Password: admin123
```

---

## 📋 What You'll See by Role

### BIDDER (3 Cards on Dashboard)
1. **Browse Auctions** - View and bid on active auctions
2. **My Bid History** - Track all your bids
3. **My Winnings** - Complete payments for won items

### SELLER (5 Cards - Bidder + 2 More)
4. **Sell New Artwork** - List new items for auction
5. **My Listings** - Track your artwork status

### ADMIN (8 Cards - Seller + 3 More)
6. **Admin Dashboard** - System statistics
7. **Manage Auctions** - Create/manage auctions
8. **Manage Users** - View/update user roles

---

## ✅ Quick Test Workflow

1. **Login as admin** (admin@gallery.com / admin123)
2. **Click "Admin Dashboard"** - See system stats
3. **Click "Manage Auctions"** - Create a new auction
4. **Register a seller account** (Logout → Register)
5. **Login as seller** - Create an artwork
6. **Switch back to admin** - Assign artwork to auction
7. **Start the auction** - Change status to active
8. **Register a bidder** - Test placing bids
9. **Close auction as admin** - Generates payments
10. **Login as bidder** - Complete payment & view receipt

---

## 🗄️ Database Connection

Your `.env` file contains:
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=F@tlady0194
DB_NAME=ArtAuctionDB
```

---

## 🔧 Recreate Database (If Needed)

```bash
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -pF@tlady0194 < ArtAuctionDb.sql
python create_admin.py
```

---

## 📁 Key Files

- `app.py` - Main Flask application
- `ArtAuctionDb.sql` - Database schema & procedures
- `create_admin.py` - Create admin accounts
- `FEATURES.md` - Complete feature documentation
- `templates/` - All HTML templates
- `.env` - Database configuration

---

## 🆘 Troubleshooting

### Can't login?
- Run: `python test_login.py` to verify credentials

### Database connection error?
- Check MySQL is running
- Verify `.env` credentials

### Need fresh database?
- Run the database recreate commands above

---

## 📞 Support

Check `FEATURES.md` for complete documentation of all features and database structure.
