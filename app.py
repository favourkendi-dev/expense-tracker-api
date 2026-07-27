from flask import Flask
from flask_migrate import Migrate

from models import db, bcrypt

migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Secret key for flask session cookies to be signed and secure
    app.config["SECRET_KEY"] = "dev-secret-key-change-in-production"

    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    from routes import register_routes
    register_routes(app)

    return app