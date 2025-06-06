from flask import Blueprint, render_template, request, redirect, session, url_for, flash
import sqlite3
from datetime import datetime, timedelta

book_bp = Blueprint('book', __name__)

def login_required(view_func):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.auth'))
        return view_func(*args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


# -------------------------
# Dashboard
# -------------------------
@book_bp.route('/dashboard')
@login_required
def dashboard():
    if session.get('role') != 'admin':
        return redirect('/')

    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM Books")
    total_books = c.fetchone()[0]

    c.execute("SELECT SUM(available_copies) FROM Books")
    available_copies = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(*) FROM Transactions WHERE status = 'borrowed'")
    borrowed_books = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM Transactions WHERE status = 'returned'")
    returned_books = c.fetchone()[0]

    search_query = request.args.get('q')
    if search_query:
        c.execute("""
            SELECT T.issue_date, T.due_date, T.return_date, T.status,
                   U.name AS user_name, B.title AS book_title
            FROM Transactions T
            JOIN Users U ON T.user_id = U.user_id
            JOIN Books B ON T.book_id = B.book_id
            WHERE U.name LIKE ? OR B.title LIKE ?
            ORDER BY T.transaction_id DESC
        """, (f'%{search_query}%', f'%{search_query}%'))
    else:
        c.execute("""
            SELECT T.issue_date, T.due_date, T.return_date, T.status,
                   U.name AS user_name, B.title AS book_title
            FROM Transactions T
            JOIN Users U ON T.user_id = U.user_id
            JOIN Books B ON T.book_id = B.book_id
            ORDER BY T.transaction_id DESC
        """)

    records = c.fetchall()
    conn.close()

    return render_template('dashboard.html',
                           total_books=total_books,
                           available_copies=available_copies,
                           borrowed_books=borrowed_books,
                           returned_books=returned_books,
                           records=records)


# -------------------------
# Add Book
# -------------------------
@book_bp.route('/add_book', methods=['GET', 'POST'])
@login_required
def add_book():
    # Only allow admin users
    if session.get('role') != 'admin':
        flash("Unauthorized access.")
        return redirect('/')

    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author_name']
        edition = request.form['edition']
        publisher = request.form['publisher']
        language = request.form['language']
        year = request.form['published_year']
        total = int(request.form['total_copies'])

        conn = sqlite3.connect('library.db')
        c = conn.cursor()
        c.execute("""
            INSERT INTO Books (title, author_name, edition, publisher, language, published_year, total_copies, available_copies)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, author, edition, publisher, language, year, total, total))
        conn.commit()
        conn.close()
        flash('Book added successfully!')
        return redirect('/add_book')

    return render_template('add_book.html')


# -------------------------
# Library Action (Borrow, Return, Reserve)
# -------------------------
@book_bp.route('/library_actions', methods=['GET', 'POST'])
@login_required
def library_actions():
    user_id = session['user_id']  

    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Expire outdated notified reservations (older than 2 days)
    c.execute("""
        UPDATE Reservations
        SET status = 'expired'
        WHERE status = 'notified'
          AND DATE('now') > DATE(notified_date, '+2 days')
    """)

    c.execute("SELECT * FROM Books WHERE available_copies > 0")
    available_books = c.fetchall()

    c.execute("""
        SELECT T.transaction_id, B.title, T.issue_date, T.due_date
        FROM Transactions T
        JOIN Books B ON T.book_id = B.book_id
        WHERE T.user_id = ? AND T.status = 'borrowed'
    """, (user_id,))
    borrowed_books = c.fetchall()

    c.execute("SELECT * FROM Books WHERE available_copies = 0")
    unavailable_books = c.fetchall()

    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'borrow':
            book_id = request.form['book_id']

            # Check for active reservation by another user
            c.execute("""
                SELECT * FROM Reservations
                WHERE book_id = ? AND status IN ('active', 'notified')
                ORDER BY reservation_id ASC
                LIMIT 1
            """, (book_id,))
            reservation = c.fetchone()

            if reservation:
                if reservation['user_id'] != user_id:
                    flash('This book is currently reserved by another user.')
                    conn.close()
                    return redirect('/library_actions')
                elif reservation['status'] == 'notified':
                    # Fulfill notified reservation if current user
                    c.execute("""
                        UPDATE Reservations
                        SET status = 'fulfilled'
                        WHERE reservation_id = ?
                    """, (reservation['reservation_id'],))

            # Proceed with borrowing
            c.execute("SELECT available_copies FROM Books WHERE book_id = ?", (book_id,))
            available = c.fetchone()
            if available and available['available_copies'] > 0:
                issue_date = datetime.now().date()
                due_date = issue_date + timedelta(days=14)
                c.execute("""
                    INSERT INTO Transactions (user_id, book_id, issue_date, due_date)
                    VALUES (?, ?, ?, ?)
                """, (user_id, book_id, issue_date, due_date))
                c.execute("""
                    UPDATE Books SET available_copies = available_copies - 1 WHERE book_id = ?
                """, (book_id,))

                conn.commit()
                flash('Book borrowed successfully.')
            else:
                flash('Book not available.')

        elif form_type == 'return':
            transaction_id = request.form['transaction_id']

            # Mark transaction as returned
            c.execute("""
                UPDATE Transactions
                SET return_date = DATE('now'), status = 'returned'
                WHERE transaction_id = ? AND user_id = ?
            """, (transaction_id, user_id))

            # Increment available copies
            c.execute("""
                UPDATE Books
                SET available_copies = available_copies + 1
                WHERE book_id = (
                    SELECT book_id FROM Transactions WHERE transaction_id = ?
                )
            """, (transaction_id,))

            # Get the book_id being returned
            c.execute("SELECT book_id FROM Transactions WHERE transaction_id = ?", (transaction_id,))
            result = c.fetchone()
            if result:
                book_id = result['book_id']

                # Notify the next valid user in the reservation queue
                c.execute("""
                    SELECT * FROM Reservations
                    WHERE book_id = ? AND status = 'active'
                    ORDER BY reservation_id ASC
                    LIMIT 1
                """, (book_id,))
                reservation = c.fetchone()

                if reservation:
                    c.execute("""
                        UPDATE Reservations
                        SET status = 'notified', notified_date = DATE('now')
                        WHERE reservation_id = ?
                    """, (reservation['reservation_id'],))
                    flash(f"This book is now reserved for user ID {reservation['user_id']}.")

            conn.commit()
            flash('Book returned successfully.')

        elif form_type == 'reserve':
            book_id = request.form['book_id']

            # Prevent duplicate reservation
            c.execute("""
                SELECT * FROM Reservations
                WHERE user_id = ? AND book_id = ? AND status IN ('active', 'notified')
            """, (user_id, book_id))
            already_reserved = c.fetchone()
            if already_reserved:
                flash('You have already reserved this book.')
            else:
                c.execute("""
                    INSERT INTO Reservations (user_id, book_id)
                    VALUES (?, ?)
                """, (user_id, book_id))
                conn.commit()
                flash('Book reserved successfully!')

        conn.close()
        return redirect('/library_actions')

    rendered_page = render_template(
        'library_actions.html',
        available_books=available_books,
        borrowed_books=borrowed_books,
        unavailable_books=unavailable_books
    )
    conn.close()
    return rendered_page


# -------------------------
# User History
# -------------------------
@book_bp.route('/user_history', methods=['GET'])
@login_required
def user_history():
    user_id = session['user_id']

    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
        SELECT B.title, T.issue_date, T.due_date, T.return_date, T.status
        FROM Transactions T
        JOIN Books B ON T.book_id = B.book_id
        WHERE T.user_id = ?
        ORDER BY T.issue_date DESC
    """, (user_id,))
    records = c.fetchall()
    conn.close()

    return render_template('user_history.html', records=records)








