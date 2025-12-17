# ================================================================
# NGIM Recommendation Dashboard Route
# Connects Flask UI to ai_engine.py backend
# ================================================================

from flask import Blueprint, render_template, request, current_app

from app.ai_engine import (
    get_products,
    get_recommendation,
    get_top10_forecast
)

recommendations_bp = Blueprint(
    "recommendations_bp",
    __name__,
    url_prefix="/dashboard/recommendations"
)

@recommendations_bp.route("/", methods=["GET", "POST"])
def recommendations_home():

    # Load products for dropdown
    products = get_products().sort_values("product_name").reset_index(drop=True)

    result = None
    top10 = None   # NEW → Forecast Report for top 10 items

    if request.method == "POST":

        pid = request.form.get("product_id")
        forecast_month = request.form.get("forecast_month")
        stock = request.form.get("current_stock", 50)

        # Validate inputs
        try:
            pid = int(pid)
            stock = float(stock)
        except:
            return render_template(
                "recommendation/recommendation_dashboard.html",
                products=products,
                result={"error": "Invalid input values."},
                top10=None
            )

        # Call AI engine
        try:
            result = get_recommendation(pid, forecast_month, stock)

            # NEW: generate Top-10 Forecast Report
            top10 = get_top10_forecast(forecast_month)

        except Exception as e:
            current_app.logger.error(f"[AI ERROR] {e}")
            return render_template(
                "recommendation/recommendation_dashboard.html",
                products=products,
                result={"error": "AI Engine failed. Check logs."},
                top10=None
            )

        current_app.logger.info(
            f"[AI] Recommendation generated for PID={pid} Month={forecast_month}"
        )

    # Render dashboard
    return render_template(
        "recommendation/recommendation_dashboard.html",
        products=products,
        result=result,
        top10=top10  # NEW → send report to UI
    )
