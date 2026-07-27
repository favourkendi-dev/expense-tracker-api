
from flask import request, session, jsonify
from marshmallow import ValidationError, EXCLUDE

from models import db, User, Expense
from schemas import ExpenseSchema, ExpenseUpdateSchema

expense_schema = ExpenseSchema()
expenses_schema = ExpenseSchema(many=True)
expense_update_schema = ExpenseUpdateSchema()


def get_current_user():
    user_id = session.get("user_id")
    if user_id:
        return User.query.get(user_id)
    return None


def register_routes(app):

    # Auth

    @app.route("/signup", methods=["POST"])
    def signup():
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        password_confirmation = data.get("password_confirmation")

        errors = []
        if not username:
            errors.append("Username is required.")
        if not password:
            errors.append("Password is required.")
        if password != password_confirmation:
            errors.append("Password and confirmation do not match.")
        if username and User.query.filter_by(username=username).first():
            errors.append("Username is already taken.")

        if errors:
            return jsonify({"errors": errors}), 422

        user = User(username=username)
        user.password_hash = password  # triggers bcrypt hashing via the setter

        try:
            db.session.add(user)
            db.session.commit()
        except ValueError as e:
            db.session.rollback()
            return jsonify({"errors": [str(e)]}), 422

        session["user_id"] = user.id
        return jsonify({"id": user.id, "username": user.username}), 201

    @app.route("/login", methods=["POST"])
    def login():
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        user = User.query.filter_by(username=username).first()

        if user and user.authenticate(password):
            session["user_id"] = user.id
            return jsonify({"id": user.id, "username": user.username}), 200

        return jsonify({"errors": ["Invalid username or password."]}), 401

    @app.route("/check_session", methods=["GET"])
    def check_session():
        user_id = session.get("user_id")
        if user_id:
            user = User.query.get(user_id)
            if user:
                return jsonify({"id": user.id, "username": user.username}), 200
        return jsonify({"errors": ["Not authorized."]}), 401

    @app.route("/logout", methods=["DELETE"])
    def logout():
        session.pop("user_id", None)
        return "", 204

    # Expenses

    @app.route("/expenses", methods=["GET"])
    def get_expenses():
        user = get_current_user()
        if user is None:
            return jsonify({"errors": ["Not authorized."]}), 401

        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        pagination = Expense.query.filter_by(user_id=user.id).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            "expenses": expenses_schema.dump(pagination.items),
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "total_pages": pagination.pages,
        }), 200

    @app.route("/expenses", methods=["POST"])
    def create_expense():
        user = get_current_user()
        if user is None:
            return jsonify({"errors": ["Not authorized."]}), 401

        json_data = request.get_json(silent=True)
        if json_data is None:
            return jsonify({"errors": ["Request body must be JSON."]}), 400

        try:
            data = expense_schema.load(json_data, unknown=EXCLUDE)
        except ValidationError as err:
            return jsonify({"errors": err.messages}), 422

        try:
            expense = Expense(
                user_id=user.id,
                title=data["title"],
                amount=data["amount"],
                category=data["category"],
                date=data["date"],  # a real date object, thanks to Marshmallow's fields.Date
            )
            db.session.add(expense)
            db.session.commit()
        except ValueError as e:
            db.session.rollback()
            return jsonify({"errors": [str(e)]}), 422

        return jsonify(expense_schema.dump(expense)), 201

    @app.route("/expenses/<int:id>", methods=["GET"])
    def get_expense(id):
        user = get_current_user()
        if user is None:
            return jsonify({"errors": ["Not authorized."]}), 401

        expense = Expense.query.filter_by(id=id, user_id=user.id).first()
        if expense is None:
            return jsonify({"errors": ["Expense not found."]}), 404

        return jsonify(expense_schema.dump(expense)), 200

    @app.route("/expenses/<int:id>", methods=["PATCH"])
    def update_expense(id):
        user = get_current_user()
        if user is None:
            return jsonify({"errors": ["Not authorized."]}), 401

        expense = Expense.query.filter_by(id=id, user_id=user.id).first()
        if expense is None:
            return jsonify({"errors": ["Expense not found."]}), 404

        json_data = request.get_json(silent=True)
        if json_data is None:
            return jsonify({"errors": ["Request body must be JSON."]}), 400

        try:
            data = expense_update_schema.load(json_data, unknown=EXCLUDE)
        except ValidationError as err:
            return jsonify({"errors": err.messages}), 422

        try:
            for field in ("title", "amount", "category", "date"):
                if field in data:
                    setattr(expense, field, data[field])
            db.session.commit()
        except ValueError as e:
            db.session.rollback()
            return jsonify({"errors": [str(e)]}), 422

        return jsonify(expense_schema.dump(expense)), 200

    @app.route("/expenses/<int:id>", methods=["DELETE"])
    def delete_expense(id):
        user = get_current_user()
        if user is None:
            return jsonify({"errors": ["Not authorized."]}), 401

        expense = Expense.query.filter_by(id=id, user_id=user.id).first()
        if expense is None:
            return jsonify({"errors": ["Expense not found."]}), 404

        db.session.delete(expense)
        db.session.commit()
        return "", 204