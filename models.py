from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'
    session_id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    started_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
        }

class ChatLog(db.Model):
    __tablename__ = 'chat_logs'
    log_id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text)
    source = db.Column(db.Enum('knowledge_base', 'ai_generated'), nullable=False)
    knowledge_id = db.Column(db.String(24))
    created_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "log_id": self.log_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "question": self.question,
            "answer": self.answer,
            "source": self.source,
            "knowledge_id": self.knowledge_id,
            "created_at": self.created_at,
        }

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)  
    email_verified_at = db.Column(db.DateTime, nullable=True)
    remember_token = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email
        }