import os

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect


db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_name=None):
    app = Flask(__name__)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", f"sqlite:///{os.path.join(app.root_path, '..', 'cras.db')}"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.environ.get("UPLOAD_FOLDER", os.path.join(app.instance_path, "uploads")),
        ALLOWED_EXTENSIONS={"png", "jpg", "jpeg", "pdf", "bmp", "tiff"},
    )

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    from flask_wtf.csrf import CSRFError, generate_csrf

    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf)

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return (
            render_template("errors/csrf_error.html", reason=e.description),
            400,
        )

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    from . import routes  # noqa: F401  # Registers blueprints

    app.register_blueprint(routes.main_bp)
    app.register_blueprint(routes.auth_bp)
    app.register_blueprint(routes.admin_bp)

    return app
