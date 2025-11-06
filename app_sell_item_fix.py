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

            args = (seller_id, title, description, year_int, category, image_url, artist_name)
            cursor.callproc('CreateArtwork', args)
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
