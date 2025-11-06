# Art Gallery Auction System - Complete Features

## User Roles & Functionalities

### 1. ALL USERS (Public - Not Logged In)

#### Available Pages:
- **Index Page** (`/` or `/index`)
  - Hero section with welcome message
  - Features showcase (Live Auctions, Secure Platform, Diverse Artworks, Community)
  - Call-to-action buttons (Browse Auctions, Join Now)
  
- **Register** (`/register`)
  - Create new account
  - Choose role: Bidder, Seller, or Admin
  - Password hashing for security
  
- **Login** (`/login`)
  - Secure login with email and password
  - Session management
  
- **API Endpoint** (`/api/welcome`)
  - Public API for testing

---

### 2. BIDDER (Logged-in Users - Default Role)

All bidders have access to **3 main functionalities** displayed as cards on their dashboard:

#### Dashboard Cards:
1. **Browse Auctions** (`/auctions`)
   - View all active auctions
   - See lot counts for each auction
   - Click to view auction details
   
2. **My Bid History** (`/my_bid_history`)
   - Track all bids placed
   - View bid amounts and timestamps
   - See lot status (open/sold/unsold)
   - View artwork images
   
3. **My Winnings** (`/my_winnings`)
   - View items won at auctions
   - See payment status (pending/completed)
   - Complete payments for won items
   - View receipts

#### Additional Bidder Features:
- **Auction Details** (`/auction/<auction_id>`)
  - View lots in an auction
  - See current highest bids
  - Place new bids
  
- **Place Bid** (`/place_bid` - POST)
  - Submit bid for a lot
  - Validation against current highest bid
  - Real-time bid tracking
  
- **Payment Page** (`/pay/<payment_id>`)
  - Review payment details
  - Complete payment for won item
  
- **Receipt Page** (`/receipt/<payment_id>`)
  - View detailed receipt after payment
  - Shows artwork, artist, amount, payment date

---

### 3. SELLER (Seller-Specific Features Only)

Sellers have **2 seller cards** with their own distinct functionality:

#### Dashboard Cards:
1. **Sell New Artwork** (`/sell_item`)
   - Create new artwork listing
   - Enter title, artist name, description
   - Specify year and category
   - Add image URL
   - Artwork added to pending pool for admin approval
   
2. **My Listings** (`/my_listings`)
   - View all artworks you've listed
   - See auction status (not assigned, in auction, sold)
   - Track which auctions contain your items
   - View creation dates

#### Database Integration:
- Creates artist if not exists
- Inserts artwork into `artworks` table
- Links to seller via `seller_id`
- Admin assigns to lots for auction

---

### 4. ADMIN (Admin-Specific Features Only)

Admins have **3 admin management cards** with exclusive administrative functionality:

#### Dashboard Cards:
1. **Admin Dashboard** (`/admin/dashboard`)
   - View total users count
   - See pending artworks (not yet in auctions)
   - Track active auctions count
   - System statistics overview
   
2. **Manage Auctions** (`/admin/manage_auctions`)
   - **Create New Auction**:
     - Set auction name
     - Define start and end dates
     - Specify location
     - Auction created in "upcoming" status
   
   - **View Auctions by Status**:
     - Upcoming auctions
     - Active auctions
     - Closed auctions (last 20)
   
   - **Auction Actions**:
     - Click auction to manage details
     - Add artworks to auction lots
     - Start auction (change status to "active")
     - Close auction (triggers payment creation)
   
3. **Manage Users** (`/admin/manage_users`)
   - View all registered users
   - See username, email, role, created date
   - Update user roles (bidder/seller/admin)
   - Role change validation (can't remove own admin status)

#### Advanced Admin Features:
- **Auction Details Page** (`/admin/auction/<auction_id>`)
  - View assigned artworks (current lots)
  - See available artworks (not yet in any auction)
  - Add artworks to auction (creates lots automatically)
  - Auto-increments lot numbers (starts at 101)
  - Start/close auction buttons
  
- **Update Auction Status** (`/admin/update_auction_status/<auction_id>/<status>`)
  - Change auction to "active" or "closed"
  - Closing auction triggers payment generation for winners
  
- **Update User Role** (`/admin/update_role/<user_id>`)
  - Change any user's role
  - Security: prevents removing own admin access

---

## Database Tables Used

### Core Tables:
1. **users** - User accounts (id, username, email, password_hash, role)
2. **artists** - Artist information (id, name)
3. **artworks** - Art pieces (id, title, description, year, category, artist_id, image_url, seller_id)
4. **auctions** - Auction events (id, name, status, start_date, end_date, location, created_by)
5. **lots** - Individual auction items (id, auction_id, lot_number, status)
6. **lot_artworks** - Links artworks to lots (id, lot_id, artwork_id)
7. **bids** - Bid records (id, bid_amount, lot_id, bidder_id, bid_timestamp)
8. **payments** - Payment records (id, lot_id, bidder_id, amount, status)
9. **audit_log** - System activity tracking

### Stored Procedures:
- `RegisterUser` - Creates new user with hashed password
- `PlaceBid` - Records a bid with validation
- `CreateArtwork` - Adds artwork and creates/links artist
- `CreateAuction` - Creates new auction event
- `AssignArtworkToLot` - Assigns artwork to auction lot

### Functions:
- `GetHighestBid(lotId)` - Returns highest bid for a lot
- `SellerTotalSales(sellerId)` - Calculates total sales
- `UserBidCount(userId)` - Counts bids by user

### Triggers:
- `check_bid_amount` - Ensures new bid is higher than current
- `mark_lot_sold` - Updates lot status when payment completed
- `update_auction_status` - Closes auction when all lots sold
- `log_bid_activity` - Records bid in audit log
- `prevent_bid_on_closed_lot` - Prevents bids on closed/sold lots
- `auto_pending_payment` - Creates pending payments when auction closes

---

## Testing the System

### 1. Test as Admin:
```
Email: admin@gallery.com
Password: admin123
```
- Login and verify all 3 admin cards appear
- Check stats on admin dashboard
- Create a new auction
- View/manage users

### 2. Create a Seller Account:
- Register new user with "seller" role
- Login and verify 5 cards appear (3 bidder + 2 seller)
- Create artwork listing
- View your listings

### 3. Create a Bidder Account:
- Register new user with "bidder" role
- Login and verify 3 bidder cards appear
- Browse auctions
- Place bids
- View bid history

### 4. Complete Workflow:
1. **Admin**: Create auction
2. **Seller**: Create artwork
3. **Admin**: Assign artwork to auction lot
4. **Admin**: Start auction (set to active)
5. **Bidder**: Browse auctions and place bid
6. **Admin**: Close auction
7. **Bidder**: View winnings and complete payment
8. **Bidder**: View receipt

---

## Security Features

- ✓ Password hashing with Werkzeug
- ✓ Session management
- ✓ Role-based access control
- ✓ Admin-only route protection with `@admin_required`
- ✓ SQL injection prevention (parameterized queries)
- ✓ Database triggers for data integrity
- ✓ Unique constraints on email and username

---

## Key URLs Summary

### Public:
- `/` - Index page
- `/register` - Register account
- `/login` - Login page
- `/logout` - Logout

### Bidder:
- `/dashboard` - User dashboard
- `/auctions` - Browse auctions
- `/auction/<id>` - Auction details
- `/my_bid_history` - Bid history
- `/my_winnings` - Winnings/payments
- `/pay/<payment_id>` - Payment page
- `/receipt/<payment_id>` - Receipt

### Seller (+ Bidder):
- `/sell_item` - Create artwork
- `/my_listings` - View listings

### Admin (+ Seller + Bidder):
- `/admin/dashboard` - Admin stats
- `/admin/manage_auctions` - Auction management
- `/admin/manage_users` - User management
- `/admin/auction/<id>` - Auction details
- `/admin/update_auction_status/<id>/<status>` - Update auction
- `/admin/update_role/<user_id>` - Update user role
