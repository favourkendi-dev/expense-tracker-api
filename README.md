# Expense Tracker API

A session-authenticated Flask + SQLAlchemy + Marshmallow REST API for tracking personal expenses. Built to integrate with the provided `client-with-sessions` React frontend.

## Project Description

Users sign up, log in, and manage their own list of expenses (title, amount, category, date). All expense data is strictly scoped to the logged-in user — no user can view, edit, or delete another user's expenses, enforced at the database query level on every route.

Authentication is **session-based**: on login, Flask stores the user's id in a signed session cookie; the React dev server proxies API requests so the cookie is set and sent automatically, with no extra CORS configuration needed.

## Tech Stack

- Python 3.10
- Flask 2.2.2 / Flask-SQLAlchemy 3.0.3 / Flask-Migrate 4.0.0
- Flask-Bcrypt 1.0.1 (password hashing)
- Marshmallow 3.20.1
- Faker 15.3.2 (seed data)
- SQLite

## Installation

1. Clone the repo and navigate to the backend:
```bash
   git clone <repo-url>
   cd <repo>
```

2. Install dependencies (Pipenv, pinned to Python 3.10 for compatibility with the required Flask/Werkzeug versions):
```bash
   pipenv install
   pipenv install pytest --dev
```

3. Activate the environment:
```bash
   pipenv shell
```

4. Run migrations:
```bash
   export FLASK_APP=app.py
   flask db upgrade head
```

5. Seed the database:
```bash
   python seed.py
```
   This creates a `favour` user (`password: demo123`) plus a few Faker-generated users, each with several expenses.

## Running the Server

```bash
python run.py
```

The API runs at `http://127.0.0.1:5555` — this exact port is required, since the frontend's `package.json` proxies requests here.

### Connecting the frontend

From the `client-with-sessions` folder:
```bash
npm install
npm start
```
The React app runs on port 3000 and proxies API calls to port 5555 automatically.

## Running Tests

```bash
pytest -v
```

19 tests covering signup/login/logout/session checks, full expense CRUD, schema validation, pagination, and — critically — **ownership isolation** (explicit tests proving one user cannot view, update, or delete another user's expenses).

## Authentication Flow

| Route | Method | Body | Response |
|-------|--------|------|----------|
| `/signup` | POST | `{ username, password, password_confirmation }` | `201` + user object, or `422` + `{ errors: [...] }` |
| `/login` | POST | `{ username, password }` | `200` + user object, or `401` + `{ errors: [...] }` |
| `/check_session` | GET | — | `200` + user object if logged in, else `401` |
| `/logout` | DELETE | — | `204` |

Passwords are never stored in plaintext — `User.password_hash` is a write-only property that hashes via bcrypt on assignment; the raw hash cannot be read back out via the model.

## Expense Endpoints

All routes below require an active session (`401` returned otherwise) and only ever operate on the logged-in user's own expenses.

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/expenses?page=1&per_page=10` | Paginated list of the current user's expenses |
| POST | `/expenses` | Create an expense (`title`, `amount`, `category`, `date`) |
| GET | `/expenses/<id>` | Get a single expense (`404` if it doesn't exist or belongs to another user) |
| PATCH | `/expenses/<id>` | Update any subset of `title`, `amount`, `category`, `date` |
| DELETE | `/expenses/<id>` | Delete an expense |

### Example: creating an expense

```bash
curl -b cookies.txt -X POST http://127.0.0.1:5555/expenses \
  -H "Content-Type: application/json" \
  -d '{"title": "Groceries", "amount": 45.50, "category": "food", "date": "2026-07-01"}'
```

### Example: paginated list

```bash
curl -b cookies.txt "http://127.0.0.1:5555/expenses?page=2&per_page=5"
```
Response includes `expenses`, `page`, `per_page`, `total`, and `total_pages`.

## Validations

**Table constraints:**
- `users.username` is unique
- `expenses.amount > 0` (SQLite `CHECK` constraint)

**Model validations (`@validates`):**
- `User.username` cannot be empty
- `Expense.title` cannot be empty
- `Expense.amount` must be positive

**Schema validations (Marshmallow):**
- `Expense.category` must be one of a fixed set of allowed values
- `Expense.amount` must be within a valid positive range
- `Expense.date` is parsed from an ISO date string (`"2026-07-01"`) into a real `date` object before it ever reaches the database — solves a real `TypeError` encountered during development, where SQLite's `Date` column rejected raw strings

## Security Notes

- Every expense query is filtered by `user_id=current_user.id` at the database level — never fetched by id alone and checked afterward. This is what makes cross-user data leakage structurally impossible rather than just "handled" in application logic.
- Session cookies are signed using `SECRET_KEY` (hardcoded for this dev/lab context; would move to an environment variable in production).