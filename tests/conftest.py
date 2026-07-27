
import pytest

from app import create_app
from models import db


@pytest.fixture
def app():
    app = create_app()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def signup(client, username="trainer1", password="secret123"):
    return client.post(
        "/signup",
        json={
            "username": username,
            "password": password,
            "password_confirmation": password,
        },
    )