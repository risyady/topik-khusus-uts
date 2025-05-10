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
from bson import ObjectId

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

    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt(rounds=12))
    new_user = User(
        name=data['name'],
        email=data['email'],
        password=hashed_password.decode('utf-8'),
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
    if user and bcrypt.checkpw(data['password'].encode('utf-8'), user.password.encode('utf-8')):
        session['user_id'] = user.id
        session['user_name'] = user.name
        session['user_email'] = user.email
        return jsonify({"message": "Login successful"})
    return jsonify({"message": "Invalid credentials"}), 401

@app.route("/logout", methods=["POST"])
#@login_required
def logout():
    session.clear() 
    return jsonify({"message": "Logout successful"}), 200

@app.route("/me", methods=["GET"])
#@login_required
def get_me():
    user = User.query.get(session['user_id'])
    return jsonify(user.to_dict())

@app.route("/ask", methods=["POST"])
#@login_required
def ask():
    data = request.json
    query = data.get("question")

    kb_result = knowledge_base_col.find({
        "$text": { "$search": query }
    })

    """ source = "knowledge_base"
    if result:
        response = result.get("content")
        attachments = result.get("attachments", []) """
    
    faq_result = faqs_col.find({
        "$text": {"$search": query}
    })

    result_list = []

    for result in kb_result:
        result_list.append({
            "content": result.get("content"),
            "attachments": result.get("attachments", []),
            "source": "knowledge_base"
        })

    for result in faq_result:
        result_list.append({
            "content": result.get("answer"),
            "attachments": [],
            "source": "faq"
        })
    
    if not result_list:
        result_list.append({
            "content": f"Maaf, saya belum menemukan jawaban pasti untuk: '{query}'.",
            "attachments": [],
            "source": "ai_generated"
        })

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
        "answers": result_list
    })

@app.route("/knowledge_base", methods=["POST"])
def create_kb():
    data = request.json
    kb_doc = {
        "title": data.get("title"),
        "content": data.get("content"),
        "keywords": data.get("keywords", []),
        "attachments": data.get("attachments", []),
        "dept_id": data.get("dept_id"),
        "created_at": datetime.datetime.utcnow(),
        "updated_at": datetime.datetime.utcnow()
    }
    result = knowledge_base_col.insert_one(kb_doc)
    return jsonify({"message": "Knowledge base created", "id": str(result.inserted_id)}), 201

@app.route("/knowledge_base", methods=["GET"])
def read_all_kb():
    results = list(knowledge_base_col.find())
    formatted = [{
        "id": str(item["_id"]),
        "title": item.get("title"),
        "content": item.get("content"),
        "keywords": item.get("keywords", []),
        "attachments": item.get("attachments", []),
        "dept_id": item.get("dept_id"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at")
    } for item in results]
    return jsonify(formatted)

@app.route("/knowledge_base/<string:id>", methods=["GET"])
def read_one_kb(id):
    result = knowledge_base_col.find_one({"_id": ObjectId(id)})
    if not result:
        return jsonify({"message": "Data not found"}), 404
    return jsonify({
        "id": str(result["_id"]),
        "title": result.get("title"),
        "content": result.get("content"),
        "keywords": result.get("keywords", []),
        "attachments": result.get("attachments", []),
        "dept_id": result.get("dept_id"),
        "created_at": result.get("created_at"),
        "updated_at": result.get("updated_at")
    })

@app.route("/knowledge_base/<string:id>", methods=["PUT"])
def update_kb(id):
    data = request.json
    update_data = {
        "title": data.get("title"),
        "content": data.get("content"),
        "keywords": data.get("keywords", []),
        "attachments": data.get("attachments", []),
        "dept_id": data.get("dept_id"),
        "updated_at": datetime.datetime.utcnow()
    }
    result = knowledge_base_col.update_one({"_id": ObjectId(id)}, {"$set": update_data})
    if result.matched_count == 0:
        return jsonify({"message": "Data not found"}), 404
    return jsonify({"message": "Knowledge base updated"})

@app.route("/knowledge_base/<string:id>", methods=["DELETE"])
def delete_kb(id):
    result = knowledge_base_col.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        return jsonify({"message": "Data not found"}), 404
    return jsonify({"message": "Knowledge base deleted"})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', debug=True)