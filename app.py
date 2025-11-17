import os
import uuid
import mysql.connector.pooling
from mysql.connector import Error
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from functools import wraps # <<< REQUIRED FOR ADMIN
import logging

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# IMPORTANT: Use a strong, random secret key in your .env file
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-fallback-secret-key')

# File upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Database Connection Pool ---
db_pool = None # Initialize pool variable
try:
    db_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="auction_pool",
        pool_size=5, # Number of connections to keep ready
        pool_reset_session=True, # Resets session variables for reused connections
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    print("Database connection pool created successfully.")
except Error as e:
    print(f"FATAL ERROR creating database connection pool: {e}")
    exit(1) # Exit if the pool can't be created

# --- Helper Function to Get Connection ---
def get_db_connection():
    """Get a connection from the pool."""
    if db_pool is None:
        print("!!! ERROR: Database pool was not initialized.")
        return None
    try:
        conn = db_pool.get_connection()
        return conn
    except Error as e:
        print(f"!!! ERROR DURING REQUEST: Failed to get connection from pool: {e}")
        return None

# Create default admin user if not exists
try:
    conn = get_db_connection()
    if conn is None: raise Error("Failed to get DB connection")
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE email = 'admin@artgallery.com'")
    if not cursor.fetchone():
        # Create default admin
        admin_id = str(uuid.uuid4())
        hashed_password = generate_password_hash('admin123')
        cursor.execute("INSERT INTO users (id, username, email, password_hash, role) VALUES (%s, %s, %s, %s, %s)",
                       (admin_id, 'admin', 'admin@artgallery.com', hashed_password, 'admin'))
        conn.commit()
        print("Default admin user created: admin@artgallery.com / admin123")
    cursor.close()
    conn.close()
except Error as e:
    print(f"Error creating default admin: {e}")

# --- Context Processor for Global Data ---
@app.context_processor
def inject_global_data():
    conn = None
    cursor = None
    competitive_lots = []
    top_bidders = []
    try:
        conn = get_db_connection()
        if conn is None: raise Error("Failed to get DB connection")
        cursor = conn.cursor(dictionary=True)

        # Competitive lots
        competitive_query = """
            SELECT l.id AS lot_id, COUNT(b.id) AS total_bids, a.name AS auction_name,
                   ar.title, ar.image_url, t.name AS artist_name
            FROM lots l
            JOIN bids b ON l.id = b.lot_id
            JOIN auctions a ON l.auction_id = a.id
            JOIN lot_artworks la ON l.id = la.lot_id
            JOIN artworks ar ON la.artwork_id = ar.id
            JOIN artists t ON ar.artist_id = t.id
            GROUP BY l.id, a.name, ar.title, ar.image_url, t.name
            ORDER BY total_bids DESC
            LIMIT 5;
        """
        cursor.execute(competitive_query)
        competitive_lots = cursor.fetchall()

        # Top bidders
        bidders_query = """
            SELECT u.username, COUNT(b.id) AS bid_count
            FROM users u
            JOIN bids b ON u.id = b.bidder_id
            GROUP BY u.id, u.username
            ORDER BY bid_count DESC
            LIMIT 5;
        """
        cursor.execute(bidders_query)
        top_bidders = cursor.fetchall()

    except Error as e:
        print(f"!!! DB Error (Global Data): {e}")
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
    return {'global_competitive_lots': competitive_lots, 'global_top_bidders': top_bidders}

# --- Helper Function to Auto-Start Auctions ---
def auto_start_auctions():
    """
    Automatically starts auctions that have reached their start_date.
    Called on various page loads to ensure auctions go live on time.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return
        
        cursor = conn.cursor()
        # Update auctions to 'active' if start_date has passed and status is still 'upcoming'
        query = """
            UPDATE auctions 
            SET status = 'active' 
            WHERE status = 'upcoming' 
            AND start_date <= NOW()
        """
        cursor.execute(query)
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info(f"Auto-started {cursor.rowcount} auction(s)")
            
    except Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Error auto-starting auctions: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# =============================================================
# USER AUTHENTICATION ROUTES
# =============================================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    conn = None
    cursor = None
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'bidder') 

        try:
            conn = get_db_connection()
            if conn is None:
                flash("Database connection error. Please try again later.", "danger")
                return render_template('register.html')

            cursor = conn.cursor()
            user_id = str(uuid.uuid4())
            hashed_password = generate_password_hash(password)

            cursor.execute("INSERT INTO users (id, username, email, password_hash, role) VALUES (%s, %s, %s, %s, %s)",
                           (user_id, username, email, hashed_password, role))
            conn.commit()

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))

        except Error as e:
            conn.rollback() 
            if e.errno == 1062: # Duplicate entry
                flash("Username or Email already exists.", "danger")
            else:
                flash(f"An error occurred during registration: {e.msg}", "danger")
                print(f"!!! DB Error (Register): {e}")
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    conn = None
    cursor = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            conn = get_db_connection()
            if conn is None:
                flash("Database connection error. Please try again later.", "danger")
                return render_template('login.html')

            cursor = conn.cursor(dictionary=True)
            query = "SELECT id, username, password_hash, role FROM users WHERE email = %s"
            cursor.execute(query, (email,))
            user = cursor.fetchone()

            # Standard check
            if user and user.get('password_hash') and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id']
                session['user_role'] = user['role']
                session['username'] = user['username']

                # Update last login timestamp
                update_query = "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s"
                cursor.execute(update_query, (user['id'],))
                conn.commit()

                flash(f"Welcome back, {user['username']}!", 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password.', 'danger')

        except Error as e:
            flash(f"An error occurred during login: {e.msg}", "danger")
            print(f"!!! DB Error (Login): {e}")
        except ValueError as ve: # Catch the hash error
              flash(f"Login Error: Could not verify password hash. {ve}", "danger")
              print(f"!!! Value Error (Login - check_password_hash): {ve}")
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/api/welcome', methods=['GET'])
def api_welcome():
    logger.info(f"Request received: {request.method} {request.path}")
    return jsonify({'message': 'Welcome to the Art Gallery Auction API!'})

# =============================================================
# CORE APP ROUTES
# =============================================================

@app.route('/')
def index():
    conn = None
    cursor = None
    top_sellers = []
    try:
        conn = get_db_connection()
        if conn is None: raise Error("Failed to get DB connection")
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT u.username, SUM(p.amount) AS total_sales
            FROM users u
            JOIN artworks a ON u.id = a.seller_id
            JOIN lot_artworks la ON a.id = la.artwork_id
            JOIN lots l ON la.lot_id = l.id
            JOIN payments p ON l.id = p.lot_id
            WHERE p.status = 'completed'
            GROUP BY u.username
            ORDER BY total_sales DESC
            LIMIT 5;
        """
        cursor.execute(query)
        top_sellers = cursor.fetchall()
    except Error as e:
        print(f"!!! DB Error (Top Sellers): {e}")
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
    return render_template('index.html', top_sellers=top_sellers)

@app.route('/index')
def index_page():
    return render_template('index.html')

@app.route('/auctions')
def auctions():
    # Auto-start any auctions that should be active
    auto_start_auctions()

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None: raise Error("Failed to get DB connection")
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT a.id, a.name, a.status, a.end_date, COUNT(l.id) as lot_count
            FROM auctions a
            LEFT JOIN lots l ON a.id = l.auction_id
            WHERE a.status = 'active'
            GROUP BY a.id ORDER BY a.end_date ASC
        """
        cursor.execute(query)
        active_auctions = cursor.fetchall()

        # Fetch most competitive lots
        competitive_query = """
            SELECT l.id AS lot_id, COUNT(b.id) AS total_bids, a.name AS auction_name,
                   ar.title, ar.image_url, t.name AS artist_name
            FROM lots l
            JOIN bids b ON l.id = b.lot_id
            JOIN auctions a ON l.auction_id = a.id
            JOIN lot_artworks la ON l.id = la.lot_id
            JOIN artworks ar ON la.artwork_id = ar.id
            JOIN artists t ON ar.artist_id = t.id
            WHERE a.status = 'active'
            GROUP BY l.id, a.name, ar.title, ar.image_url, t.name
            ORDER BY total_bids DESC
            LIMIT 5;
        """
        cursor.execute(competitive_query)
        competitive_lots = cursor.fetchall()

        return render_template('auctions.html', auctions=active_auctions, competitive_lots=competitive_lots)
    except Error as e:
        flash(f"Error fetching auctions: {e.msg}", "danger")
        print(f"!!! DB Error (Auctions): {e}")
        return render_template('auctions.html', auctions=[], competitive_lots=[])
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

@app.route('/auction/<string:auction_id>')
def auction_details(auction_id):
    if 'user_id' not in session:
        flash('Please log in to view auction details.', 'warning')
        return redirect(url_for('login'))

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None: raise Error("Failed to get DB connection")
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, name, status FROM auctions WHERE id = %s", (auction_id,))
        auction = cursor.fetchone()
        if not auction:
            flash("Auction not found.", "danger")
            return redirect(url_for('auctions'))

        query_lots = """
            SELECT l.id as lot_id, l.lot_number, l.status,
                   ar.title, ar.description, ar.image_url, t.name as artist_name
            FROM lots l
            JOIN lot_artworks la ON l.id = la.lot_id
            JOIN artworks ar ON la.artwork_id = ar.id
            JOIN artists t ON ar.artist_id = t.id
            WHERE l.auction_id = %s ORDER BY l.lot_number ASC
        """
        cursor.execute(query_lots, (auction_id,))
        lots = cursor.fetchall()

        for lot in lots:
            cursor.execute("SELECT GetHighestBid(%s) AS highest_bid", (lot['lot_id'],))
            result = cursor.fetchone()
            lot['highest_bid'] = result['highest_bid'] if result and result['highest_bid'] is not None else 0.00

        return render_template('bids.html', lots=lots, auction=auction, auction_id=auction_id)

    except Error as e:
        flash(f"Error fetching auction details: {e.msg}", "danger")
        print(f"!!! DB Error (Auction Details): {e}")
        return redirect(url_for('auctions'))
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

@app.route('/place_bid', methods=['POST'])
def place_bid():
    if 'user_id' not in session:
        flash('You must be logged in to place a bid.', 'warning')
        return redirect(url_for('login'))

    conn = None
    cursor = None
    lot_id = request.form.get('lot_id')
    auction_id = request.form.get('auction_id')
    amount = request.form.get('amount')
    bidder_id = session['user_id']

    if not all([lot_id, auction_id, amount]):
        flash('Missing bid information.', 'danger')
        return redirect(request.referrer or url_for('auctions')) 

    try:
        conn = get_db_connection()
        if conn is None: raise Error("Failed to get DB connection")
        cursor = conn.cursor()
        bid_id = str(uuid.uuid4())

        cursor.execute("INSERT INTO bids (id, bid_amount, lot_id, bidder_id) VALUES (%s, %s, %s, %s)",
                       (bid_id, amount, lot_id, bidder_id))
        conn.commit()
        flash('Bid placed successfully!', 'success')

    except Error as e:
        conn.rollback() 
        if e.sqlstate == '45000': 
            flash(f"Bid Error: {e.msg}", "danger")
        else:
            flash(f"An error occurred placing bid: {e.msg}", "danger")
            print(f"!!! DB Error (Place Bid): {e}")
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

    return redirect(url_for('auction_details', auction_id=auction_id))

# =============================================================
# DASHBOARD & RELATED ROUTES
# =============================================================

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))
    
    # Auto-start any auctions that should be active
    auto_start_auctions()
    
    return render_template('dashboard.html')

@app.route('/my_winnings')
def my_winnings():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))

    conn = None
    cursor = None
    winnings = []
    try:
        conn = get_db_connection()
        if conn is None: raise Error("Failed to get DB connection")
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT p.id as payment_id, p.amount, p.status, p.payment_date,
                   l.lot_number,
                   ar.title, ar.image_url, t.name as artist_name
            FROM payments p
            JOIN lots l ON p.lot_id = l.id
            JOIN lot_artworks la ON l.id = la.lot_id
            JOIN artworks ar ON la.artwork_id = ar.id
            JOIN artists t ON ar.artist_id = t.id
            WHERE p.bidder_id = %s
            ORDER BY p.payment_date DESC
        """
        cursor.execute(query, (session['user_id'],))
        winnings = cursor.fetchall()
    except Error as e:
        flash(f"Error fetching your winnings: {e.msg}", "danger")
        print(f"!!! DB Error (My Winnings): {e}")
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
    return render_template('my_winnings.html', winnings=winnings)

@app.route('/sell_item', methods=['GET', 'POST'])
def sell_item():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))
    if session.get('user_role') != 'seller':
        flash('You must be a seller to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    conn = None
    cursor = None
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            artist_name = request.form.get('artist_name')
            description = request.form.get('description', '') 
            year = request.form.get('year') 
            category = request.form.get('category', '') 
            image_url = request.form.get('image_url')
            seller_id = session['user_id']

            # Validation
            if not title or not artist_name or not image_url:
                flash('Title, Artist Name, and Image URL are required.', 'danger')
                return render_template('sell_item.html')

            year_int = int(year) if year and year.isdigit() else None

            conn = get_db_connection()
            if conn is None: raise Error("Failed to get DB connection")
            cursor = conn.cursor()

            # First, check if artist exists, if not, insert
            cursor.execute("SELECT id FROM artists WHERE name = %s", (artist_name,))
            artist = cursor.fetchone()
            if not artist:
                artist_id = str(uuid.uuid4())
                cursor.execute("INSERT INTO artists (id, name) VALUES (%s, %s)", (artist_id, artist_name))
            else:
                artist_id = artist['id']

            artwork_id = str(uuid.uuid4())
            cursor.execute("INSERT INTO artworks (id, seller_id, artist_id, title, description, year, category, image_url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                           (artwork_id, seller_id, artist_id, title, description, year_int, category, image_url))
            conn.commit()

            flash('New artwork listed successfully!', 'success')
            return redirect(url_for('my_listings')) 

        except Error as e:
            if conn: conn.rollback()
            flash(f"Error listing item: {e.msg}", "danger")
            print(f"!!! DB Error (Sell Item): {e}")
        except ValueError:
             flash("Invalid year provided. Please enter a number.", "danger")
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    return render_template('sell_item.html')

@app.route('/pay/<string:payment_id>', methods=['GET', 'POST'])
def payment_page(payment_id):
    if 'user_id' not in session:
        flash('Please log in.', 'warning')
        return redirect(url_for('login'))

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None: raise Error("Failed to get DB connection")
        cursor = conn.cursor(dictionary=True)

        if request.method == 'POST':
            update_query = """
                UPDATE payments SET status = 'completed', payment_date = CURRENT_TIMESTAMP
                WHERE id = %s AND bidder_id = %s AND status = 'pending'
            """
            cursor.execute(update_query, (payment_id, session['user_id']))
            conn.commit()

            if cursor.rowcount > 0: 
                flash('Payment successful!', 'success')
                return redirect(url_for('receipt_page', payment_id=payment_id))
            else:
                 flash('Payment could not be processed. It might already be completed or invalid.', 'warning')
                 return redirect(url_for('my_winnings'))


        else: # GET Request
            query = """
                SELECT p.id as payment_id, p.amount, p.status, 
                       ar.title, ar.image_url, t.name as artist_name
                FROM payments p
                JOIN lots l ON p.lot_id = l.id
                JOIN lot_artworks la ON l.id = la.lot_id
                JOIN artworks ar ON la.artwork_id = ar.id
                JOIN artists t ON ar.artist_id = t.id
                WHERE p.id = %s AND p.bidder_id = %s
            """
            cursor.execute(query, (payment_id, session['user_id']))
            item = cursor.fetchone()

            if not item:
                flash("Payment record not found.", "danger")
                return redirect(url_for('my_winnings'))

            if item['status'] == 'completed':
                flash("This item is already paid.", "info")
                return redirect(url_for('receipt_page', payment_id=payment_id))

            return render_template('payment.html', item=item)

    except Error as e:
        if conn and request.method == 'POST': conn.rollback() 
        flash(f"An error occurred during payment: {e.msg}", "danger")
        print(f"!!! DB Error (Payment Page): {e}")
        return redirect(url_for('my_winnings'))
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


@app.route('/receipt/<string:payment_id>')
def receipt_page(payment_id):
    if 'user_id' not in session:
        flash('Please log in.', 'warning')
        return redirect(url_for('login'))

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None: raise Error("Failed to get DB connection")
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT
                p.id as payment_id, p.amount, p.payment_date, p.payment_method, p.status, 
                ar.title, ar.image_url, ar.year,
                art.name as artist_name,
                bidder.username as bidder_name, bidder.email as bidder_email,
                seller.username as seller_name
            FROM payments p
            JOIN users bidder ON p.bidder_id = bidder.id
            JOIN lots l ON p.lot_id = l.id
            JOIN lot_artworks la ON l.id = la.lot_id
            JOIN artworks ar ON la.artwork_id = ar.id
            JOIN artists art ON ar.artist_id = art.id
            JOIN users seller ON ar.seller_id = seller.id
            WHERE p.id = %s AND p.bidder_id = %s
        """
        cursor.execute(query, (payment_id, session['user_id']))
        item = cursor.fetchone()

        if not item:
            flash("Receipt not found.", "danger")
            return redirect(url_for('my_winnings'))

        if item['status'] != 'completed':
            flash("Payment for this item is not completed.", "warning")
            return redirect(url_for('payment_page', payment_id=payment_id))

        return render_template('receipt.html', item=item)

    except Error as e:
        flash(f"Error fetching receipt: {e.msg}", "danger")
        print(f"!!! DB Error (Receipt): {e}")
        return redirect(url_for('my_winnings'))
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

@app.route('/my_listings')
def my_listings():
    if 'user_id' not in session:
        flash('Please log in.', 'warning')
        return redirect(url_for('login'))
    if session.get('user_role') != 'seller':
        flash('Sellers only.', 'danger')
        return redirect(url_for('dashboard'))

    # Auto-start any auctions that should be active
    auto_start_auctions()

    conn = None
    cursor = None
    listings = []
    total_sales = 0.00
    try:
        conn = get_db_connection()
        if conn is None: raise Error("Failed to get DB connection")
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT
                ar.title, ar.image_url, ar.created_at, ar.category,
                a.name as artist_name,
                l.status as lot_status,
                au.name as auction_name,
                au.status as auction_status
            FROM artworks ar
            JOIN artists a ON ar.artist_id = a.id
            LEFT JOIN lot_artworks la ON ar.id = la.artwork_id
            LEFT JOIN lots l ON la.lot_id = l.id
            LEFT JOIN auctions au ON l.auction_id = au.id
            WHERE ar.seller_id = %s
            ORDER BY ar.created_at DESC
        """
        cursor.execute(query, (session['user_id'],))
        listings = cursor.fetchall()

        # Get total sales
        cursor.execute("SELECT SUM(p.amount) AS total_sales FROM payments p JOIN lots l ON p.lot_id = l.id JOIN lot_artworks la ON l.id = la.lot_id JOIN artworks a ON la.artwork_id = a.id WHERE a.seller_id = %s AND p.status = 'completed'", (session['user_id'],))
        result = cursor.fetchone()
        total_sales = result['total_sales'] if result and result['total_sales'] else 0.00
    except Error as e:
        flash(f"Error fetching listings: {e.msg}", "danger")
        print(f"!!! DB Error (My Listings): {e}")
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
    return render_template('my_listings.html', listings=listings, total_sales=total_sales)

@app.route('/my_bid_history')
def my_bid_history():
    if 'user_id' not in session:
        flash('Please log in.', 'warning')
        return redirect(url_for('login'))

    conn = None
    cursor = None
    bids = []
    bid_count = 0
    try:
        conn = get_db_connection()
        if conn is None: raise Error("Failed to get DB connection")
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT
                b.bid_amount, b.bid_timestamp,
                ar.title, ar.image_url,
                l.status as lot_status,
                au.id as auction_id
            FROM bids b
            JOIN lots l ON b.lot_id = l.id
            JOIN lot_artworks la ON l.id = la.lot_id
            JOIN artworks ar ON la.artwork_id = ar.id
            JOIN auctions au ON l.auction_id = au.id
            WHERE b.bidder_id = %s
            ORDER BY b.bid_timestamp DESC
        """
        cursor.execute(query, (session['user_id'],))
        bids = cursor.fetchall()

        # Get bid count
        cursor.execute("SELECT COUNT(*) AS bid_count FROM bids WHERE bidder_id = %s", (session['user_id'],))
        result = cursor.fetchone()
        bid_count = result['bid_count'] if result and result['bid_count'] else 0
    except Error as e:
        flash(f"Error fetching bid history: {e.msg}", "danger")
        print(f"!!! DB Error (Bid History): {e}")
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
    return render_template('my_bid_history.html', bids=bids, bid_count=bid_count)

# =============================================================
# ADMIN PANEL ROUTES
# =============================================================

# --- Helper function for admin security ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = None
    cursor = None
    stats = {'total_users': 0, 'pending_artworks': 0, 'active_auctions': 0}
    top_sellers = []
    competitive_lots = []
    auction_winners = []
    try:
        conn = get_db_connection()
        if conn is None: raise Error("Failed to get DB connection")
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) as count FROM users")
        res = cursor.fetchone()
        stats['total_users'] = res['count'] if res else 0

        cursor.execute("""
            SELECT COUNT(*) as count FROM artworks
            WHERE id NOT IN (SELECT DISTINCT artwork_id FROM lot_artworks WHERE artwork_id IS NOT NULL)
        """)
        res = cursor.fetchone()
        stats['pending_artworks'] = res['count'] if res else 0

        cursor.execute("SELECT COUNT(*) as count FROM auctions WHERE status = 'active'")
        res = cursor.fetchone()
        stats['active_auctions'] = res['count'] if res else 0

        # Top sellers
        query = """
            SELECT u.username, SUM(p.amount) AS total_sales
            FROM users u
            JOIN artworks a ON u.id = a.seller_id
            JOIN lot_artworks la ON a.id = la.artwork_id
            JOIN lots l ON la.lot_id = l.id
            JOIN payments p ON l.id = p.lot_id
            WHERE p.status = 'completed'
            GROUP BY u.username
            ORDER BY total_sales DESC
            LIMIT 5;
        """
        cursor.execute(query)
        top_sellers = cursor.fetchall()

        # Competitive lots
        competitive_query = """
            SELECT l.id AS lot_id, COUNT(b.id) AS total_bids, a.name AS auction_name,
                   ar.title, ar.image_url, t.name AS artist_name
            FROM lots l
            JOIN bids b ON l.id = b.lot_id
            JOIN auctions a ON l.auction_id = a.id
            JOIN lot_artworks la ON l.id = la.lot_id
            JOIN artworks ar ON la.artwork_id = ar.id
            JOIN artists t ON ar.artist_id = t.id
            GROUP BY l.id, a.name, ar.title, ar.image_url, t.name
            ORDER BY total_bids DESC
            LIMIT 5;
        """
        cursor.execute(competitive_query)
        competitive_lots = cursor.fetchall()

        # Auction winners
        winners_query = """
            SELECT p.lot_id, u.username AS winner, p.amount, p.status, a.name AS auction_name
            FROM payments p
            JOIN users u ON p.bidder_id = u.id
            JOIN lots l ON p.lot_id = l.id
            JOIN auctions a ON l.auction_id = a.id
            WHERE p.status = 'completed'
            ORDER BY p.payment_date DESC
            LIMIT 10;
        """
        cursor.execute(winners_query)
        auction_winners = cursor.fetchall()

    except Error as e:
        flash(f"Error fetching admin stats: {e.msg}", "danger")
        print(f"!!! DB Error (Admin Stats): {e}")
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
    return render_template('admin_dashboard.html', stats=stats, top_sellers=top_sellers, competitive_lots=competitive_lots, auction_winners=auction_winners)

@app.route('/admin/manage_auctions', methods=['GET', 'POST'])
@admin_required
def admin_manage_auctions():
    # Auto-start any auctions that should be active
    auto_start_auctions()
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None: raise Error("Failed to get DB connection")

        if request.method == 'POST':
            try:
                name = request.form['name']
                start_date = request.form['start_date']
                end_date = request.form['end_date']
                location = request.form.get('location', '') 
                admin_id = session['user_id']

                cursor = conn.cursor()
                auction_id = str(uuid.uuid4())
                cursor.execute("INSERT INTO auctions (id, admin_id, name, start_date, end_date, location, status) VALUES (%s, %s, %s, %s, %s, %s, 'upcoming')",
                               (auction_id, admin_id, name, start_date, end_date, location))
                conn.commit()
                flash(f"Auction '{name}' created.", 'success')
            except Error as e:
                if conn: conn.rollback()
                flash(f"Error creating auction: {e.msg}", "danger")
                print(f"!!! DB Error (Create Auction): {e}")
            
            return redirect(url_for('admin_manage_auctions'))

        # --- Display Page (GET) ---
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, status, start_date FROM auctions WHERE status = 'upcoming' ORDER BY start_date ASC")
        upcoming_auctions = cursor.fetchall()
        cursor.execute("SELECT id, name, status, end_date FROM auctions WHERE status = 'active' ORDER BY end_date ASC")
        active_auctions = cursor.fetchall()
        cursor.execute("SELECT id, name, status, end_date FROM auctions WHERE status = 'closed' ORDER BY end_date DESC LIMIT 20")
        closed_auctions = cursor.fetchall()

        return render_template('admin_manage_auctions.html',
                               upcoming=upcoming_auctions,
                               active=active_auctions,
                               closed=closed_auctions)

    except Error as e:
        flash(f"Error managing auctions: {e.msg}", "danger")
        print(f"!!! DB Error (Manage Auctions): {e}")
        return redirect(url_for('admin_dashboard'))
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

#
# --- THIS IS THE CORRECT, SINGLE 'admin_manage_users' FUNCTION ---
#
@app.route('/admin/manage_users')
@admin_required
def admin_manage_users():
    conn = None
    cursor = None
    users = []
    try:
        conn = get_db_connection()
        if conn is None: raise Error("Failed to get DB connection")
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT id, username, email, role, created_at, last_login FROM users ORDER BY created_at DESC"
        cursor.execute(query)
        users = cursor.fetchall()
        
    except Error as e:
        flash(f"Error fetching users: {e.msg}", "danger")
        print(f"!!! DB Error (Manage Users): {e}")
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
            
    return render_template('admin_manage_users.html', users=users)

#
# --- THIS IS THE FUNCTION TO UPDATE ROLES ---
#
@app.route('/admin/update_role/<string:user_id>', methods=['POST'])
@admin_required
def admin_update_role(user_id):
    new_role = request.form.get('role')
    if new_role not in ['bidder', 'seller', 'admin']:
        flash("Invalid role selected.", 'danger')
        return redirect(url_for('admin_manage_users'))

    if user_id == session['user_id'] and new_role != 'admin':
        flash("You cannot remove your own admin status.", 'danger')
        return redirect(url_for('admin_manage_users'))

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None: raise Error("Failed to get DB connection")
        cursor = conn.cursor()
        
        cursor.execute("UPDATE users SET role = %s WHERE id = %s", (new_role, user_id))
        conn.commit()
        flash("User role updated successfully.", 'success')
        
    except Error as e:
        if conn: conn.rollback()
        flash(f"Error updating role: {e.msg}", "danger")
        print(f"!!! DB Error (Update Role): {e}")
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
            
    return redirect(url_for('admin_manage_users'))

#
# --- THIS IS THE AUCTION DETAILS PAGE (FOR ADDING LOTS) ---
#
@app.route('/admin/auction/<string:auction_id>', methods=['GET', 'POST'])
@admin_required
def admin_auction_details(auction_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None: raise Error("Failed to get DB connection")

        if request.method == 'POST':
            artwork_id = request.form.get('artwork_id')
            if artwork_id:
                try:
                    cursor = conn.cursor()
                    lot_id = str(uuid.uuid4())
                    cursor.execute("INSERT INTO lots (id, auction_id, lot_number, status) VALUES (%s, %s, (SELECT COALESCE(MAX(lot_number), 0) + 1 FROM lots WHERE auction_id = %s), 'active')",
                                   (lot_id, auction_id, auction_id))
                    cursor.execute("INSERT INTO lot_artworks (lot_id, artwork_id) VALUES (%s, %s)", (lot_id, artwork_id))
                    conn.commit()
                    flash("Artwork added to auction.", 'success')
                except Error as e:
                    if conn: conn.rollback()
                    flash(f"Error adding artwork: {e.msg}", "danger")
                    print(f"!!! DB Error (Assign Artwork): {e}")
            else:
                 flash("No artwork selected to add.", "warning")
            return redirect(url_for('admin_auction_details', auction_id=auction_id))

        # --- Display Page (GET) ---
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, status FROM auctions WHERE id = %s", (auction_id,))
        auction = cursor.fetchone()
        if not auction:
            flash("Auction not found.", "danger")
            return redirect(url_for('admin_manage_auctions'))

        # Get assigned artworks with winner info for closed auctions
        query_assigned = """
            SELECT ar.id as artwork_id, ar.title, ar.image_url, l.lot_number, art.name as artist_name,
                   u.username as winner_name, p.amount, p.status as payment_status
            FROM artworks ar JOIN artists art ON ar.artist_id = art.id
            JOIN lot_artworks la ON ar.id = la.artwork_id
            JOIN lots l ON la.lot_id = l.id
            LEFT JOIN payments p ON l.id = p.lot_id
            LEFT JOIN users u ON p.bidder_id = u.id
            WHERE l.auction_id = %s ORDER BY l.lot_number ASC
        """
        cursor.execute(query_assigned, (auction_id,))
        assigned_artworks = cursor.fetchall()

        query_available = """
            SELECT ar.id, ar.title, ar.image_url, art.name as artist_name, u.username as seller_name
            FROM artworks ar JOIN artists art ON ar.artist_id = art.id
            JOIN users u ON ar.seller_id = u.id
            WHERE ar.id NOT IN (SELECT DISTINCT artwork_id FROM lot_artworks WHERE artwork_id IS NOT NULL)
            ORDER BY ar.created_at DESC
        """
        cursor.execute(query_available)
        available_artworks = cursor.fetchall()

        return render_template('admin_auction_details.html',
                               auction=auction,
                               assigned_artworks=assigned_artworks,
                               available_artworks=available_artworks)

    except Error as e:
        flash(f"Error fetching auction details: {e.msg}", "danger")
        print(f"!!! DB Error (Admin Auction Details): {e}")
        return redirect(url_for('admin_manage_auctions'))
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

#
# --- THIS IS THE ROUTE TO START/CLOSE AUCTIONS ---
#
@app.route('/admin/update_auction_status/<string:auction_id>/<string:status>', methods=['POST'])
@admin_required
def admin_update_auction_status(auction_id, status):
    if status not in ['active', 'closed']:
        flash("Invalid status update.", 'danger')
        return redirect(url_for('admin_auction_details', auction_id=auction_id))

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None: raise Error("Failed to get DB connection")
        cursor = conn.cursor()

        cursor.execute("UPDATE auctions SET status = %s WHERE id = %s", (status, auction_id))
        conn.commit()

        flash(f"Auction status updated to '{status}'.", 'success')

    except Error as e:
        if conn: conn.rollback()
        flash(f"Error updating auction status: {e.msg}", "danger")
        print(f"!!! DB Error (Update Auction Status): {e}")
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

    return redirect(url_for('admin_auction_details', auction_id=auction_id))

@app.route('/admin/review_artworks')
@admin_required
def admin_review_artworks():
    conn = None
    cursor = None
    pending_artworks = []
    try:
        conn = get_db_connection()
        if conn is None: raise Error("Failed to get DB connection")
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT ar.id, ar.title, ar.description, ar.year, ar.category, ar.image_url, ar.created_at,
                   a.name as artist_name, u.username as seller_name
            FROM artworks ar
            JOIN artists a ON ar.artist_id = a.id
            JOIN users u ON ar.seller_id = u.id
            WHERE ar.id NOT IN (SELECT DISTINCT artwork_id FROM lot_artworks WHERE artwork_id IS NOT NULL)
            ORDER BY ar.created_at DESC
        """
        cursor.execute(query)
        pending_artworks = cursor.fetchall()
        
        cursor.execute("SELECT id, name, status FROM auctions WHERE status IN ('upcoming', 'active') ORDER BY start_date ASC")
        available_auctions = cursor.fetchall()
        
    except Error as e:
        flash(f"Error fetching artworks: {e.msg}", "danger")
        print(f"!!! DB Error (Review Artworks): {e}")
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
    
    return render_template('admin_review_artworks.html', artworks=pending_artworks, auctions=available_auctions)

@app.route('/admin/assign_to_auction', methods=['POST'])
@admin_required
def admin_assign_to_auction():
    artwork_id = request.form.get('artwork_id')
    auction_id = request.form.get('auction_id')
    
    if not artwork_id or not auction_id:
        flash('Missing artwork or auction selection.', 'danger')
        return redirect(url_for('admin_review_artworks'))
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None: raise Error("Failed to get DB connection")
        cursor = conn.cursor()

        lot_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO lots (id, auction_id, lot_number, status) VALUES (%s, %s, (SELECT COALESCE(MAX(lot_number), 0) + 1 FROM lots WHERE auction_id = %s), 'active')",
                       (lot_id, auction_id, auction_id))
        cursor.execute("INSERT INTO lot_artworks (lot_id, artwork_id) VALUES (%s, %s)", (lot_id, artwork_id))
        conn.commit()
        flash('Artwork assigned to auction successfully!', 'success')
        
    except Error as e:
        if conn: conn.rollback()
        flash(f"Error assigning artwork: {e.msg}", "danger")
        print(f"!!! DB Error (Assign Artwork): {e}")
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
    
    return redirect(url_for('admin_review_artworks'))


# --- Run the App ---
if __name__ == '__main__':
    app.run(debug=True)