from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(200))
    dob = db.Column(db.Date)          # Date of birth
    weight = db.Column(db.Float)      # in kg
    height = db.Column(db.Float)      # in cm
    goal = db.Column(db.String(50))   # Weight loss / Maintain / Gain
