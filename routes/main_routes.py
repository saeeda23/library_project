from flask import Blueprint, render_template, session, redirect

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def root():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect('/dashboard')
        else:
            return redirect('/home')
    return render_template('welcome.html')
