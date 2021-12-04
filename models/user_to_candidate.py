import os, sys
from passlib.apps import custom_app_context as pwd_context
from models.serializer import Serializer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import db, app

#  
class UserToCandidate(db.Model, Serializer):
    __tablename__ = 'userstocandidates'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), 
                      nullable=False, index=True)
    job_id = db.Column(db.String, nullable = False)
    candidate_id = db.Column(db.Integer, db.ForeignKey("users.id"), 
                             nullable = False, index=True)