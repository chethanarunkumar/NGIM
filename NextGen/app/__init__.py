from flask import Flask
import psycopg2
import psycopg2.extras
from app.config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    # ---------------------------------------
    # 📌 Connect to PostgreSQL
    # ---------------------------------------
    try:
        conn = psycopg2.connect(
            dbname=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        app.db = conn
        print("✅ PostgreSQL Database Connected Successfully!")
    except Exception as e:
        print(f"❌ Database Connection Error: {e}")

    # ---------------------------------------
    # 📌 Register Blueprints
    # ---------------------------------------
    from app.routes.main import main
    from app.routes.products import products
    from app.routes.auto_order import auto_order_bp
    from app.routes.alerts import alerts_bp
    from app.routes.analytics import analytics_bp 
    from app.routes.auth import auth
    from app.routes.recommendations import recommendations_bp

    app.register_blueprint(recommendations_bp)
    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(products)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(auto_order_bp)
    app.register_blueprint(analytics_bp)  

    return app
