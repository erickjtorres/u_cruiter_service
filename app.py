#!flask/bin/python
from operator import pos
import os
from models.user import User
from models.user_to_candidate import UserToCandidate
from models.user_to_chat import UserToChats
from models.user_to_job import UserToJob
from models.request import Request
from models.message import Message
from models.chat import Chats
from flask import Flask, abort, request, jsonify, g, url_for
from flask_httpauth import HTTPBasicAuth
from db import db, app, socketio
from datetime import datetime
from sqlalchemy import or_, tuple_, and_, text
import json
# extensions
auth = HTTPBasicAuth()

# Need to refactor --> split into seperate controllers --> auth, requests, etc


# Authentication + User
@app.route('/api/users', methods=['POST'])
def new_user():
    content = request.get_json()
    email = content['email']
    password = content['password']
    first_name = content['first_name']
    last_name = content['last_name']
    company = content['company']
    corporate_email = content['corporate_email']
    title = content['title']
    current_salary = content['current_salary']
    expected_salary = content['expected_salary']
    school = content['school']
    licenses = content['licenses']
    degrees = content['degrees']
    bio = content['bio']
    skills = content['skills']
    organization = content['organization']
    date = datetime.utcnow()
    if email is None or password is None:
        abort(400)    # missing arguments
    if User.query.filter_by(email=email).first() is not None:
        abort(400)    # existing user
    user = User(email=email, first_name=first_name, last_name=last_name, company=company, corporate_email=corporate_email, title=title, current_salary=current_salary,
                expected_salary=expected_salary, school=school, licenses=licenses, degrees=degrees, organization=organization, skills=skills, bio=bio, date=date)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return (jsonify({'email': user.email}), 201,
            {'Location': url_for('get_user', id=user.id, _external=True)})


@app.route('/api/user/<int:id>')
def get_user(id):
    user = User.query.get(id)
    response = {}
    response["id"] = user.id
    response["email"] = user.email
    response["first_name"] = user.first_name
    response["last_name"] = user.last_name
    response["company"] = user.company
    response["corporate_email"] = user.corporate_email
    response["title"] = user.title
    response["skills"] = user.skills
    response["current_salary"] = user.current_salary
    response["expected_salary"] = user.expected_salary
    response["school"] = user.school
    response["licenses"] = user.licenses
    response["degrees"] = user.degrees
    response["organization"] = user.organization
    response["bio"] = user.bio
    if not response:
        abort(400)
    return jsonify({'user': response})


@app.route('/api/users',  methods=['GET'])
@auth.login_required
def get_candidates():
    result = User.query.all()
    if not result:
        abort(400)
    users = []
    for row in result:
        user = {}
        if(g.user.id == row.id):
            continue
        user["id"] = row.id
        user["email"] = row.email
        user["first_name"] = row.first_name
        user["last_name"] = row.last_name
        user["company"] = row.company
        user["corporate_email"] = row.corporate_email
        user["title"] = row.title
        user["skills"] = row.skills
        user["current_salary"] = row.current_salary
        user["expected_salary"] = row.expected_salary
        user["school"] = row.school
        user["licenses"] = row.licenses
        user["degrees"] = row.degrees
        user["organization"] = row.organization
        user["bio"] = row.bio
        users.append(user)

    return (jsonify({"candidates": users}))


@app.route('/api/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(5000)
    return jsonify({'token': token.decode('ascii'), 'duration': 5000})


@auth.verify_password
def verify_password(email, password):
    # first try to authenticate by token
    user = User.verify_auth_token(email)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(email=email).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


def messageReceived():
    print('message was received!!!')

# Messages


@app.route('/api/messages', methods=['POST'])
@auth.login_required
def send_message():
    content = request.get_json()
    sender_id = g.user.id
    receiver_id = content['receiver_id']
    mode = content['mode']
    body = content['body']
    chat_id = content['chat_id']
    date = datetime.utcnow()

    if sender_id is None or receiver_id is None:
        abort(400)    # missing arguments
    message = Message(sender_id=sender_id, receiver_id=receiver_id,
                      mode=mode, body=body, date=date, chat_id=chat_id)
    db.session.add(message)
    db.session.commit()

    socketio.emit('new_message', Message.serialize(Message(id=message.id, sender_id=sender_id, receiver_id=receiver_id,
                                                           mode=mode, body=body, date="", chat_id=chat_id)), callback=messageReceived)
    return (jsonify({'success': "message sent"}), 201)


@app.route('/api/messages/<int:chat_id>', methods=['GET'])
@auth.login_required
def get_messages(chat_id):
    messages = Message.query.filter(or_(Message.chat_id == chat_id)).all()
    print('MESSAGES', messages)
    return jsonify({"messages": Message.serialize_list(messages)})


@app.route('/api/chat', methods=['POST'])
@auth.login_required
def create_chat():
    content = request.get_json()
    with_ = content['with']

    chat = Chats()
    db.session.add(chat)
    db.session.commit()

    usersChat0 = UserToChats(user_id=g.user.id, chat_id=chat.id, with_id=with_)
    usersChat1 = UserToChats(user_id=with_, chat_id=chat.id, with_id=g.user.id)
    db.session.add(usersChat0)
    db.session.add(usersChat1)
    db.session.commit()

    return jsonify({"chat_id": chat.id})


@app.route('/api/chat', methods=['GET'])
@auth.login_required
def get_chats():
    chats = UserToChats.query.filter(
        and_(or_(UserToChats.user_id == g.user.id))).all()
    return jsonify({"chats": UserToChats.serialize_list(chats)})

# Requests


# For Recruiters


@app.route('/api/candidate/like', methods=['POST'])
@auth.login_required
def send_candidate_like():
    #  we want to like a candidate (as a recruiter) -> and generate a job match
    content = request.get_json()
    user_id = str(g.user.id)
    candidate_id = content["candidate_id"]
    if "job_id" in content:
        best_job_id = content["job_id"]
        user_to_job = UserToJob(
            user_id=user_id, candidate_id=candidate_id, job_id=best_job_id)
        db.session.add(user_to_job)
        db.session.commit()
        return (jsonify({'success': "request sent"}), 201)

    # get the latest recruiter from the company of interest, highest paying, and our same profession
    query = """select * from job_postings where job_postings.company = (select users.company from users where users.id = """ + user_id + """) 
and job_postings.job_title = (select users.title from users where users.id = """ + candidate_id + """)
and job_postings.salary = (select max(job_postings.salary) from job_postings
where job_postings.company = (select users.company from users where users.id = """ + candidate_id + """) 
and job_postings.job_title = (select users.title from users where users.id = """ + candidate_id + """)) """
    result = db.engine.execute(query)
    best_job_id = result.first()[0]

    if user_id is None or candidate_id is None:
        abort(400)    # missing arguments
    user_to_job = UserToJob(
        user_id=user_id, candidate_id=candidate_id, job_id=best_job_id)
    db.session.add(user_to_job)
    db.session.commit()
    return (jsonify({'success': "request sent"}), 201)

# For applicants


@app.route('/api/posting/like', methods=['POST'])
@auth.login_required
def send_posting_like():
    #  we want to like a posting (as an applicant) -> and generate a recruiter
    content = request.get_json()
    user_id = g.user.id
    job_id = content["job_id"]

    if "latest_recruiter" in content:
        latest_recruiter = content["latest_recruiter"]
        user_to_job = UserToCandidate(
            user_id=user_id, job_id=job_id, candidate_id=latest_recruiter)
        db.session.add(user_to_job)
        db.session.commit()
        return (jsonify({'success': "request sent"}), 201)

    # get the latest recruiter from the company of interest
    query = """select users.id from users 
where users.company like (select job_postings.company from job_postings where job_postings.posting_id = '""" + job_id + """')
"""
    result = db.engine.execute(query)
    result = result.first()[0]

    if user_id is None or job_id is None:
        abort(400)    # missing arguments
    user_to_job = UserToCandidate(
        user_id=user_id, job_id=job_id, candidate_id=result)
    db.session.add(user_to_job)
    db.session.commit()
    return (jsonify({'success': "request sent"}), 201)


@app.route('/api/get-matches/<id>', methods=["GET"])
@auth.login_required
def get_matches(id):
    user_id = id

    # jobs where you job was chosen first (we suggest you)
    sql = text("""select userstocandidates.* as recruiter, userstocandidates.job_id, job_postings.*  from userstocandidates
inner join job_postings on (userstocandidates.job_id = job_postings.posting_id)
where userstocandidates.candidate_id = """ + str(user_id) + """""")

    data = {}
    result = db.engine.execute(sql)
    data["applicant"] = [row._asdict() for row in result]
    # jobs where you were chosen (we suggest job)
    sql = text("""select userstojobs.* as recruiter, userstojobs.job_id, job_postings.*  from userstojobs
inner join job_postings on (userstojobs.job_id = job_postings.posting_id)
where userstojobs.candidate_id = """ + str(user_id) + """""")
    result = db.engine.execute(sql)
    data["recruiter"] = [row._asdict() for row in result]

    return json.dumps(data, default=str)


@app.route('/api/postings', methods=['GET'])
@auth.login_required
def get_job_postings():
    # potentially will need to remove the already liked postings
    user_id = g.user.id
    sql = text('select * from job_postings')
    result = db.engine.execute(sql)
    if user_id is None:
        abort(400)    # missing arguments
    postings = []
    for row in result:
        posting = {}
        posting["id"] = row[0]
        posting["posting_id"] = row[1]
        posting["job_title"] = row[2]
        posting["company"] = row[3]
        posting["location"] = row[4]
        posting["date_posted"] = row[5]
        posting["date_extracted"] = row[6]
        posting["short_summary"] = row[7]
        posting["rating"] = row[8]
        posting["salary"] = row[10]
        posting["html_description"] = row[14]
        postings.append(posting)

    return (jsonify({"job_postings": postings}))


@app.route("/api/")
# Other
@app.route('/api/current-user')
@auth.login_required
def get_current_user():
    return jsonify({'user':  g.user.id})


@app.route('/api/potential-ucruiters/<job_posting_id>', methods=["GET"])
@auth.login_required
def get_potential_ucruiters(job_posting_id):
    # via a job posting, get the people that could recommend you to this job
    if job_posting_id is None:
        abort(400)
    sql = text("""select * from users where users.company like 
	(select company from job_postings where posting_id like '""" + job_posting_id + """') and users.id != '""" + str(g.user.id) + """' """)
    result = db.engine.execute(sql)

    return json.dumps([row._asdict() for row in result], default=str)


@app.route('/api/potential-recommend-jobs', methods=["GET"])
@auth.login_required
def get_potential_recommended_jobs():
    # jobs that a user can recommend (jobs from their own company)
    if g.user.id is None:
        abort(400)
    sql = text("""select * from job_postings 
               where job_postings.company = 
               (select users.company from users where users.id = '""" + str(g.user.id) + """')""")
    result = db.engine.execute(sql)

    return json.dumps([row._asdict() for row in result])


@app.route('/api/create-request', methods=["POST"])
@auth.login_required
def create_request():
    content = request.get_json()
    receiver = str(content["receiver_id"])
    mode = content["mode"]
    job_post_name = content["job_post_name"]

    sql = text("insert into requests (sender_id, receiver_id, mode, subject_id, accepted) values (" +
               str(g.user.id) + ", " + receiver + ", '" + mode + "', '" + job_post_name + "', ' FALSE ');")
    db.engine.execute(sql)
    

    return (jsonify({'success': "request sent"}), 201)


@app.route('/api/delete-request/<id>', methods=["GET"])
@auth.login_required
def delete_request(id):
    if not id:
        abort(400)
    sql = text("delete from requests where id = " + str(id) + ";")
    db.engine.execute(sql)
    return (jsonify({'success': "request sent"}), 201)


@app.route('/api/accept-request/<id>', methods=["GET"])
@auth.login_required
def accept_request(id):
    user_id = str(g.user.id)
    sender_id = str(id)
    sql = text("""update requests set accepted = True where requests.id = """ +
               sender_id + """ and requests.receiver_id = """ + user_id + """""")
    db.engine.execute(sql)

    return (jsonify({'success': "request sent"}), 201)


@app.route('/api/get-request-list/<mode>', methods=["GET"])
@auth.login_required
def get_request_list(mode):
    if not mode:
        abort(400)
    request_received_mode = "recruiter"
    if(mode == "recruiter"):
        request_received_mode = "applicant"

    sql = text("""select requests.id as request_id, requests.mode, requests.sender_id, requests.subject_id, 
requests.receiver_id, job_postings.company as job_postings_company, job_postings.salary, job_postings.job_title as job_postings_job_title, job_postings.id as job_postings_id, users.* from requests inner join 
    users ON (users.id = requests.sender_id) inner join job_postings on (job_postings.posting_id = requests.subject_id)
    where requests.mode = '""" + request_received_mode + """'
    AND requests.receiver_id = """ + str(g.user.id) + """
    AND requests.accepted != TRUE
    """)
    result = db.engine.execute(sql)

    output = {}
    output["request_received"] = [row._asdict() for row in result]

    sql = text("""select requests.id as request_id, requests.mode, requests.sender_id, requests.subject_id, 
requests.receiver_id, job_postings.company as job_postings_company, job_postings.salary, job_postings.job_title as job_postings_job_title, job_postings.id as job_postings_id, users.* from requests inner join 
users ON (users.id = requests.receiver_id) inner join job_postings on (job_postings.posting_id = requests.subject_id)
where requests.mode = '""" + mode + """'
AND requests.sender_id = """ + str(g.user.id) + """""")

    result = db.engine.execute(sql)
    output["request_sent"] = [row._asdict() for row in result]

    return json.dumps(output, default=str)


def index():
    return "Hello, World!"


if __name__ == '__main__':
    # this needs to be updated --> needs to check if tables have been created
    if not os.path.exists('db.sqlite'):
        db.create_all()
    socketio.run(app, debug=True)
