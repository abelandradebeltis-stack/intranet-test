from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from .models import Event
from . import db
from .decorators import group_required
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from flask import current_app

eventos_bp = Blueprint('eventos', __name__, url_prefix='/eventos')

def save_image(file):
    if not file or file.filename == '':
        return None
    filename = secure_filename(file.filename)
    unique_filename = f"{current_user.id}_{os.urandom(8).hex()}_{filename}"
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, unique_filename)
    os.makedirs(upload_folder, exist_ok=True)
    file.save(file_path)
    return os.path.join('uploads', unique_filename)

@eventos_bp.route('/administracao')
@login_required
@group_required('Eventos', 'Marketing')
def administracao():
    return render_template('eventos_administracao.html')

@eventos_bp.route('/publicar', methods=['GET', 'POST'])
@login_required
@group_required('Eventos', 'Marketing')
def publicar():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        event_date_str = request.form['event_date']
        image_file = request.files.get('image')

        if title and description and event_date_str:
            event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
            image_url = save_image(image_file)
            new_event = Event(title=title, description=description, event_date=event_date, image_url=image_url, creator_id=current_user.id)
            db.session.add(new_event)
            db.session.commit()
            flash('Evento publicado com sucesso!', 'success')
            return redirect(url_for('eventos.administracao'))
    return render_template('eventos_publicacoes.html')

@eventos_bp.route('/editar/<int:event_id>', methods=['GET', 'POST'])
@login_required
@group_required('Eventos', 'Marketing')
def editar(event_id):
    event_item = Event.query.get_or_404(event_id)
    if request.method == 'POST':
        event_item.title = request.form['title']
        event_item.description = request.form['description']
        event_date_str = request.form['event_date']
        event_item.event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
        image_file = request.files.get('image')

        if image_file:
            if event_item.image_url:
                old_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(event_item.image_url))
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            event_item.image_url = save_image(image_file)

        db.session.commit()
        flash('Evento atualizado com sucesso!', 'success')
        return redirect(url_for('eventos.administracao'))
    return render_template('eventos_publicacoes.html', event_item=event_item)

@eventos_bp.route('/deletar/<int:event_id>', methods=['POST'])
@login_required
@group_required('Eventos', 'Marketing')
def deletar(event_id):
    event_item = Event.query.get_or_404(event_id)
    if event_item.image_url:
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(event_item.image_url))
        if os.path.exists(image_path):
            os.remove(image_path)
    db.session.delete(event_item)
    db.session.commit()
    return jsonify(status='success', message='Evento deletado com sucesso!')

@eventos_bp.route('/api/events', methods=['GET'], endpoint='get_events_api')
@login_required
@group_required('Eventos', 'Marketing')
def get_events_api():
    event_items = Event.query.order_by(Event.event_date.asc()).all()
    return jsonify(events=[event.to_dict() for event in event_items])
