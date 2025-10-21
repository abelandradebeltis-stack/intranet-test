
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
            # Converte ObjectId para string. Se a chave for '_id', cria uma chave 'id'.
            if key == '_id':
                serialized['id'] = str(value)
            else:
                serialized[key] = str(value)
        elif isinstance(value, datetime):
            serialized[key] = value.isoformat()
        else:
            serialized[key] = value
    return serialized

def save_image(file, upload_folder):
    """Salva um arquivo de imagem e retorna seu caminho relativo."""
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        upload_path = os.path.join(current_app.root_path, 'static', upload_folder)
        os.makedirs(upload_path, exist_ok=True)
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        return os.path.join(upload_folder, filename).replace('\\', '/')
    return None

# --- Processadores de Contexto ---

@main.context_processor
def inject_user_groups():
    user_groups = set()
    if current_user.is_authenticated:
        group_ids = current_user.user_doc.get('groups', [])
        if group_ids:
            groups_cursor = pymongo.db.groups.find({'_id': {'$in': group_ids}}, {'name': 1})
            user_groups = {group['name'] for group in groups_cursor}
    return dict(user_groups=user_groups)

# --- Rotas Principais ---

@main.route('/')
def welcome():
    news_items = [serialize_doc(item) for item in pymongo.db.news.find().sort('publication_date', DESCENDING).limit(5)]
    event_items = [serialize_doc(item) for item in pymongo.db.events.find({'event_date': {'$gte': datetime.now()}}).sort('event_date', ASCENDING).limit(5)]
    return render_template('welcome.html', news=news_items, events=event_items)

@main.route('/login', methods=['GET', 'POST'])
def login():
    # ... (código de login já migrado) ...
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.welcome'))

@main.route('/dashboard')
@login_required
def dashboard():
    # ... (código do dashboard já migrado) ...
    return render_template('index.html', user=current_user.username, pending_requests=[])

# --- Rotas de Administração ---
@main.route('/administracao')
@login_required
@group_required('Administração')
def administracao():
    return render_template('admin_dashboard.html')

@main.route('/administracao/usuarios')
@login_required
@group_required('Administração')
def administracao_usuarios():
    return render_template('admin_users.html')

# --- API de Usuários (Já Migrada) ---
# GET /api/users, POST /api/users/<id>/toggle/<status>, POST /api/users/<id>/unlock
# ... (código da API de usuários já migrado) ...

# --- API de Grupos (Migração Completa) ---

@main.route('/api/groups', methods=['GET'])
@login_required
@group_required('Administração')
def get_groups_api():
    groups_cursor = pymongo.db.groups.find({'name': {'$ne': '_acesso_total_'}}).sort('name', ASCENDING)
    groups = [serialize_doc(g) for g in groups_cursor]
    return jsonify(groups=groups)

@main.route('/api/groups', methods=['POST'])
@login_required
@group_required('Administração')
def create_group_api():
    data = request.json
    name = data.get('name')
    if not name or pymongo.db.groups.find_one({'name': name}):
        return jsonify(status='error', message='Nome de grupo inválido ou já existente.'), 400
    
    new_group = {'name': name}
    result = pymongo.db.groups.insert_one(new_group)
    created_group = pymongo.db.groups.find_one({'_id': result.inserted_id})
    return jsonify(status='success', message='Grupo criado.', group=serialize_doc(created_group))

@main.route('/api/groups/<string:group_id>', methods=['DELETE'])
@login_required
@group_required('Administração')
def delete_group_api(group_id):
    group_obj_id = ObjectId(group_id)
    group = pymongo.db.groups.find_one({'_id': group_obj_id})
    if not group or group.get('name') == '_acesso_total_':
        return jsonify(status='error', message='Grupo não encontrado ou não pode ser excluído.'), 404

    # Remove o grupo de todos os usuários que o possuem
    pymongo.db.users.update_many({}, {'$pull': {'groups': group_obj_id}})
    pymongo.db.groups.delete_one({'_id': group_obj_id})
    return jsonify(status='success', message='Grupo excluído.')

# --- Publicações (Notícias e Eventos) ---

@main.route('/administracao/publicacoes')
@login_required
@group_required('Marketing')
def administracao_publicacoes():
    news_items = [serialize_doc(item) for item in pymongo.db.news.find().sort('publication_date', DESCENDING)]
    event_items = [serialize_doc(item) for item in pymongo.db.events.find().sort('event_date', DESCENDING)]
    return render_template('publicacoes_administracao.html', news_items=news_items, event_items=event_items)

@main.route('/marketing/noticias/publicar', methods=['GET', 'POST'])
@login_required
@group_required('Marketing')
def noticias_publicar():
    if request.method == 'POST':
        # ... (lógica de publicação de notícias migrada)
        flash('Notícia publicada com sucesso!', 'success')
        return redirect(url_for('main.administracao_publicacoes'))
    return render_template('marketing_publicacoes.html')

# ... (Adicionar rotas de editar e deletar para notícias e eventos, seguindo o padrão) ...

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
        return redirect(url_for('main.sistemas_solicitacoes'))
    return render_template('sistemas_solicitacoes.html')

@main.route('/administracao/solicitacoes')
@login_required
@group_required('Administração')
def administracao_solicitacoes():
    requests_cursor = pymongo.db.access_requests.find().sort('requested_at', DESCENDING)
    # Simples paginação manual (para uma solução robusta, use uma biblioteca)
    page = request.args.get('page', 1, type=int)
    per_page = 10
    requests_list = [serialize_doc(r) for r in requests_cursor.skip((page - 1) * per_page).limit(per_page)]
    # Para a paginação funcionar, você precisará passar o total de documentos para o template
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
        'link': url_for('main.sistemas_acessos'),
        'is_read': False,
        'created_at': datetime.utcnow()
    })
    return jsonify(status='success', message='Solicitação atualizada.')

# --- O restante das rotas (estáticas e outras já migradas) ---
# ...
