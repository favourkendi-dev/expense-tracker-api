
from marshmallow import Schema, fields, validate

VALID_CATEGORIES = {"food", "transport", "housing", "entertainment", "utilities", "other"}


class ExpenseSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=1, error="Title cannot be empty."))
    amount = fields.Float(
        required=True,
        validate=validate.Range(min=0.01, error="Amount must be positive.")
    )
    category = fields.Str(
        required=True,
        validate=validate.OneOf(VALID_CATEGORIES, error="Category must be one of: {choices}.")
    )
    date = fields.Date(required=True)  
    user_id = fields.Int(dump_only=True)


class ExpenseUpdateSchema(Schema):
    title = fields.Str(validate=validate.Length(min=1))
    amount = fields.Float(validate=validate.Range(min=0.01))
    category = fields.Str(validate=validate.OneOf(VALID_CATEGORIES))
    date = fields.Date()