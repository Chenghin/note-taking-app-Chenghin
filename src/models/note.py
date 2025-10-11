from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    # integer order field for manual ordering; higher numbers appear first
    order = db.Column(db.Integer, nullable=False, default=0)
    # store tags as JSON text
    tags = db.Column(db.Text, nullable=True)
    event_date = db.Column(db.String(50), nullable=True)
    event_time = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Note {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'order': self.order,
            'tags': [] if not self.tags else __import__('json').loads(self.tags),
            'event_date': self.event_date,
            'event_time': self.event_time,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

