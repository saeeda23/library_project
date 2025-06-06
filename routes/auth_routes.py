from flask import Blueprint, render_template, request, redirect, session, flash
import sqlite3

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = sqlite3.connect('library.db')
        c = conn.cursor()
        c.execute("SELECT * FROM Users WHERE email = ? AND password = ?", (email, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[4]
            return redirect('/')
        else:
            flash('Invalid login credentials', 'danger')

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'user')

        conn = sqlite3.connect('library.db')
        c = conn.cursor()

        try:
            c.execute("INSERT INTO Users (name, email, password, role) VALUES (?, ?, ?, ?)",
                      (name, email, password, role))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect('/login')
        except sqlite3.IntegrityError:
            flash('Email already exists!', 'danger')
        finally:
            conn.close()

    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/')  # Redirect to welcome page after logout



