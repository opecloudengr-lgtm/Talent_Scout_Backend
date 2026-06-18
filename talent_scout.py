from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from marshmallow import Schema, fields, ValidationError
from marshmallow.validate import Length
import uuid

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///talent_scout.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


# =========================
#           MODELS
# =========================

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    current_position = db.Column(db.String(100), nullable=True)
    company = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(100), nullable=False)
    timeline = db.relationship("Timeline", backref="user", lazy=True)


class Timeline(db.Model):
    __tablename__ = "timeline"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.String(36),db.ForeignKey("users.id"),nullable=False)

# =========================
#           SCHEMAS
# =========================

class UserSchema(Schema):
    id = fields.Str(dump_only=True)
    first_name = fields.Str()
    last_name = fields.Str()
    email = fields.Email(required=True)
    current_position = fields.Str()
    company = fields.Str()
    password = fields.Str(required=True, validate=Length(min=8), load_only=True)


class UpdateUserSchema(Schema):
    first_name = fields.Str()
    last_name = fields.Str()
    email = fields.Email()
    current_position = fields.Str()
    company = fields.Str()
    password = fields.Str(validate=Length(min=8))


class TimelineSchema(Schema):
    id = fields.Str(dump_only=True)
    content = fields.Str(required=True, validate=Length(min=5))
    user_id = fields.Str(dump_only=True)


user_schema = UserSchema()
users_schema = UserSchema(many=True)
update_user_schema = UpdateUserSchema()
timeline_schema = TimelineSchema()
timelines_schema = TimelineSchema(many=True)


# =========================
#       USER ROUTES
# =========================

@app.route("/users", methods=["POST"])
def post_user():
    data = request.get_json()
    try:
        validated_data = user_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "errors": err.messages
        }), 400
    existing_user = User.query.filter_by(email=validated_data["email"]).first()
    if existing_user:
        return jsonify({
            "message": "Email already exists"
        }), 409
    new_user = User(
        email=validated_data["email"],
        password=validated_data["password"]
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Sign-Up successful"}), 201

# =========================
#           RUN APP
# =========================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)