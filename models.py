from flask_sqlalchemy import SQLAlchemy

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