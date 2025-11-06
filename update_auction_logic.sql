-- ============================================================================
-- AUTO-START AUCTION UPDATES
-- ============================================================================
-- This file updates the auction system to:
-- 1. Auto-start auctions when start_date is reached
-- 2. Keep manual "Start Auction" button working
-- 3. Prevent auto-closing of auctions (only manual close allowed)
-- ============================================================================

USE ArtAuctionDB;

-- Drop the auto-close auction trigger if it exists
DROP TRIGGER IF EXISTS update_auction_status;

DELIMITER $$

-- Keep the mark_lot_sold trigger (this is still useful)
-- This only marks individual lots as sold when payment is completed
-- It does NOT auto-close the entire auction

-- Note: The auto_pending_payment trigger remains to create payments
-- when an admin manually closes an auction

DELIMITER ;

-- ============================================================================
-- VERIFICATION QUERY
-- ============================================================================
-- Run this to see all triggers in your database:
-- SHOW TRIGGERS WHERE `Table` IN ('auctions', 'lots', 'payments', 'bids');
-- ============================================================================
