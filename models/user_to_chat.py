from db import db, app
import os
import sys
from passlib.apps import custom_app_context as pwd_context
from models.serializer import Serializer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class UserToChats(db.Model, Serializer):
    __tablename__ = 'usertochats'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"),
                        nullable=False, index=True)
    with_id = db.Column(db.Integer, db.ForeignKey("users.id"),
                        nullable=False, index=True)
    chat_id = db.Column(db.Integer, db.ForeignKey("chats.id"),
                        nullable=False, index=True)
