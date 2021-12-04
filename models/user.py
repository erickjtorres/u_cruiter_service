import os, sys
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from sqlalchemy import text
from db import db, app

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text(), index=True)
    password_hash = db.Column(db.Text())
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    company = db.Column(db.String(100))
    corporate_email = db.Column(db.String(100))
    title = db.Column(db.String(100))
    current_salary = db.Column(db.Integer)
    expected_salary = db.Column(db.String(100))
    school = db.Column(db.String(100))
    licenses = db.Column(db.String(100))
    skills = db.Column(db.Text())
    bio = db.Column(db.Text())
    degrees = db.Column(db.String(100))
    organization = db.Column(db.String(100))
    date = db.Column(db.DateTime)

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None    # valid token, but expired
        except BadSignature:
            return None    # invalid token
        user = User.query.get(data['id'])
        return user

