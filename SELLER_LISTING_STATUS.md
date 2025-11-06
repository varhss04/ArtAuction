# Seller Listing Status - Auto-Update Feature

## ✅ What's Implemented

Seller listings now **automatically reflect auction status** in real-time!

When you visit `/my_listings`, the page will:
1. Auto-start any pending auctions that should be live
2. Show the current status of each artwork
3. Display which auction the artwork is in
4. Update status badges based on auction state

---

## 🎨 Status Badges Explained

Your artwork can have these statuses:

### 🟢 Live in Auction
```
✓ Status: "Live in Auction: Renaissance Masters"
```
**When shown:**
- Artwork is in an auction that's currently ACTIVE
- Bidders can place bids right now
- This appears when `auction_status = 'active'` and `lot_status = 'open'`

### 🟡 Scheduled for Auction
```
⏱ Status: "Scheduled for: Modern Art Sale"
```
**When shown:**
- Artwork is assigned to an upcoming auction
- Auction hasn't started yet (status = 'upcoming')
- Will auto-change to "Live" when auction starts!

### 🟠 Pending Admin Review
```
⏰ Status: "Pending Admin Review"
```
**When shown:**
- Artwork created but not assigned to any auction yet
- Waiting for admin to add it to a lot
- No auction name shown

### 🔵 Sold
```
✓ Status: "Sold"
```
**When shown:**
- Artwork sold during auction
- Payment completed by winner
- Final state - no longer available

### 🔴 Unsold
```
✗ Status: "Unsold"
```
**When shown:**
- Auction closed but item didn't sell
- No winning bid placed
- May be re-listed in future auction

### 🔴 In Closed Auction
```
📦 Status: "In Closed Auction: Renaissance Masters"
```
**When shown:**
- Auction has been closed by admin
- Item is in a closed auction
- Waiting for final processing

---

## 📊 Status Flow Example

Here's how your artwork status changes over time:

```
DAY 1: Create Artwork
└─→ "Pending Admin Review"

DAY 2: Admin assigns to upcoming auction
└─→ "Scheduled for: Renaissance Masters"
    (Auction start_date = Nov 15, 3:00 PM)

DAY 3: Nov 15, 3:00 PM arrives
└─→ Auto-starts! Now shows: "Live in Auction: Renaissance Masters"

DAY 5: Bidding continues
└─→ Still "Live in Auction: Renaissance Masters"

DAY 7: Admin closes auction
└─→ If sold: "Sold"
└─→ If no bids: "Unsold"
```

---

## 🔄 Real-Time Updates

### How Auto-Update Works:

When you visit `/my_listings`, the system:

1. **Calls `auto_start_auctions()`**
   - Checks all 'upcoming' auctions
   - If `start_date <= NOW()`, sets status to 'active'

2. **Fetches Your Listings**
   - Joins artworks → lots → auctions
   - Gets both lot_status AND auction_status

3. **Displays Dynamic Status**
   - Template checks auction_status
   - Shows appropriate badge and message

### Example Scenario:

```
10:00 AM - You create artwork "Sunset Painting"
          Status: "Pending Admin Review"

10:30 AM - Admin assigns to "Evening Sale" (starts 11:00 AM)
          Status: "Scheduled for: Evening Sale"

11:00 AM - You refresh /my_listings page
          auto_start_auctions() runs automatically
          Status: "Live in Auction: Evening Sale" ✓
```

---

## 🎯 What Each Column Shows

When viewing your listings, you see:

- **Title** - Your artwork name
- **Artist** - Artist name you provided
- **Category** - Portrait, Landscape, etc.
- **Listed** - Date you created the listing
- **Status Badge** - Current auction status (auto-updates!)

---

## 💡 Tips for Sellers

1. **Check Status Regularly**
   - Visit `/my_listings` to see current status
   - Page auto-refreshes auction states

2. **Scheduled vs Live**
   - "Scheduled" = auction not started yet
   - "Live" = bidding is happening now!

3. **Pending Review**
   - Contact admin to assign your artwork to an auction
   - Or wait for admin to review pending items

4. **After Auction Closes**
   - "Sold" = Congratulations! 🎉
   - "Unsold" = Can be re-listed in another auction

5. **Multiple Listings**
   - Each artwork tracked independently
   - Can have items in different auctions simultaneously

---

## 🔍 Database Query

The system uses this query to fetch your listings with auction info:

```sql
SELECT
    ar.title, ar.image_url, ar.created_at, ar.category,
    a.name as artist_name,
    l.status as lot_status,           -- open/sold/unsold
    au.name as auction_name,          -- auction name
    au.status as auction_status       -- upcoming/active/closed
FROM artworks ar
JOIN artists a ON ar.artist_id = a.id
LEFT JOIN lot_artworks la ON ar.id = la.artwork_id
LEFT JOIN lots l ON la.lot_id = l.id
LEFT JOIN auctions au ON l.auction_id = au.id
WHERE ar.seller_id = YOUR_ID
ORDER BY ar.created_at DESC
```

The **LEFT JOIN** ensures artworks without auctions still appear!

---

## ✅ Testing the Feature

### Test 1: Create and Wait for Auto-Start

1. Create an artwork
2. Admin assigns it to an auction with `start_date = now + 1 minute`
3. Visit `/my_listings` - see "Scheduled for: [Auction]"
4. Wait 1 minute
5. Refresh `/my_listings`
6. Should now show "Live in Auction: [Auction]" ✓

### Test 2: Multiple Artworks

1. Create 3 artworks
2. Admin assigns:
   - Art #1 to active auction
   - Art #2 to upcoming auction
   - Art #3 left unassigned
3. Visit `/my_listings`
4. Should see:
   - Art #1: "Live in Auction"
   - Art #2: "Scheduled for"
   - Art #3: "Pending Admin Review"

### Test 3: Auction Closes

1. Have artwork in active auction
2. Admin closes the auction
3. Refresh `/my_listings`
4. Status changes to "In Closed Auction" or "Sold"

---

## 🚀 Summary

✅ Listings auto-update when auctions go live  
✅ Shows clear status for each artwork  
✅ Displays which auction artwork is in  
✅ Differentiates between upcoming and active  
✅ Works automatically on page load  
✅ No manual refresh needed (just reload page)

Your seller dashboard now gives you complete visibility into where your artworks are in the auction process!
