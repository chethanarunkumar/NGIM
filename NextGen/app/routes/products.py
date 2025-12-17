from flask import Blueprint, render_template, current_app, jsonify, request, flash, redirect, url_for
import psycopg2.extras
from datetime import datetime
from app.routes.main import log_activity

products = Blueprint("products", __name__, url_prefix="/dashboard/products")

# ---------------------------------------------------
# PRODUCT DASHBOARD
# ---------------------------------------------------
@products.route("/")
def dashboard():
    try:
        conn = current_app.db
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Total products
        cur.execute("SELECT COUNT(*) FROM products;")
        total_products = cur.fetchone()["count"]

        # Global minimum stock level
        cur.execute("SELECT min_stock_level FROM auto_order_settings LIMIT 1;")
        row = cur.fetchone()
        global_min_stock = int(row["min_stock_level"]) if row else 40

        # Low stock
        cur.execute("""
            SELECT COUNT(*) FROM products
            WHERE stock_qty < %s;
        """, (global_min_stock,))
        low_stock = cur.fetchone()["count"]

        # Expiring soon
        cur.execute("""
            SELECT COUNT(*) FROM products
            WHERE expiry_date <= CURRENT_DATE + INTERVAL '7 days';
        """)
        expiring_soon = cur.fetchone()["count"]

        # Total revenue
        cur.execute("SELECT SUM(total_amount) AS revenue FROM sales;")
        total_revenue = cur.fetchone()["revenue"] or 0

        # Top selling products
        cur.execute("""
            SELECT p.name AS product_name,
                   SUM(s.qty_sold) AS units_sold,
                   SUM(s.total_amount) AS revenue
            FROM sales s
            JOIN products p ON s.product_id = p.id
            GROUP BY p.name
            ORDER BY revenue DESC
            LIMIT 5;
        """)
        top_products = cur.fetchall()

        # Suppliers
        cur.execute("SELECT id, name FROM suppliers ORDER BY name;")
        suppliers = cur.fetchall()

        # ✅ PRODUCTS FOR INCREASE STOCK DROPDOWN
        cur.execute("SELECT id, name FROM products ORDER BY name;")
        products_list = cur.fetchall()

        cur.close()

        return render_template(
            "product/product_dashboard.html",
            total_products=total_products,
            expiring_soon=expiring_soon,
            low_stock=low_stock,
            total_revenue=total_revenue,
            top_products=top_products,
            suppliers=suppliers,
            products=products_list
        )

    except Exception as e:
        flash(f"⚠️ Error loading dashboard: {e}", "danger")
        return render_template(
            "product/product_dashboard.html",
            total_products=0,
            expiring_soon=0,
            low_stock=0,
            total_revenue=0,
            top_products=[],
            suppliers=[],
            products=[]
        )

# ---------------------------------------------------
# GET PRODUCT DETAILS (Increase Stock Modal)
# ---------------------------------------------------
@products.route("/get/<int:pid>")
def get_product(pid):
    conn = current_app.db
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT id,
               name AS product_name,
               stock_qty AS stock,
               expiry_date
        FROM products
        WHERE id = %s
    """, (pid,))

    product = cur.fetchone()
    cur.close()

    if product and product.get("expiry_date"):
        product["expiry_date"] = product["expiry_date"].strftime("%Y-%m-%d")

    return jsonify(product)

# ---------------------------------------------------
# INCREASE STOCK + OPTIONAL EXPIRY UPDATE
# ---------------------------------------------------
@products.route("/increase-stock", methods=["POST"])
def increase_stock():
    data = request.get_json()
    pid = int(data["product_id"])
    qty = int(data["qty"])
    expiry = data.get("expiry_date")

    conn = current_app.db
    cur = conn.cursor()

    if expiry:
        cur.execute("""
            UPDATE products
            SET stock_qty = stock_qty + %s,
                expiry_date = %s
            WHERE id = %s
        """, (qty, expiry, pid))
    else:
        cur.execute("""
            UPDATE products
            SET stock_qty = stock_qty + %s
            WHERE id = %s
        """, (qty, pid))

    conn.commit()
    cur.close()

    log_activity(conn, f"Stock increased for product ID {pid}")
    return jsonify({"status": "success"})

# ---------------------------------------------------
# ADD CATEGORY (UI helper only)
# ---------------------------------------------------
@products.route("/add-category", methods=["POST"])
def add_category():
    data = request.get_json()
    name = data.get("name")

    if not name:
        return jsonify({"error": "Category required"}), 400

    # No DB insert here.
    # Category will be saved when product is added.
    return jsonify({"message": "ok"})

@products.route("/categories")
def get_categories():
    conn = current_app.db
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT DISTINCT category
        FROM products
        WHERE category IS NOT NULL
        ORDER BY category;
    """)

    categories = [row["category"] for row in cur.fetchall()]
    cur.close()

    return jsonify(categories)

# ---------------------------------------------------
# VIEW ALL PRODUCTS
# ---------------------------------------------------
@products.route("/view")
def view_products():
    conn = current_app.db
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    search = request.args.get("search", "").lower()

    sql = """
        SELECT 
            p.id,
            p.name,
            p.category,
            p.stock_qty,
            s.name AS supplier,
            p.selling_price,
            p.updated_at
        FROM products p
        LEFT JOIN suppliers s ON p.supplier_id = s.id
    """

    if search:
        sql += " WHERE LOWER(p.name) LIKE %s ORDER BY p.id;"
        cur.execute(sql, (f"%{search}%",))
    else:
        sql += " ORDER BY p.id;"
        cur.execute(sql)

    products_list = cur.fetchall()
    cur.close()

    return render_template(
        "product/view_products.html",
        products=products_list,
        search=search
    )


# ---------------------------------------------------
# ADD PRODUCT
# ---------------------------------------------------
@products.route("/add", methods=["POST"])
def add_product():
    name = request.form.get("product_name")
    category = request.form.get("category")
    selling_price = float(request.form.get("selling_price") or 0)
    stock = int(request.form.get("stock") or 0)
    expiry = request.form.get("expiry_date") or None
    supplier_id = request.form.get("supplier_id") or None

    conn = current_app.db
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        INSERT INTO products
            (name, category, stock_qty, selling_price, supplier_id, expiry_date)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id;
    """, (name, category, stock, selling_price, supplier_id, expiry))

    pid = cur.fetchone()["id"]
    conn.commit()
    cur.close()

    log_activity(conn, f"New product added — {name}")
    flash("✅ Product added successfully!", "success")
    return redirect(url_for("products.view_products"))



# ---------------------------------------------------
# REMOVE PRODUCT
# ---------------------------------------------------
@products.route("/remove/<int:product_id>")
def remove_product(product_id):
    conn = current_app.db
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id=%s;", (product_id,))
    conn.commit()
    cur.close()

    log_activity(conn, f"Product removed — ID {product_id}")
    flash("🗑️ Product removed!", "info")
    return redirect(url_for("products.view_products"))


# ---------------------------------------------------
# ADD SUPPLIER (AJAX)
# ---------------------------------------------------
@products.route("/add_supplier", methods=["POST"])
def add_supplier():
    data = request.get_json() or {}

    manual_id = data.get("supplier_id")
    name = data.get("name")
    contact = data.get("contact")
    address = data.get("address")
    lead = data.get("lead_time")

    if not name:
        return jsonify({"error": "Supplier name required"}), 400

    try:
        conn = current_app.db
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        if manual_id:
            try:
                mid = int(manual_id)
            except:
                mid = manual_id

            cur.execute("""
                INSERT INTO suppliers (id, name, contact, address, lead_time)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
            """, (mid, name, contact, address, lead))
        else:
            cur.execute("""
                INSERT INTO suppliers (name, contact, address, lead_time)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
            """, (name, contact, address, lead))

        new_id = cur.fetchone()["id"]
        conn.commit()

        log_activity(conn, f"Supplier added — {name}")

        return jsonify({"message": "Supplier added", "id": new_id})

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

# -----------------------------------------------------------
# BILLING SYSTEM
# -----------------------------------------------------------
@products.route("/billing")
def billing_page():
    try:
        conn = current_app.db
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("SELECT id, name, selling_price, stock_qty FROM products ORDER BY name;")
        products_list = cur.fetchall()
        cur.close()

        return render_template("product/billing.html", products=products_list)

    except Exception as e:
        return render_template("product/billing.html", products=[])

@products.route("/billing/search")
def billing_search():
    q = request.args.get("q", "").strip()
    conn = current_app.db
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        if q.isdigit():
            cur.execute("""
                SELECT id, name, selling_price, stock_qty 
                FROM products 
                WHERE id = %s
            """, (int(q),))
        else:
            cur.execute("""
                SELECT id, name, selling_price, stock_qty
                FROM products 
                WHERE LOWER(name) LIKE %s
            """, (f"%{q.lower()}%",))

        rows = cur.fetchall()
        return jsonify(rows)

    except Exception:
        return jsonify([])

    finally:
        cur.close()

@products.route("/billing/checkout", methods=["POST"])
def billing_checkout():
    from datetime import datetime

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "missing payload"}), 400

    items = data.get("items", [])
    biller_id = data.get("biller_id", 1)

    if not items:
        return jsonify({"error": "no items"}), 400

    conn = current_app.db
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        today = datetime.now().strftime("%Y%m%d")
        like_pattern = f"BILL-{today}-%"

        cur.execute("""
            SELECT bill_no 
            FROM sales 
            WHERE bill_no LIKE %s 
            ORDER BY id DESC 
            LIMIT 1
        """, (like_pattern,))

        row = cur.fetchone()

        if row and row.get("bill_no"):
            try:
                last_num = int(row["bill_no"].split("-")[-1])
                next_seq = last_num + 1
            except:
                next_seq = 1
        else:
            next_seq = 1

        bill_no = f"BILL-{today}-{next_seq:04d}"

        sale_ids = []
        normalized_items = []

        for it in items:
            pid = int(it.get("product_id"))
            qty = int(it.get("qty", 0))
            unit_price = float(it.get("unit_price", 0))

            if qty <= 0:
                return jsonify({"error": f"Invalid qty for product {pid}"}), 400

            normalized_items.append({
                "product_id": pid,
                "qty": qty,
                "unit_price": unit_price,
                "batch_id": it.get("batch_id")
            })

        for it in normalized_items:
            cur.execute("SELECT stock_qty FROM products WHERE id=%s FOR UPDATE", (it["product_id"],))
            row = cur.fetchone()

            if not row:
                raise Exception(f"Product {it['product_id']} not found")

            available = row["stock_qty"] or 0
            if it["qty"] > available:
                raise Exception(f"Insufficient stock for product {it['product_id']}")

            if it["batch_id"]:
                cur.execute("SELECT batch_qty FROM batches WHERE id=%s FOR_UPDATE", (it["batch_id"],))
                b = cur.fetchone()
                if not b or it["qty"] > (b["batch_qty"] or 0):
                    raise Exception(f"Insufficient batch qty {it['batch_id']}")

        for it in normalized_items:
            total = it["qty"] * it["unit_price"]

            cur.execute("""
                INSERT INTO sales 
                    (product_id, batch_id, qty_sold, sale_date, total_amount, biller_id, bill_no)
                VALUES 
                    (%s, %s, %s, CURRENT_TIMESTAMP, %s, %s, %s)
                RETURNING id;
            """, (it["product_id"], it["batch_id"], it["qty"], total, biller_id, bill_no))

            sid = cur.fetchone()["id"]
            sale_ids.append(sid)

            cur.execute("UPDATE products SET stock_qty = stock_qty - %s WHERE id = %s",
                        (it["qty"], it["product_id"]))

            if it["batch_id"]:
                cur.execute("UPDATE batches SET batch_qty = batch_qty - %s WHERE id = %s",
                            (it["qty"], it["batch_id"]))

        # 🚫 REMOVED: BILL LOG ENTRY
        # No bill logs will appear in recent_activities now.

        conn.commit()
        return jsonify({"message": "success", "bill_no": bill_no, "sale_ids": sale_ids})

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cur.close()

# -----------------------------------------------------------
# BILL HISTORY
# -----------------------------------------------------------
@products.route("/billing/history")
def billing_history():
    try:
        conn = current_app.db
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT
                bill_no,
                MIN(sale_date) AS created_at,
                SUM(total_amount) AS net_amount,
                COUNT(*) AS item_count
            FROM sales
            WHERE bill_no IS NOT NULL
            GROUP BY bill_no
            ORDER BY created_at DESC
            LIMIT 50;
        """)
        rows = cur.fetchall()
        cur.close()
        for r in rows:
            if r.get("created_at") is not None:
                r["created_at"] = r["created_at"].isoformat()
        return jsonify(rows)
    except:
        return jsonify([]), 500

@products.route("/billing/print/<string:bill_no>")
def billing_print(bill_no):
    try:
        conn = current_app.db
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT 
                p.name AS product_name,
                s.qty_sold,
                s.total_amount,
                s.sale_date,
                COALESCE(s.biller_id, 1) AS biller_id
            FROM sales s
            LEFT JOIN products p ON s.product_id = p.id
            WHERE s.bill_no = %s
            ORDER BY s.id;
        """, (bill_no,))

        items = cur.fetchall()
        cur.close()

        if not items:
            return "Bill not found", 404

        total = sum(float(i["total_amount"]) for i in items)

        return render_template(
            "product/bill_print.html",
            bill_no=bill_no,
            items=items,
            total=total
        )

    except Exception as e:
        return f"Error: {e}", 500


@products.route("/billing/pdf/<string:bill_no>")
def billing_pdf(bill_no):
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from flask import make_response
        import io
        import psycopg2.extras

        conn = current_app.db
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT 
                s.product_id,
                p.name AS product_name,
                s.qty_sold,
                s.total_amount,
                s.sale_date,
                s.biller_id
            FROM sales s
            LEFT JOIN products p ON s.product_id = p.id
            WHERE s.bill_no = %s
            ORDER BY s.id;
        """, (bill_no,))
        items = cur.fetchall()
        cur.close()

        if not items:
            return "Bill not found", 404

        # -----------------------------
        # CALCULATIONS
        # -----------------------------
        total = sum(float(i["total_amount"]) for i in items)
        gst = round(total * 0.18, 2)
        grand_total = round(total + gst, 2)

        # -----------------------------
        # PDF SETUP
        # -----------------------------
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)

        x_left = 20 * mm
        y = 280 * mm

        # -----------------------------
        # HEADER
        # -----------------------------
        pdf.setFont("Helvetica-Bold", 22)
        pdf.drawString(x_left, y, "NXT GEN Inventory")

        pdf.setFont("Helvetica", 11)
        y -= 10 * mm
        pdf.drawString(x_left, y, "Bengaluru – 560003")
        y -= 6 * mm
        pdf.drawString(x_left, y, "Phone: +91 3121030103")
        y -= 6 * mm
        pdf.drawString(x_left, y, "GSTIN: 29CYCM2314CT17")

        y -= 8 * mm
        pdf.line(x_left, y, 190 * mm, y)
        y -= 10 * mm

        # -----------------------------
        # BILL INFO
        # -----------------------------
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(x_left, y, f"Bill No: {bill_no}")
        y -= 7 * mm

        pdf.drawString(x_left, y, f"Date: {items[0]['sale_date']}")
        y -= 7 * mm

        pdf.drawString(x_left, y, f"Biller ID: {items[0]['biller_id']}")
        y -= 10 * mm

        # -----------------------------
        # TABLE HEADER
        # -----------------------------
        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(x_left, y, "Product")
        pdf.drawString(100 * mm, y, "Qty")
        pdf.drawString(130 * mm, y, "Price")
        pdf.drawString(160 * mm, y, "Total")

        y -= 6 * mm
        pdf.line(x_left, y, 190 * mm, y)
        y -= 8 * mm

        # -----------------------------
        # TABLE ROWS
        # -----------------------------
        pdf.setFont("Helvetica", 12)

        for it in items:
            price_per_unit = float(it["total_amount"]) / int(it["qty_sold"])

            pdf.drawString(x_left, y, it["product_name"])
            pdf.drawString(100 * mm, y, str(it["qty_sold"]))
            pdf.drawString(130 * mm, y, f"Rs. {price_per_unit:.2f}")
            pdf.drawString(160 * mm, y, f"Rs. {it['total_amount']:.2f}")

            y -= 7 * mm

        # -----------------------------
        # TOTALS
        # -----------------------------
        y -= 5 * mm
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(x_left, y, f"Subtotal: Rs. {total:.2f}")
        y -= 7 * mm

        pdf.drawString(x_left, y, f"GST (18%): Rs. {gst:.2f}")
        y -= 7 * mm

        pdf.drawString(x_left, y, f"Grand Total: Rs. {grand_total:.2f}")
        y -= 15 * mm

        # -----------------------------
        # FOOTER
        # -----------------------------
        pdf.setFont("Helvetica-Oblique", 12)
        pdf.drawString(x_left, y, "Thank you for shopping with NXT GEN Inventory!")

        pdf.showPage()
        pdf.save()

        buffer.seek(0)
        response = make_response(buffer.read())
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = f"attachment; filename={bill_no}.pdf"

        return response

    except Exception as e:
        return f"PDF Error: {e}", 500
