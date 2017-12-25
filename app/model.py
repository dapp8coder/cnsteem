from . import db
class Order(db.Model):
    __tablename__ = "order"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(100))
    create_time = db.Column(db.DateTime)
    status = db.Column(db.Boolean)
