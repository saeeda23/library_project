from flask import Flask, render_template, redirect, session, request
from routes.auth_routes import auth_bp
from routes.book_routes import book_bp
from routes.main_routes import main_bp
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(book_bp)
app.register_blueprint(main_bp)

# Home route: show home page if logged in as user with search and books
@app.route('/home')
def home():
    if 'user_id' not in session or session.get('role') != 'user':
        return redirect('/login')

    query = request.args.get('query', '')

    conn = sqlite3.connect('library.db')
    c = conn.cursor()

    if query:
        c.execute("SELECT * FROM Books WHERE title LIKE ? OR author_name LIKE ?", 
                  ('%' + query + '%', '%' + query + '%'))
    else:
        c.execute("SELECT * FROM Books")

    books = c.fetchall()
    conn.close()

    return render_template('home.html', books=books, query=query)

# Dashboard route: show admin dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)
