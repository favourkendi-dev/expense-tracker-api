
import json


def signup(client, username="trainer1", password="secret123"):
    return client.post(
        "/signup",
        json={"username": username, "password": password, "password_confirmation": password},
    )


def login(client, username="trainer1", password="secret123"):
    return client.post("/login", json={"username": username, "password": password})


#  Auth

def test_signup_success(client):
    response = signup(client)
    assert response.status_code == 201
    assert response.get_json()["username"] == "trainer1"


def test_signup_password_mismatch(client):
    response = client.post(
        "/signup",
        json={"username": "x", "password": "abc", "password_confirmation": "xyz"},
    )
    assert response.status_code == 422
    assert "errors" in response.get_json()


def test_signup_duplicate_username(client):
    signup(client, username="dupe")
    response = signup(client, username="dupe")
    assert response.status_code == 422


def test_login_success(client):
    signup(client)
    response = login(client)
    assert response.status_code == 200
    assert response.get_json()["username"] == "trainer1"


def test_login_wrong_password(client):
    signup(client)
    response = login(client, password="wrongpassword")
    assert response.status_code == 401


def test_check_session_when_logged_in(client):
    signup(client)
    response = client.get("/check_session")
    assert response.status_code == 200


def test_check_session_when_logged_out(client):
    response = client.get("/check_session")
    assert response.status_code == 401


def test_logout_clears_session(client):
    signup(client)
    client.delete("/logout")
    response = client.get("/check_session")
    assert response.status_code == 401


def test_create_expense_requires_login(client):
    response = client.post(
        "/expenses",
        json={"title": "Coffee", "amount": 4.5, "category": "food", "date": "2026-07-01"},
    )
    assert response.status_code == 401


def test_create_expense_success(client):
    signup(client)
    response = client.post(
        "/expenses",
        json={"title": "Coffee", "amount": 4.5, "category": "food", "date": "2026-07-01"},
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["title"] == "Coffee"
    assert data["amount"] == 4.5


def test_create_expense_invalid_category(client):
    signup(client)
    response = client.post(
        "/expenses",
        json={"title": "Mystery", "amount": 10, "category": "not_real", "date": "2026-07-01"},
    )
    assert response.status_code == 422
    assert "category" in response.get_json()["errors"]


def test_create_expense_negative_amount(client):
    signup(client)
    response = client.post(
        "/expenses",
        json={"title": "Refund?", "amount": -5, "category": "food", "date": "2026-07-01"},
    )
    assert response.status_code == 422


def test_get_expense_by_id(client):
    signup(client)
    create_response = client.post(
        "/expenses",
        json={"title": "Coffee", "amount": 4.5, "category": "food", "date": "2026-07-01"},
    )
    expense_id = create_response.get_json()["id"]

    response = client.get(f"/expenses/{expense_id}")
    assert response.status_code == 200
    assert response.get_json()["title"] == "Coffee"


def test_update_expense(client):
    signup(client)
    create_response = client.post(
        "/expenses",
        json={"title": "Coffee", "amount": 4.5, "category": "food", "date": "2026-07-01"},
    )
    expense_id = create_response.get_json()["id"]

    response = client.patch(f"/expenses/{expense_id}", json={"amount": 5.0})
    assert response.status_code == 200
    assert response.get_json()["amount"] == 5.0


def test_delete_expense(client):
    signup(client)
    create_response = client.post(
        "/expenses",
        json={"title": "Coffee", "amount": 4.5, "category": "food", "date": "2026-07-01"},
    )
    expense_id = create_response.get_json()["id"]

    response = client.delete(f"/expenses/{expense_id}")
    assert response.status_code == 204

    get_response = client.get(f"/expenses/{expense_id}")
    assert get_response.status_code == 404


# ownership isolation

def test_user_cannot_view_another_users_expense(client):
    signup(client, username="alice", password="pass1")
    create_response = client.post(
        "/expenses",
        json={"title": "Alice's Rent", "amount": 1000, "category": "housing", "date": "2026-07-01"},
    )
    expense_id = create_response.get_json()["id"]
    client.delete("/logout")

    signup(client, username="bob", password="pass2")
    response = client.get(f"/expenses/{expense_id}")
    assert response.status_code == 404


def test_user_cannot_delete_another_users_expense(client):
    signup(client, username="alice", password="pass1")
    create_response = client.post(
        "/expenses",
        json={"title": "Alice's Rent", "amount": 1000, "category": "housing", "date": "2026-07-01"},
    )
    expense_id = create_response.get_json()["id"]
    client.delete("/logout")

    signup(client, username="bob", password="pass2")
    response = client.delete(f"/expenses/{expense_id}")
    assert response.status_code == 404


def test_index_only_shows_own_expenses(client):
    signup(client, username="alice", password="pass1")
    client.post(
        "/expenses",
        json={"title": "Alice's Coffee", "amount": 4.5, "category": "food", "date": "2026-07-01"},
    )
    client.delete("/logout")

    signup(client, username="bob", password="pass2")
    client.post(
        "/expenses",
        json={"title": "Bob's Lunch", "amount": 12.0, "category": "food", "date": "2026-07-01"},
    )

    response = client.get("/expenses")
    data = response.get_json()
    assert data["total"] == 1
    assert data["expenses"][0]["title"] == "Bob's Lunch"


#Pagination

def test_pagination(client):
    signup(client)
    for i in range(15):
        client.post(
            "/expenses",
            json={"title": f"Item {i}", "amount": 1.0, "category": "other", "date": "2026-07-01"},
        )

    response = client.get("/expenses?page=1&per_page=10")
    data = response.get_json()
    assert len(data["expenses"]) == 10
    assert data["total"] == 15
    assert data["total_pages"] == 2

    response_page_2 = client.get("/expenses?page=2&per_page=10")
    assert len(response_page_2.get_json()["expenses"]) == 5