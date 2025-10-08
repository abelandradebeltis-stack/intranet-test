from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from .models import News
from . import db
from .decorators import group_required
import os
from werkzeug.utils import secure_filename
from flask import current_app

marketing_bp = Blueprint('marketing', __name__, url_prefix='/marketing')

def save_image(file):
    if not file or file.filename == '':
        return None
    filename = secure_filename(file.filename)
    # Garante um nome de arquivo único
    unique_filename = f"{current_user.id}_{os.urandom(8).hex()}_{filename}"
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, unique_filename)
    
    # Cria o diretório se ele não existir
    os.makedirs(upload_folder, exist_ok=True)
    
    file.save(file_path)
    # Retorna o caminho relativo para ser salvo no DB
    return os.path.join('uploads', unique_filename)

@marketing_bp.route('/administracao')
@login_required
@group_required('Marketing')
def administracao():
    return render_template('marketing_administracao.html')

@marketing_bp.route('/publicar', methods=['GET', 'POST'])
@login_required
@group_required('Marketing')
def publicar():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image_file = request.files.get('image')

        if title and content:
            image_url = save_image(image_file)
            new_news = News(title=title, content=content, image_url=image_url, author_id=current_user.id)
            db.session.add(new_news)
            db.session.commit()
            flash('Notícia publicada com sucesso!', 'success')
            return redirect(url_for('marketing.administracao'))
    return render_template('marketing_publicacoes.html')

@marketing_bp.route('/editar/<int:news_id>', methods=['GET', 'POST'])
@login_required
@group_required('Marketing')
def editar(news_id):
    news_item = News.query.get_or_404(news_id)
    if request.method == 'POST':
        news_item.title = request.form['title']
        news_item.content = request.form['content']
        image_file = request.files.get('image')
        if image_file:
            # Deleta a imagem antiga se uma nova for enviada
            if news_item.image_url:
                old_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(news_item.image_url))
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            news_item.image_url = save_image(image_file)
        
        db.session.commit()
        flash('Notícia atualizada com sucesso!', 'success')
        return redirect(url_for('marketing.administracao'))
    return render_template('marketing_publicacoes.html', news_item=news_item)

@marketing_bp.route('/deletar/<int:news_id>', methods=['POST'])
@login_required
@group_required('Marketing')
def deletar(news_id):
    news_item = News.query.get_or_404(news_id)
    if news_item.image_url:
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(news_item.image_url))
        if os.path.exists(image_path):
            os.remove(image_path)
    db.session.delete(news_item)
    db.session.commit()
    return jsonify(status='success', message='Notícia deletada com sucesso!')

@marketing_bp.route('/api/news', methods=['GET'], endpoint='get_news_api')
@login_required
@group_required('Marketing')
def get_news_api():
    news_items = News.query.order_by(News.publication_date.desc()).all()
    return jsonify(news=[news.to_dict() for news in news_items])
