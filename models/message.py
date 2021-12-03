import os, sys
from passlib.apps import custom_app_context as pwd_context
from models.serializer import Serializer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import db, app

class Message(db.Model, Serializer):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), 
                      nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), 
                      nullable=False, index=True)
    mode = db.Column(db.String(32))
    body = db.Column(db.String(32))
    date = db.Column(db.DateTime)