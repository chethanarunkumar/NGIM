from flask import Blueprint, render_template, current_app
import psycopg2.extras

analytics_bp = Blueprint("analytics_bp", __name__, url_prefix="/analytics")

@analytics_bp.route("/")
def analytics_dashboard():
    conn = current_app.db
    # use RealDictCursor for convenience
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # 1) Revenue + Profit (from sales) - unchanged logic but safe casting
    cur.execute("""
        SELECT
            DATE_TRUNC('month', sale_date) AS month_dt,
            TO_CHAR(DATE_TRUNC('month', sale_date), 'Mon') AS month_label,
            SUM(total_amount) AS revenue,
            SUM(total_amount * 0.20) AS profit
        FROM sales
        GROUP BY month_dt
        ORDER BY month_dt;
    """)
    raw_rp = cur.fetchall()
    revenue_profit = [
        [ row["month_label"], float(row["revenue"] or 0), float(row["profit"] or 0) ]
        for row in raw_rp
    ]

    # 2) Category sales — include categories with zero sales
    #    Left join products -> sales so categories present in products show up even if no sales
    cur.execute("""
        SELECT
            p.category AS category,
            COALESCE(SUM(s.qty_sold), 0) AS total_qty
        FROM products p
        LEFT JOIN sales s ON s.product_id = p.id
        GROUP BY p.category
        ORDER BY total_qty DESC NULLS LAST, p.category;
    """)
    raw_cat = cur.fetchall()
    category_sales = [
        [ row["category"], int(row["total_qty"] or 0) ]
        for row in raw_cat
    ]

    # 3) Per-product totals (so you can display a product list + sales counts; includes zero)
    cur.execute("""
        SELECT
            p.id,
            p.name,
            p.category,
            COALESCE(SUM(s.qty_sold), 0) AS total_qty,
            p.stock_qty
        FROM products p
        LEFT JOIN sales s ON s.product_id = p.id
        GROUP BY p.id, p.name, p.category, p.stock_qty
        ORDER BY total_qty DESC, p.name;
    """)
    raw_prod = cur.fetchall()
    product_sales = [
        {
            "id": row["id"],
            "name": row["name"],
            "category": row["category"],
            "total_qty": int(row["total_qty"] or 0),
            "stock_qty": int(row["stock_qty"] or 0)
        }
        for row in raw_prod
    ]

    cur.close()

    # debug prints (optional)
    print("DEBUG RP:", revenue_profit)
    print("DEBUG CAT:", category_sales[:10])
    print("DEBUG PROD sample:", product_sales[:5])

    return render_template(
        "analytics/analytics_dashboard.html",
        revenue_profit=revenue_profit,
        category_sales=category_sales,
        product_sales=product_sales
    )
