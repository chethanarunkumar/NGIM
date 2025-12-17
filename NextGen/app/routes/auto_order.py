from flask import Blueprint, render_template, request, jsonify, current_app, abort
import psycopg2.extras
from datetime import datetime

auto_order_bp = Blueprint("auto_order_bp", __name__, url_prefix="/dashboard/reorder")


# =======================================================
# 📌 Ensure every product has a rule
# =======================================================
def ensure_rules_exist():
    conn = current_app.db
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT p.id, p.name 
        FROM products p
        LEFT JOIN product_rules pr ON pr.product_id = p.id
        WHERE pr.id IS NULL;
    """)
    missing = cur.fetchall()

    for item in missing:
        cur.execute("""
            INSERT INTO product_rules (product_id, reorder_quantity, is_enabled)
            VALUES (%s, 10, TRUE);
        """, (item["id"],))

    conn.commit()


# =======================================================
# ⭐ AUTO-ORDER ENGINE — Only when stock < threshold
# =======================================================
def run_auto_order_engine():
    conn = current_app.db
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Load global settings
    cur.execute("SELECT * FROM auto_order_settings LIMIT 1;")
    settings = cur.fetchone()
    min_stock = settings["min_stock_level"]

    # Load products + rules
    cur.execute("""
        SELECT 
            p.id AS product_id,
            p.name,
            p.stock_qty,
            p.supplier_id,
            s.name AS supplier_name,
            pr.reorder_quantity,
            pr.is_enabled
        FROM products p
        JOIN product_rules pr ON pr.product_id = p.id
        LEFT JOIN suppliers s ON s.id = p.supplier_id
        WHERE pr.is_enabled = TRUE;
    """)
    products = cur.fetchall()

    for p in products:

        # STEP 1 — Stock must be low
        if p["stock_qty"] is None or p["stock_qty"] > min_stock:
            continue

        # STEP 2 — Prevent duplicate auto orders
        cur.execute("""
            SELECT id FROM orders
            WHERE product_id = %s AND status = 'Pending' AND generated_by = 1
            LIMIT 1;
        """, (p["product_id"],))
        existing = cur.fetchone()

        if existing:
            continue  # Skip duplicate

        # STEP 3 — Create new auto-order
        qty = p["reorder_quantity"]

        cur.execute("""
            INSERT INTO orders (
                product_id, supplier_id, qty_ordered,
                order_date, status, generated_by, order_form_url
            )
            VALUES (%s, %s, %s, NOW(), 'Pending', 1, NULL)
        """, (
            p["product_id"],
            p["supplier_id"],
            qty
        ))

        print("AUTO ORDER GENERATED:", p["name"], "| Qty:", qty)

    conn.commit()


# =======================================================
# 📌 AUTO-ORDER PAGE
# =======================================================
@auto_order_bp.route("/", methods=["GET"])
def auto_order_page():
    conn = current_app.db
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    ensure_rules_exist()
    run_auto_order_engine()   # ⭐ Auto-generates orders safely

    # Load global settings
    cur.execute("SELECT * FROM auto_order_settings LIMIT 1;")
    settings = cur.fetchone()

    # Load product rules
    cur.execute("""
        SELECT 
            p.id AS product_id,
            p.name AS product_name,
            pr.id AS rule_id,
            COALESCE(pr.reorder_quantity, 10) AS reorder_quantity,
            COALESCE(pr.is_enabled, TRUE) AS is_enabled
        FROM products p
        LEFT JOIN product_rules pr ON p.id = pr.product_id
        ORDER BY p.id;
    """)
    rules = cur.fetchall()

    # Load activity (auto-generated orders only)
    cur.execute("""
        SELECT
            o.id,
            o.product_id,
            p.name AS product_name,
            o.supplier_id,
            s.name AS supplier_name,
            o.qty_ordered,
            o.order_date,
            o.status,
            o.order_form_url
        FROM orders o
        LEFT JOIN products p ON o.product_id = p.id
        LEFT JOIN suppliers s ON o.supplier_id = s.id
        WHERE o.generated_by = 1
        ORDER BY o.order_date DESC
        LIMIT 100;
    """)
    rows = cur.fetchall()

    activity = []
    for r in rows:
        od = r.get("order_date")

        if od:
            try:
                dt = datetime.fromisoformat(str(od))
                date_str = dt.strftime("%d %b")
                date_long = dt.strftime("%d %b %Y")
            except:
                date_str = str(od)
                date_long = str(od)
        else:
            date_str = "-"
            date_long = "-"

        activity.append({
            "id": r.get("id"),
            "date": date_str,
            "date_long": date_long,
            "product_id": r.get("product_id"),
            "product_name": r.get("product_name"),
            "supplier_id": r.get("supplier_id"),
            "supplier_name": r.get("supplier_name"),
            "qty": r.get("qty_ordered"),
            "status": r.get("status"),
            "order_form_url": r.get("order_form_url")
        })

    return render_template(
        "reorder/auto_reorder.html",
        settings=settings,
        rules=rules,
        activity=activity
    )


# =======================================================
# 📌 Toggle Global Settings
# =======================================================
@auto_order_bp.route("/toggle_global", methods=["POST"])
def toggle_global():
    data = request.get_json()
    conn = current_app.db
    cur = conn.cursor()

    cur.execute("""
        UPDATE auto_order_settings
        SET min_stock_level = %s,
            lead_time_days = %s,
            updated_at = NOW()
        WHERE id = 1;
    """, (data["min_stock_level"], data["lead_time_days"]))

    conn.commit()
    return jsonify({"message": "Updated"})


# =======================================================
# 📌 Toggle Product Rule
# =======================================================
@auto_order_bp.route("/toggle_rule/<int:rule_id>", methods=["POST"])
def toggle_rule(rule_id):
    conn = current_app.db
    cur = conn.cursor()

    cur.execute("""
        UPDATE product_rules
        SET is_enabled = NOT is_enabled
        WHERE id = %s;
    """, (rule_id,))

    conn.commit()
    return jsonify({"message": "Rule toggled"})


# =======================================================
# 📌 Update Reorder Quantity
# =======================================================
@auto_order_bp.route("/update_rule", methods=["POST"])
def update_rule():
    data = request.get_json()
    conn = current_app.db
    cur = conn.cursor()

    cur.execute("""
        UPDATE product_rules
        SET reorder_quantity = %s
        WHERE id = %s;
    """, (data["reorder_quantity"], data["rule_id"]))

    conn.commit()
    return jsonify({"message": "Quantity updated"})


# =======================================================
# 📌 Auto-Order Report
# =======================================================
@auto_order_bp.route("/report/<int:order_id>", methods=["GET"])
def order_report(order_id):
    conn = current_app.db
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT 
            o.id,
            o.product_id,
            p.name AS product_name,
            p.selling_price,   -- use selling_price
            o.supplier_id,
            s.name AS supplier_name,
            o.qty_ordered,
            o.order_date,
            o.status
        FROM orders o
        LEFT JOIN products p ON o.product_id = p.id
        LEFT JOIN suppliers s ON o.supplier_id = s.id
        WHERE o.id = %s;
    """, (order_id,))

    r = cur.fetchone()
    if not r:
        abort(404, description="Order report not found")

    # Format date
    try:
        dt = datetime.fromisoformat(str(r["order_date"]))
        date_long = dt.strftime("%d %b %Y %H:%M")
    except:
        date_long = str(r["order_date"])

    # Calculate total amount
    unit_price = float(r["selling_price"])
    quantity = int(r["qty_ordered"])
    total_amount = unit_price * quantity

    report = {
        "id": r["id"],
        "product_id": r["product_id"],
        "product_name": r["product_name"],
        "unit_price": unit_price,
        "quantity": quantity,
        "total_amount": total_amount,
        "supplier_id": r["supplier_id"],
        "supplier_name": r["supplier_name"],
        "status": r["status"],
        "date": date_long
    }

    return render_template("reorder/order_report.html", report=report)



