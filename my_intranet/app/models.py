
from . import db
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, date

# Association table for the many-to-many relationship between User and Group
user_group = db.Table('user_group',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'))
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_blocked = db.Column(db.Boolean, default=False)
    is_suspended = db.Column(db.Boolean, default=False)
    groups = db.relationship('Group', secondary=user_group, backref='users')
    news = db.relationship('News', backref='author', lazy=True)
    events = db.relationship('Event', backref='creator', lazy=True)
    requests = db.relationship('AccessRequest', backref='requester', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def is_in_group(self, group_name):
        for group in self.groups:
            if group.name == group_name:
                return True
        return False

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'is_blocked': self.is_blocked,
            'is_suspended': self.is_suspended
        }

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    children = db.relationship('Group', backref=db.backref('parent', remote_side=[id]))

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    publication_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'image_url': self.image_url,
            'publication_date': self.publication_date.isoformat(),
            'author': self.author.to_dict()
        }

    def __repr__(self):
        return f"News('{self.title}', '{self.publication_date}')"

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    event_date = db.Column(db.Date, nullable=False)
    publication_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    location = db.Column(db.String(200), nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'image_url': self.image_url,
            'event_date': self.event_date.isoformat() if self.event_date else None,
            'publication_date': self.publication_date.isoformat(),
            'location': self.location,
            'creator': self.creator.to_dict()
        }

    def __repr__(self):
        return f"Event('{self.title}', '{self.event_date}')"

class AccessRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sistema = db.Column(db.String(150), nullable=False)
    justificativa = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Pendente')  # Status: Pendente, Em andamento, Liberado, Negado
    admin_notes = db.Column(db.Text, nullable=True)
    requested_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user': self.requester.username,
            'sistema': self.sistema,
            'justificativa': self.justificativa,
            'status': self.status,
            'admin_notes': self.admin_notes,
            'requested_at': self.requested_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(500), nullable=False)
    link = db.Column(db.String(500), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='notifications')

    def to_dict(self):
        return {
            'id': self.id,
            'message': self.message,
            'link': self.link,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat()
        }
