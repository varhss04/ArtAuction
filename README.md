# 🎨 Art Gallery Auction System

A complete auction management platform built with Flask and MySQL, featuring role-based access control and real-time bidding.

---

## ✨ Features Overview

### 👥 User Roles

#### **BIDDER** (3 Dashboard Cards)
- 🎯 Browse active auctions
- 📜 Track bid history  
- 🏆 View winnings & complete payments

#### **SELLER** (5 Dashboard Cards = Bidder + 2)
- ➕ List new artwork for auction
- 📋 View all your listings

#### **ADMIN** (8 Dashboard Cards = Seller + 3)
- 📊 View system statistics
- 🔨 Create & manage auctions
- 👤 Manage user accounts & roles

---

## 🚀 Quick Start

### 1. Start the Application
```bash
python app.py
```
Or double-click: **START_APP.bat**

### 2. Visit
```
http://127.0.0.1:5000
```

### 3. Login
```
Email: admin@gallery.com
Password: admin123
```

---

## 📦 What's Inside

```
ArtGallery/
├── app.py                    # Main Flask application
├── create_admin.py           # Admin account creator
├── verify_system.py          # System health check
├── test_login.py            # Login verification
├── ArtAuctionDb.sql         # Database schema
├── .env                     # Database credentials
├── templates/               # HTML templates
│   ├── layout.html         # Base template
│   ├── index.html          # Landing page
│   ├── dashboard.html      # Role-based dashboard
│   ├── login.html          # Login page
│   ├── register.html       # Registration
│   ├── auctions.html       # Browse auctions
│   ├── bids.html           # Place bids
│   ├── sell_item.html      # Create listings
│   ├── my_listings.html    # View seller items
│   ├── my_bid_history.html # Bid tracking
│   ├── my_winnings.html    # Won items
│   ├── payment.html        # Payment page
│   ├── receipt.html        # Payment receipt
│   ├── admin_dashboard.html      # Admin stats
│   ├── admin_manage_auctions.html # Auction management
│   ├── admin_manage_users.html    # User management
│   └── admin_auction_details.html # Lot management
└── static/
    └── bgpic.jpeg          # Hero background image
```

---

## 🗄️ Database Schema

### Core Tables
- **users** - User accounts with roles
- **artists** - Artist information
- **artworks** - Art pieces with metadata
- **auctions** - Auction events
- **lots** - Individual auction items
- **lot_artworks** - Artwork-to-lot mapping
- **bids** - Bid records
- **payments** - Payment transactions
- **audit_log** - Activity tracking

### Stored Procedures
- `RegisterUser` - Create new user
- `PlaceBid` - Record bid with validation
- `CreateArtwork` - Add artwork listing
- `CreateAuction` - Create auction event
- `AssignArtworkToLot` - Add artwork to auction

### Smart Triggers
- Auto-validate bid amounts
- Update lot status on payment
- Close auction when all lots sold
- Log all bid activity
- Prevent bids on closed lots
- Generate pending payments

---

## 🔐 Security Features

✅ Password hashing (Werkzeug)  
✅ Session management  
✅ Role-based access control  
✅ Admin route protection  
✅ SQL injection prevention  
✅ Database constraints  
✅ Unique email/username enforcement

---

## 📚 Documentation

- **FEATURES.md** - Complete feature documentation
- **QUICK_START.md** - Getting started guide
- **SYSTEM_FIXED.md** - What was fixed and how

---

## 🔧 Maintenance

### Verify System Health
```bash
python verify_system.py
```

### Recreate Database
```bash
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -pYourPassword < ArtAuctionDb.sql
python create_admin.py
```

### Create New Admin
Edit `create_admin.py` and run:
```bash
python create_admin.py
```

---

## 🎯 Complete Workflow Example

1. **Admin** creates an auction
2. **Seller** lists an artwork
3. **Admin** assigns artwork to auction lot
4. **Admin** starts the auction (sets to active)
5. **Bidder** browses auctions and places bids
6. **Admin** closes the auction
7. **System** auto-generates pending payment for winner
8. **Bidder** views winnings and completes payment
9. **Bidder** receives receipt

---

## 🌐 All Available Routes

### Public
- `/` - Landing page
- `/register` - Create account
- `/login` - User login

### Bidder
- `/dashboard` - Role-based dashboard
- `/auctions` - Browse active auctions
- `/auction/<id>` - View auction details & bid
- `/my_bid_history` - Track all bids
- `/my_winnings` - View won items
- `/pay/<payment_id>` - Complete payment
- `/receipt/<payment_id>` - View receipt

### Seller (+ Bidder routes)
- `/sell_item` - Create artwork listing
- `/my_listings` - View your artworks

### Admin (+ Seller + Bidder routes)
- `/admin/dashboard` - System statistics
- `/admin/manage_auctions` - Create & manage auctions
- `/admin/auction/<id>` - Manage auction lots
- `/admin/manage_users` - User management
- `/admin/update_role/<user_id>` - Change user role

---

## 💻 Technology Stack

- **Backend**: Flask (Python)
- **Database**: MySQL 8.0
- **Template Engine**: Jinja2
- **Security**: Werkzeug password hashing
- **CSS**: Custom responsive design
- **Icons**: Font Awesome
- **Fonts**: Google Fonts (Playfair Display, Inter)

---

## 📊 System Statistics

Run `verify_system.py` to check:
- ✅ Database connection
- ✅ All tables exist
- ✅ Admin account verified
- ✅ Password authentication
- ✅ Stored procedures loaded
- ✅ Flask app operational

---

## 🐛 Troubleshooting

### Login not working?
```bash
python test_login.py
```

### Database errors?
- Check MySQL is running
- Verify `.env` credentials match
- Recreate database with SQL file

### Missing features?
- Check `FEATURES.md` for complete list
- Verify you're logged in with correct role

---

## 📝 Environment Variables

File: `.env`
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=ArtAuctionDB
FLASK_SECRET_KEY=random_secret_key
```

---

## 🎨 Customization

- Modify `templates/layout.html` for global styling
- Update `static/bgpic.jpeg` for hero image
- Edit color variables in CSS sections
- Customize email templates in respective files

---

## 📞 Support

For issues or questions:
1. Check documentation files
2. Run `verify_system.py`
3. Review error messages in console
4. Check MySQL logs

---

## 📄 License

Built for educational purposes. Modify as needed.

---

**Built with ❤️ using Flask & MySQL**
