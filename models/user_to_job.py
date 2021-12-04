import os, sys
from passlib.apps import custom_app_context as pwd_context
from models.serializer import Serializer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import db

# Only meant to be used in recruiter mode 
class UserToJob(db.Model, Serializer):
    __tablename__ = 'userstojobs'
    id = db.Column(db.Integer, primary_key=True) 
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), 
                      nullable=False, index=True) # id of recruiter (our id)
    candidate_id =  db.Column(db.Integer, db.ForeignKey("users.id"), 
                      nullable=False, index=True) # who they liked 
    job_id = db.Column(db.String, nullable = True) # generated job match 