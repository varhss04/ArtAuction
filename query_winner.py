import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="query_pool",
    pool_size=1,
    pool_reset_session=True,
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)

conn = db_pool.get_connection()
cursor = conn.cursor(dictionary=True)

auction_id = 'a75dd265-bac5-11f0-b4d0-00fff419e3c7'

# Get lots in auction
cursor.execute("SELECT id FROM lots WHERE auction_id = %s", (auction_id,))
lots = cursor.fetchall()

for lot in lots:
    lot_id = lot['id']
    # Get highest bid using direct SQL query
    cursor.execute("SELECT MAX(bid_amount) AS highest_bid FROM bids WHERE lot_id = %s", (lot_id,))
    result = cursor.fetchone()
    highest_bid = result['highest_bid']
    if highest_bid:
        # Get bidder
        cursor.execute("SELECT bidder_id FROM bids WHERE lot_id = %s AND bid_amount = %s ORDER BY bid_timestamp DESC LIMIT 1", (lot_id, highest_bid))
        bid = cursor.fetchone()
        if bid:
            bidder_id = bid['bidder_id']
            cursor.execute("SELECT username FROM users WHERE id = %s", (bidder_id,))
            user = cursor.fetchone()
            print(f"Lot {lot_id}: Winner {user['username']} with bid ${highest_bid}")
    else:
        print(f"Lot {lot_id}: No bids")

cursor.close()
conn.close()
