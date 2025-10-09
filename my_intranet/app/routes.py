
import os
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from .models import User, Group, News, Event
from . import db
from .decorators import group_required
from datetime import datetime
from werkzeug.utils import secure_filename

main = Blueprint('main', __name__)


@main.context_processor
def inject_user_groups():
    """
    Injects the current user's group names into the template context.
    This allows checking for group membership directly in Jinja2 templates.
    e.g., {% if 'Marketing' in user_groups %}
    """
    if current_user.is_authenticated:
        user_groups = {group.name for group in current_user.groups}
        return dict(user_groups=user_groups)
    return dict(user_groups=set()) # Return an empty set for anonymous users


# --- Função Auxiliar para Salvar Imagens ---
def save_image(file, upload_folder):
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        upload_path = os.path.join(current_app.root_path, 'static', upload_folder)
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        return os.path.join(upload_folder, filename).replace('\\', '/')
    return None


# --- Rotas Públicas e de Autenticação ---

@main.route('/')
def welcome():
    news_items = News.query.order_by(News.publication_date.desc()).limit(5).all()
    event_items = Event.query.filter(Event.event_date >= datetime.now()).order_by(Event.event_date.asc()).limit(5).all()
    return render_template('welcome.html', news=news_items, events=event_items)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash('Usuário ou senha inválidos. Por favor, tente novamente.', 'error')
        elif user.is_blocked:
            flash('Esta conta foi bloqueada por um administrador.', 'error')
        elif user.is_suspended:
            flash('Esta conta está temporariamente suspensa.', 'error')
        else:
            login_user(user)
            return redirect(url_for('main.dashboard'))
            
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.welcome'))

# --- Rotas Internas Gerais ---

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('index.html', user=current_user.username)

@main.route('/ramais')
@login_required
def ramais():
    return render_template('ramais.html')

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

@main.route('/administracao/publicacoes')
@login_required
@group_required('Marketing')
def administracao_publicacoes():
    news_items = News.query.order_by(News.publication_date.desc()).all()
    event_items = Event.query.order_by(Event.event_date.desc()).all()
    return render_template('publicacoes_administracao.html', news_items=news_items, event_items=event_items)

# --- API de Administração ---

def serialize_group(group):
    return {
        'id': group.id,
        'name': group.name,
        'children': [serialize_group(child) for child in group.children]
    }

@main.route('/api/groups', methods=['GET'], endpoint='get_groups_api')
@login_required
@group_required('Administração')
def get_groups_api():
    groups = Group.query.filter(Group.name != '_acesso_total_', Group.parent_id.is_(None)).all()
    return jsonify(groups=[serialize_group(g) for g in groups])

@main.route('/api/groups', methods=['POST'], endpoint='create_group_api')
@login_required
@group_required('Administração')
def create_group_api():
    data = request.json
    name = data.get('name')
    parent_id = data.get('parent_id')

    if not name or Group.query.filter_by(name=name).first():
        return jsonify(status='error', message='Nome de grupo inválido ou já existente.'), 400
    
    new_group = Group(name=name, parent_id=parent_id)
    db.session.add(new_group)
    db.session.commit()
    return jsonify(status='success', message='Grupo criado.', group=serialize_group(new_group))

@main.route('/api/groups/<int:group_id>', methods=['PUT'], endpoint='update_group_api')
@login_required
@group_required('Administração')
def update_group_api(group_id):
    group = Group.query.get_or_404(group_id)
    data = request.json
    name = data.get('name')

    if not name or (name != group.name and Group.query.filter_by(name=name).first()):
        return jsonify(status='error', message='Nome de grupo inválido ou já existente.'), 400

    group.name = name
    db.session.commit()
    return jsonify(status='success', message='Grupo atualizado.')

@main.route('/api/groups/<int:group_id>', methods=['DELETE'], endpoint='delete_group_api')
@login_required
@group_required('Administração')
def delete_group_api(group_id):
    group = Group.query.get_or_404(group_id)
    if group.name == '_acesso_total_':
         return jsonify(status='error', message='Este grupo não pode ser excluído.'), 403
    
    db.session.delete(group)
    db.session.commit()
    return jsonify(status='success', message='Grupo excluído.')

@main.route('/api/groups/<int:group_id>/users', methods=['GET'], endpoint='get_users_by_group_api')
@login_required
@group_required('Administração')
def get_users_by_group_api(group_id):
    group = Group.query.get_or_404(group_id)
    users = group.users
    return jsonify(users=[u.to_dict() for u in users])

@main.route('/api/users', methods=['GET'], endpoint='get_all_users_api')
@login_required
@group_required('Administração')
def get_all_users_api():
    users = User.query.all()
    return jsonify(users=[u.to_dict() for u in users])

@main.route('/api/users', methods=['POST'], endpoint='create_user_api')
@login_required
@group_required('Administração')
def create_user_api():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    group_ids = data.get('group_ids', [])

    if not username or not password:
        return jsonify(status='error', message='Dados incompletos (usuário e senha são obrigatórios).'), 400

    if User.query.filter_by(username=username).first():
        return jsonify(status='error', message='Nome de usuário já existe.'), 400

    new_user = User(username=username)
    new_user.set_password(password)

    # Buscar grupos padrão
    default_group_names = ['Inicio', 'Contato', 'RH Externo']
    default_groups = Group.query.filter(Group.name.in_(default_group_names)).all()
    
    # Unir IDs de grupos selecionados com os padrões (usando set para evitar duplicatas)
    final_group_ids = set(group_ids) | {g.id for g in default_groups}

    # Associar grupos ao novo usuário
    if final_group_ids:
        groups = Group.query.filter(Group.id.in_(list(final_group_ids))).all()
        if len(groups) != len(final_group_ids):
             return jsonify(status='error', message='Um ou mais grupos (incluindo padrões) não foram encontrados. Execute a inicialização do DB.'), 500
        new_user.groups = groups
    
    db.session.add(new_user)
    db.session.commit()
    return jsonify(status='success', message='Usuário criado com acesso padrão.', user=new_user.to_dict())

@main.route('/api/users/<int:user_id>', methods=['PUT'], endpoint='update_user_api')
@login_required
@group_required('Administração')
def update_user_api(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json
    username = data.get('username')
    password = data.get('password')
    group_ids = data.get('group_ids')

    if not username:
        return jsonify(status='error', message='Nome de usuário é obrigatório.'), 400

    if username != user.username and User.query.filter_by(username=username).first():
        return jsonify(status='error', message='Nome de usuário já existe.'), 400

    user.username = username
    if password:
        user.set_password(password)
        
    if group_ids is not None:
        # Lógica para proteger o grupo '_acesso_total_' do admin
        if user.username == 'admin':
            acesso_total_group = Group.query.filter_by(name='_acesso_total_').first()
            if acesso_total_group:
                # Garante que o ID do grupo de acesso total esteja na lista
                if acesso_total_group.id not in group_ids:
                    group_ids.append(acesso_total_group.id)

        groups = Group.query.filter(Group.id.in_(group_ids)).all()
        if len(groups) != len(set(group_ids)):
            return jsonify(status='error', message='Um ou mais IDs de grupo são inválidos.'), 404
        user.groups = groups

    db.session.commit()
    return jsonify(status='success', message='Usuário atualizado.', user=user.to_dict())

@main.route('/api/users/<int:user_id>/groups', methods=['GET'], endpoint='get_user_groups_api')
@login_required
@group_required('Administração')
def get_user_groups_api(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(group_ids=[g.id for g in user.groups])

@main.route('/api/users/<int:user_id>', methods=['DELETE'], endpoint='delete_user_api')
@login_required
@group_required('Administração')
def delete_user_api(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify(status='success', message='Usuário excluído.')

@main.route('/api/users/<int:user_id>/<string:status_type>', methods=['POST'], endpoint='toggle_user_status_api')
@login_required
@group_required('Administração')
def toggle_user_status_api(user_id, status_type):
    user = User.query.get_or_404(user_id)
    if status_type == 'suspend':
        user.is_suspended = not user.is_suspended
    elif status_type == 'block':
        user.is_blocked = not user.is_blocked
    else:
        return jsonify(status='error', message='Tipo de status inválido.'), 400
    
    db.session.commit()
    return jsonify(status='success', message=f'Status do usuário atualizado.', user=user.to_dict())

# --- Notícias ---
@main.route('/marketing/noticias/publicar', methods=['GET', 'POST'])
@login_required
@group_required('Marketing')
def noticias_publicar():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image_file = request.files.get('image')

        if title and content:
            image_url = save_image(image_file, 'uploads/news_images')
            new_news = News(title=title, content=content, image_url=image_url, author_id=current_user.id)
            db.session.add(new_news)
            db.session.commit()
            flash('Notícia publicada com sucesso!', 'success')
            return redirect(url_for('main.administracao_publicacoes'))

    return render_template('marketing_publicacoes.html')


@main.route('/marketing/noticias/editar/<int:news_id>', methods=['GET', 'POST'])
@login_required
@group_required('Marketing')
def noticias_editar(news_id):
    news_item = News.query.get_or_404(news_id)
    if request.method == 'POST':
        news_item.title = request.form['title']
        news_item.content = request.form['content']
        image_file = request.files.get('image')

        if image_file:
            image_url = save_image(image_file, 'uploads/news_images')
            news_item.image_url = image_url

        db.session.commit()
        flash('Notícia atualizada com sucesso!', 'success')
        return redirect(url_for('main.administracao_publicacoes'))

    return render_template('marketing_publicacoes.html', news_item=news_item)


@main.route('/marketing/noticias/deletar/<int:news_id>', methods=['POST'])
@login_required
@group_required('Marketing')
def noticias_deletar(news_id):
    news_item = News.query.get_or_404(news_id)
    db.session.delete(news_item)
    db.session.commit()
    flash('Notícia deletada com sucesso!', 'success')
    return redirect(url_for('main.administracao_publicacoes'))

# --- Eventos ---
@main.route('/marketing/eventos/publicar', methods=['GET', 'POST'])
@login_required
@group_required('Marketing')
def eventos_publicar():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        event_date_str = request.form['event_date']
        image_file = request.files.get('image')

        if title and description and event_date_str:
            event_date = datetime.strptime(event_date_str, '%Y-%m-%dT%H:%M')
            image_url = save_image(image_file, 'uploads/event_images')
            new_event = Event(title=title, description=description, event_date=event_date, image_url=image_url, creator_id=current_user.id)
            db.session.add(new_event)
            db.session.commit()
            flash('Evento publicado com sucesso!', 'success')
            return redirect(url_for('main.administracao_publicacoes'))

    return render_template('eventos_publicacoes.html')


@main.route('/marketing/eventos/editar/<int:event_id>', methods=['GET', 'POST'])
@login_required
@group_required('Marketing')
def eventos_editar(event_id):
    event_item = Event.query.get_or_404(event_id)
    if request.method == 'POST':
        event_item.title = request.form['title']
        event_item.description = request.form['description']
        event_date_str = request.form['event_date']
        event_item.event_date = datetime.strptime(event_date_str, '%Y-%m-%dT%H:%M')
        image_file = request.files.get('image')

        if image_file:
            image_url = save_image(image_file, 'uploads/event_images')
            event_item.image_url = image_url

        db.session.commit()
        flash('Evento atualizado com sucesso!', 'success')
        return redirect(url_for('main.administracao_publicacoes'))

    return render_template('eventos_publicacoes.html', event_item=event_item)


@main.route('/marketing/eventos/deletar/<int:event_id>', methods=['POST'])
@login_required
@group_required('Marketing')
def eventos_deletar(event_id):
    event_item = Event.query.get_or_404(event_id)
    db.session.delete(event_item)
    db.session.commit()
    flash('Evento deletado com sucesso!', 'success')
    return redirect(url_for('main.administracao_publicacoes'))
