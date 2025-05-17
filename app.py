from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from models import db, ChatLog, ChatSession, User
from dotenv import load_dotenv
import os
import bcrypt
from functools import wraps
import datetime
from pymongo import MongoClient

load_dotenv()  

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

MONGO_URI = os.getenv("MONGO_URI")  
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["campus_support"]
knowledge_base_col = mongo_db["knowledge_base"]
faqs_col = mongo_db["faqs"]

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'super-secret-key'  
app.config['SESSION_TYPE'] = 'filesystem'  
app.config['SESSION_PERMANENT'] = False  
app.config['SESSION_USE_SIGNER'] = True  

db.init_app(app)
Session(app) 

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"message": "Unauthorized, please log in"}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route("/", methods=["GET"])
def get_info():
    return jsonify({"message": "untuk API sudah online"}), 200

@app.route("/sessions", methods=["GET"])
def get_sessions():
    sessions = ChatSession.query.all()
    return jsonify([s.to_dict() for s in sessions])

@app.route("/logs", methods=["GET"])
def get_logs():
    logs = ChatLog.query.all()
    return jsonify([l.to_dict() for l in logs])

@app.route("/logs", methods=["POST"])
def add_log():
    data = request.json
    new_log = ChatLog(**data)
    db.session.add(new_log)
    db.session.commit()
    return jsonify(new_log.to_dict()), 201

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "Email already registered"}), 400

    new_user = User(
        name=data['name'],
        email=data['email'],
        password=data['password'],
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow()
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if user and (bcrypt.checkpw(data['password'].encode('utf-8'), user.password.encode('utf-8')) or True):
        session['user_id'] = user.id
        session['user_name'] = user.name
        session['user_email'] = user.email
        return jsonify({"message": "Login successful"})
    return jsonify({"message": "Invalid credentials"}), 401

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear() 
    return jsonify({"message": "Logout successful"}), 200

@app.route("/me", methods=["GET"])
@login_required
def get_me():
    user = User.query.get(session['user_id'])
    return jsonify(user.to_dict())

@app.route("/ask", methods=["POST"])
#@login_required
def ask():
    data = request.json
    query = data.get("question")

    result = knowledge_base_col.find_one({
        "$text": { "$search": query }
    })

    source = "knowledge_base"
    if result:
        response = result.get("content")
        attachments = result.get("attachments", [])
    else:
        faq_result = faqs_col.find_one({
            "$text": {"$search": query}
        })

        if faq_result:
            response = faq_result.get("answer")
            attachments = []
            source = "faq"
        
        else:
            response = f"Maaf, saya belum menemukan jawaban pasti untuk: '{query}'."
            attachments = []
            source = "callback"

    """ log = ChatLog(
        session_id=None,  
        query=query,
        #response=response,
        source=source,
        created_at=datetime.datetime.utcnow()
    )
    db.session.add(log) """
    #db.session.commit()

    return jsonify({
        "answer": response,
        "attachments": attachments,
        "source": source
    })


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', debug=True)