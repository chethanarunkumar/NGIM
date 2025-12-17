from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")

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
