
import os
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from bson.objectid import ObjectId
from pymongo import DESCENDING, ASCENDING

# Importa a instância do PyMongo e o modelo User
from . import pymongo
from .models import User
from .decorators import group_required

# Cria o Blueprint principal
main = Blueprint('main', __name__)

# --- Funções Auxiliares ---

def serialize_doc(doc):
    """Converte um documento MongoDB, incluindo ObjectId e datetime, para um dicionário serializável."""
    if not doc:
        return None
    serialized = {}
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            if key == '_id':
                serialized['id'] = str(value)
            else:
                serialized[key] = str(value)
        elif isinstance(value, datetime):
            serialized[key] = value.isoformat()
        else:
            serialized[key] = value
    return serialized

# ... (O restante das funções auxiliares, processadores de contexto e rotas principais permanecem os mesmos)

# --- Rotas Principais, Login, Logout, Dashboard, etc. ---
# (Código existente omitido para brevidade)
@main.route('/')
def welcome():
    news_items = [serialize_doc(item) for item in pymongo.db.news.find().sort('publication_date', DESCENDING).limit(5)]
    event_items = [serialize_doc(item) for item in pymongo.db.events.find({'event_date': {'$gte': datetime.now()}}).sort('event_date', ASCENDING).limit(5)]
    return render_template('welcome.html', news=news_items, events=event_items)

# ... (rotas de login, logout, etc.)

# --- Solicitações de Acesso ---

@main.route('/sistemas/solicitacoes', methods=['GET', 'POST'])
@login_required
def sistemas_solicitacoes():
    if request.method == 'POST':
        new_request_doc = {
            'user_id': ObjectId(current_user.id),
            'username': current_user.username,
            'sistema': request.form.get('sistema'),
            'justificativa': request.form.get('justificativa'),
            'status': 'Pendente',
            'requested_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        pymongo.db.access_requests.insert_one(new_request_doc)
        flash('Sua solicitação de acesso foi enviada com sucesso!', 'success')
        return redirect(url_for('main.sistemas_acessos')) # Redireciona para a nova página de acompanhamento
    return render_template('sistemas_solicitacoes.html')

# NOVA ROTA ADICIONADA
@main.route('/sistemas/acessos')
@login_required
def sistemas_acessos():
    """Página para o usuário ver o status de suas próprias solicitações."""
    user_requests_cursor = pymongo.db.access_requests.find(
        {'user_id': ObjectId(current_user.id)}
    ).sort('requested_at', DESCENDING)
    
    user_requests = list(user_requests_cursor) # Converte o cursor para uma lista para passar ao template
    
    return render_template('sistemas_acessos.html', requests=user_requests)

@main.route('/administracao/solicitacoes')
@login_required
@group_required('Administração')
def administracao_solicitacoes():
    requests_cursor = pymongo.db.access_requests.find().sort('requested_at', DESCENDING)
    page = request.args.get('page', 1, type=int)
    per_page = 10
    requests_list = [serialize_doc(r) for r in requests_cursor.skip((page - 1) * per_page).limit(per_page)]
    total_requests = pymongo.db.access_requests.count_documents({})
    return render_template('admin_requests.html', requests=requests_list, page=page, per_page=per_page, total=total_requests)

@main.route('/api/requests/<string:request_id>', methods=['PUT'])
@login_required
@group_required('Administração')
def update_request_status(request_id):
    data = request.json
    status = data.get('status')
    req_obj_id = ObjectId(request_id)

    update_result = pymongo.db.access_requests.find_one_and_update(
        {'_id': req_obj_id},
        {'$set': {'status': status, 'admin_notes': data.get('admin_notes'), 'updated_at': datetime.utcnow()}},
        return_document=True
    )
    if not update_result:
        return jsonify(status='error', message='Solicitação não encontrada.'), 404

    # Cria notificação para o usuário
    notification_message = f"Sua solicitação para '{update_result['sistema']}' foi atualizada para: {status}."
    pymongo.db.notifications.insert_one({
        'user_id': update_result['user_id'],
        'message': notification_message,
        'link': url_for('main.sistemas_acessos'), # Esta linha agora funciona!
        'is_read': False,
        'created_at': datetime.utcnow()
    })
    return jsonify(status='success', message='Solicitação atualizada.')

# --- O restante do arquivo (APIs, admin, etc.) permanece o mesmo ---
# ...
