import os, sys
from passlib.apps import custom_app_context as pwd_context
from models.serializer import Serializer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import db, app

class Chats(db.Model, Serializer):
    __tablename__ = 'chats'
    id = db.Column(db.Integer, primary_key=True)