from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy dog'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://ericktorres:pass@localhost/u_cruiter'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
socketio = SocketIO(app)

# extensions
db = SQLAlchemy(app)