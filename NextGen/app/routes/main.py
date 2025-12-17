from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, session, current_app
from datetime import datetime

import psycopg2.extras

main = Blueprint('main', __name__)

# -------------------------
# Helper: ensure activity table and logging
# -------------------------
def ensure_recent_activities_table(conn):
    """Create recent_activities table if it doesn't exist."""
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS recent_activities (
                id SERIAL PRIMARY KEY,
                activity_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass

def log_activity(conn, message):
    """Insert a new activity row (safe: creates table if missing)."""
    try:
        ensure_recent_activities_table(conn)
        cur = conn.cursor()
        cur.execute("INSERT INTO recent_activities (activity_text) VALUES (%s);", (message,))
        conn.commit()
        cur.close()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        # silent fail - activity logging should not break main flow

# 🏠 Home
@main.route('/')
def index():
    return render_template('index.html')


# 🧭 Main Dashboard (with live PostgreSQL stats)
@main.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('auth.login'))  # 🔥 FIXED HERE

    try:
        conn = current_app.db
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Total products
        cur.execute("SELECT COUNT(*) FROM products;")
        total_products = cur.fetchone()['count']

        # Low stock products (using reorder_threshold)
        # Fetch global minimum stock level (fixed number)
        cur.execute("SELECT min_stock_level FROM auto_order_settings LIMIT 1;")
        row = cur.fetchone()
        min_stock_level = row['min_stock_level'] if row else 40  # default 40

        # Low Stock Count (fixed rule)
        cur.execute("""
            SELECT COUNT(*)
            FROM products
            WHERE stock_qty < %s;
        """, (min_stock_level,))

        low_stock = cur.fetchone()['count']

        # Expiring soon batches
        cur.execute("""
            SELECT COUNT(*) 
            FROM products 
            WHERE expiry_date <= NOW() + INTERVAL '7 days';
        """)
        expiring_soon = cur.fetchone()['count']

        # Monthly revenue (safe - set to 0 if null)
        total_revenue = 0
        try:
            cur.execute("""
                SELECT SUM(total_amount) AS total_revenue
                FROM sales
                WHERE DATE_TRUNC('month', sale_date) = DATE_TRUNC('month', CURRENT_DATE);
            """)
            tr = cur.fetchone()
            total_revenue = tr['total_revenue'] or 0
        except Exception:
            total_revenue = 0

        # Fetch recent activities from DB (last 10)
        recent_activities = []
        try:
            ensure_recent_activities_table(conn)
            cur.execute("""
                SELECT activity_text, created_at
                FROM recent_activities
                ORDER BY created_at DESC
                LIMIT 10;
            """)
            rows = cur.fetchall()
            for r in rows:
                activity_text = r['activity_text']
                created_at = r['created_at']
                icon = "📌"
                if 'added' in activity_text.lower() or 'new product' in activity_text.lower():
                    icon = "📦"
                elif 'reorder' in activity_text.lower() or 'auto-reorder' in activity_text.lower():
                    icon = "🔁"
                elif 'expiry' in activity_text.lower():
                    icon = "⚠️"
                elif 'recommend' in activity_text.lower() or 'ai' in activity_text.lower():
                    icon = "💡"
                recent_activities.append({
                    "icon": icon,
                    "message": activity_text,
                    "time": created_at
                })
        except Exception:
            # fallback to static messages if anything goes wrong
            recent_activities = [
                {"icon": "📦", "message": "New product added — Organic Sugar", "time": None},
                {"icon": "🔁", "message": "Auto-reorder triggered for Rice Pack", "time": None},
                {"icon": "💡", "message": "AI recommends restocking Cooking Oil", "time": None},
                {"icon": "⚠️", "message": "5 products nearing expiry this week", "time": None},
            ]

        cur.close()

        return render_template(
            'dashboard.html',
            total_products=total_products,
            expiring_soon=expiring_soon,
            low_stock=low_stock,
            total_revenue=total_revenue,
            recent_activities=recent_activities
        )

    except Exception as e:
        try:
            conn = current_app.db
            conn.rollback()   # 🔥 FIX: reset bad transaction
        except:
            pass
        flash(f"⚠️ Error loading dashboard: {e}", "danger")
        return render_template('dashboard.html')

# 💡 RECOMMENDATIONS
@main.route("/dashboard/recommendations")
def recommendations():
    # redirect to the new blueprint route
    return redirect(url_for("recommendations_bp.recommendations_home"))

@main.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out successfully!", "info")
    return redirect(url_for('auth.login'))


@main.route('/order-report/<int:order_id>')
def order_report(order_id):
    return f"Report for Auto-Order ID: {order_id}"
