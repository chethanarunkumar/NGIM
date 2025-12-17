from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2.extras

auth = Blueprint('auth', __name__)

# 🔐 LOGIN
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password_entered = request.form.get('password')

        conn = current_app.db
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user['password'], password_entered):
            session['user'] = user['email']
            session['role'] = user['role']
            flash(f"Welcome back, {user['role']}!", "success")
            return redirect(url_for('main.dashboard'))
        else:
            flash("❌ Invalid email or password!", "danger")

    return render_template('auth/login.html')


# 🔐 REGISTER NEW USER (auto-hashed password)
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        raw_password = request.form['password']
        role = request.form['role']

        hashed = generate_password_hash(raw_password)

        conn = current_app.db
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (email, password, role) VALUES (%s, %s, %s)",
            (email, hashed, role)
        )
        conn.commit()
        cur.close()

        flash("User created successfully!", "success")
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')
