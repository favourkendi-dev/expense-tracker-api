#!/usr/bin/env python3

import random
from datetime import timedelta
from faker import Faker
from app import create_app
from models import db, User, Expense
from schemas import VALID_CATEGORIES

fake = Faker()
app = create_app()

with app.app_context():
    print("Clearing existing data")
    Expense.query.delete()
    User.query.delete()
    db.session.commit()

    print("Seeding users")
    users = []
    demo_user = User(username="favour")
    demo_user.password_hash = "demo123"
    users.append(demo_user)

    for _ in range(3):
        user = User(username=fake.unique.user_name())
        user.password_hash = "password123"
        users.append(user)

    db.session.add_all(users)
    db.session.commit()

    print("Seeding expenses")
    expenses = []
    for user in users:
        for _ in range(random.randint(5, 10)):
            expense = Expense(
                user_id=user.id,
                title=fake.sentence(nb_words=3).rstrip("."),
                amount=round(random.uniform(5, 500), 2),
                category=random.choice(list(VALID_CATEGORIES)),
                date=fake.date_between(start_date="-90d", end_date="today"),
            )
            expenses.append(expense)

    db.session.add_all(expenses)
    db.session.commit()

    print(f"Done seeding Created {len(users)} users and {len(expenses)} expenses")
    print("Demo login username: favour / password: demo123")
   