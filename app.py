#!flask/bin/python
from operator import pos
import os
from models.user import User
from models.user_to_candidate import UserToCandidate
from models.user_to_job import UserToJob
from models.request import Request
from models.message import Message
from flask import Flask, abort, request, jsonify, g, url_for
from flask_httpauth import HTTPBasicAuth
from db import db, app
from datetime import datetime
from sqlalchemy import or_, tuple_, and_, text
import json
#extensions
auth = HTTPBasicAuth()

#Need to refactor --> split into seperate controllers --> auth, requests, etc


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
    if email is None or password is None:
        abort(400)    # missing arguments
    if User.query.filter_by(email=email).first() is not None:
        abort(400)    # existing user
    user = User(email=email, first_name=first_name, last_name=last_name, company=company, corporate_email=corporate_email, title=title, current_salary=current_salary, expected_salary=expected_salary, school=school, licenses=licenses, degrees=degrees, organization=organization, skills=skills, bio=bio)
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

#Messages
@app.route('/api/messages', methods=['POST'])
@auth.login_required
def send_message():
    content = request.get_json()
    sender_id = g.user.id
    receiver_id = content['receiver_id']
    mode = content['mode']
    body = content['body']
    date = datetime.utcnow()

    if sender_id is None or receiver_id is None:
        abort(400)    # missing arguments
    message = Message(sender_id=sender_id, receiver_id=receiver_id, mode=mode, body=body, date=date)
    db.session.add(message)
    db.session.commit()
    return (jsonify({'success': "message sent"}), 201)

@app.route('/api/messages', methods=['GET'])
@auth.login_required
def get_messages():
    messages = Message.query.filter(or_(Message.receiver_id==g.user.id, Message.sender_id==g.user.id)).distinct(tuple_(Message.receiver_id, Message.sender_id)).all()
    return jsonify({"messages": Message.serialize_list(messages)})


@app.route('/api/chat/<int:id>', methods=['GET'])
@auth.login_required
def get_chat(id):
    messages = Message.query.filter(and_(or_(Message.receiver_id==g.user.id, Message.sender_id==id), or_(Message.receiver_id==id, Message.sender_id==g.user.id)) ).all()
    return jsonify({"chat": Message.serialize_list(messages)})



#Requests
@app.route('/api/requests', methods=['POST'])
@auth.login_required
def send_request():
    content = request.get_json()
    sender_id = g.user.id
    receiver_id = content["receiver_id"]
    mode = content["mode"] #Recruiter Mode or Candidate Mode
    subject_id = content["subject_id"] #Could be the posting --> the topic of the request?

    if sender_id is None or receiver_id is None:
        abort(400)    # missing arguments
    sent_request = Request(sender_id=sender_id, receiver_id=receiver_id, mode=mode, subject_id=subject_id)
    db.session.add(sent_request)
    db.session.commit()
    return (jsonify({'success': "request sent"}), 201)

@app.route('/api/requests/sent/<mode>', methods=['GET'])
@auth.login_required
def get_sent_requests(mode):
    request_sent = Request.query.filter_by(sender_id=g.user.id, mode=mode).all()
    return jsonify(Request.serialize_list(request_sent))


@app.route('/api/requests/received/<mode>', methods=['GET'])
@auth.login_required
def get_received_requests(mode):
    request_received = Request.query.filter_by(receiver_id=g.user.id, mode=mode).all()
    return jsonify(Request.serialize_list(request_received))


@app.route('/api/requests/<int:id>', methods=['DELETE'])
@auth.login_required
def remove_request(id):
    Request.query.filter_by(id=id).delete()
    return (jsonify({'success': "request deleted"}), 201)

#Candidates
@app.route('/api/candidate/like/<int:id>', methods=['POST'])
@auth.login_required
def send_candidate_like(id):
    user_id = g.user.id
    candidate_id = id
    liked = True

    if user_id is None or candidate_id is None:
        abort(400)    # missing arguments
    user_to_job = UserToJob(user_id=user_id, candidate_id=candidate_id, liked=liked)
    db.session.add(user_to_job)
    db.session.commit()
    return (jsonify({'success': "request sent"}), 201)

#Job Postings
@app.route('/api/posting/like/<int:id>', methods=['POST'])
@auth.login_required
def send_posting_like(id):
    user_id = g.user.id
    job_id = id
    liked = True

    if user_id is None or job_id is None:
        abort(400)    # missing arguments
    user_to_job = UserToJob(user_id=user_id, job_id=job_id, liked=liked)
    db.session.add(user_to_job)
    db.session.commit()
    return (jsonify({'success': "request sent"}), 201)

@app.route('/api/postings', methods=['GET'])
@auth.login_required
def get_job_postings():
    #potentially will need to remove the already liked postings
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


#Other
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
	(select company from job_postings where posting_id like '""" + job_posting_id + """')""")
    result = db.engine.execute(sql)
    
    return json.dumps([ row._asdict() for row in result ])

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
    
    return json.dumps([ row._asdict() for row in result ])


@app.route('/api/create-request', methods=["POST"])
@auth.login_required
def create_request():
    content = request.get_json()
    receiver = str(content["receiver_id"])
    mode = content["mode"]
    job_post_name = content["job_post_name"]  

    sql = text("insert into requests (sender_id, receiver_id, mode, subject_id) values (" + str(g.user.id) + ", " + receiver + ", '" + mode + "', '" + job_post_name +"');")
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

@app.route('/api/get-request-list/<mode>', methods=["GET"])
# @auth.login_required
def get_request_list(mode):
    if not mode: 
        abort(400)
    sql = text("""select distinct * from requests inner join 
    users ON (users.id = requests.receiver_id) inner join job_postings on (job_postings.id = requests.subject_id::int)
    where requests.mode = '""" + mode + """'
    AND requests.receiver_id = """ + str(g.user.id) + """
    """)
    result = db.engine.execute(sql)
    
    output = {} 
    output["request_received"] = [ row._asdict() for row in result ]
    
    sql = text("""select distinct * from requests inner join 
users ON (users.id = requests.sender_id) inner join job_postings on (job_postings.id = requests.subject_id::int)
where requests.mode = '""" + mode + """'
AND requests.sender_id = """ + str(g.user.id) + """""")
    
    result = db.engine.execute(sql)
    output["request_sent"] = [ row._asdict() for row in result ]
    
    return json.dumps(output)


def index():
    return "Hello, World!"

if __name__ == '__main__':
    #this needs to be updated --> needs to check if tables have been created
    if not os.path.exists('db.sqlite'):
        db.create_all()
    app.run(debug=True)
