
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
    failed_login_attempts = db.Column(db.Integer, default=0)
    is_locked = db.Column(db.Boolean, default=False) # This is the backend field for login blocking
    is_blocked = db.Column(db.Boolean, default=False) # This is for manual admin blocking
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
        """
        Serializes the User object to a dictionary.
        The key 'is_login_blocked' is intentionally used to map the 'is_locked' field,
        as this is what the frontend template expects.
        """
        return {
            'id': self.id,
            'username': self.username,
            'is_login_blocked': self.is_locked, # Maps backend is_locked to frontend is_login_blocked
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
    is_archived = db.Column(db.Boolean, default=False, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user': self.requester.username,
            'sistema': self.sistema,
            'justificativa': self.justificativa,
            'status': self.status,
            'admin_notes': self.admin_notes,
            'requested_at': self.requested_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_archived': self.is_archived
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

class KnowledgeBaseArticle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kb_id = db.Column(db.Integer, unique=True, nullable=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'kb_id': self.kb_id,
            'title': self.title,
            'content': self.content,
            'image_path': self.image_path,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f"KnowledgeBaseArticle('KB{self.kb_id:02d} - {self.title}', '{self.created_at}')"

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    logo = db.Column(db.String(500), nullable=True)
    contact_person = db.Column(db.String(150), nullable=True)
    email = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Ativo') # Ativo, Inativo
    panel_url = db.Column(db.String(500), nullable=True)
    wiki_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'logo': self.logo,
            'status': self.status,
            'panel_url': self.panel_url,
            'wiki_url': self.wiki_url,
            'contact_person': self.contact_person,
            'email': self.email,
            'phone': self.phone,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
