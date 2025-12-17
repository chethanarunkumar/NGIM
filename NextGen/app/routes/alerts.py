from flask import Blueprint, render_template, current_app, jsonify
import psycopg2.extras
from datetime import datetime

alerts_bp = Blueprint("alerts_bp", __name__, url_prefix="/alerts")


# --------------------------------------------------------
# AUTO-GENERATE EXPIRY ALERTS (Next 30 Days ONLY)
# --------------------------------------------------------
def generate_auto_alerts():
    conn = current_app.db
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # 1️⃣ Remove old expiry alerts
    cur.execute("""
        DELETE FROM alerts
        WHERE alert_type = 'Expiry';
    """)

    # 2️⃣ Insert fresh alerts (next 30 days only)
    cur.execute("""
        INSERT INTO alerts (product_id, alert_type, message, status, sent_date)
        SELECT
            p.id,
            'Expiry',
            CONCAT(p.name, ' is expiring on ', p.expiry_date),
            'Active',
            NOW()
        FROM products p
        WHERE p.expiry_date IS NOT NULL
          AND p.expiry_date > CURRENT_DATE
          AND p.expiry_date <= CURRENT_DATE + INTERVAL '30 days';
    """)

    conn.commit()
    cur.close()




# --------------------------------------------------------
# LOAD ALERTS PAGE
# --------------------------------------------------------
@alerts_bp.route("/")
def alerts_home():

    generate_auto_alerts()  # Auto-generate alerts

    conn = current_app.db
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT 
            a.id AS alert_id,
            a.product_id,
            p.name AS product_name,
            p.expiry_date,
            a.sent_date,
            a.status
        FROM alerts a
        JOIN products p ON p.id = a.product_id
        WHERE a.alert_type = 'Expiry'
        ORDER BY p.expiry_date ASC;
    """)

    alerts = cur.fetchall()

    counts = {
        "all": len(alerts),
        "resolved": sum(1 for a in alerts if a["status"].lower() == "resolved")
    }

    current_time = datetime.now()  # For days-left calculation

    return render_template(
        "alerts/alerts.html",
        alerts=alerts,
        counts=counts,
        current_time=current_time
    )



# --------------------------------------------------------
# RESOLVE ALERT
# --------------------------------------------------------
@alerts_bp.route("/resolve/<int:id>", methods=["POST"])
def resolve_alert(id):
    conn = current_app.db
    cur = conn.cursor()

    cur.execute("""
        UPDATE alerts
        SET status = 'Resolved'
        WHERE id = %s;
    """, (id,))

    conn.commit()
    return jsonify({"message": "Alert marked as resolved"})
