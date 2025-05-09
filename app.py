from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from models import db, ChatLog, ChatSession
from dotenv import load_dotenv
import os

load_dotenv()  # Load .env file

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

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

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)