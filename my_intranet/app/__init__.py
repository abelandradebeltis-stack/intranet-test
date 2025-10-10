from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
import os

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
login_manager.login_view = 'main.login'

def create_app():
    # Usar instance_relative_config=True simplifica o manuseio de caminhos
    app = Flask(__name__, instance_relative_config=True)
    
    # Carrega a configuração a partir do arquivo config.py
    app.config.from_object('my_intranet.app.config.Config')

    # Configurações da aplicação (podem sobrescrever o que foi carregado do config.py)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # Configuração do banco de dados
    db_path = os.path.join(app.instance_path, "app.db")
    database_url = f'sqlite:///{db_path}'
    
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializa as extensões com a app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Importar modelos para que o Flask-Migrate os reconheça
    from . import models

    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

    # Registra o Blueprint com as rotas
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    @app.context_processor
    def inject_notifications():
        if current_user.is_authenticated:
            # Pega as 10 notificações mais recentes para exibição
            notifications = models.Notification.query.filter_by(user_id=current_user.id).order_by(models.Notification.created_at.desc()).limit(10).all()
            # Conta as notificações não lidas
            unread_count = models.Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
            return dict(notifications=notifications, unread_notifications_count=unread_count)
        return dict(notifications=[], unread_notifications_count=0)


    # Adiciona o comando para criar admin
    @app.cli.command("create-admin")
    def create_admin_command():
        """Cria o usuário admin padrão."""
        if not models.User.query.filter_by(username='admin').first():
            print("Criando o usuário admin...")
            admin = models.User(username='admin', password=generate_password_hash('admin', method='pbkdf2:sha256'))
            db.session.add(admin)
            db.session.commit()
            print("Usuário 'admin' criado com sucesso.")
        else:
            print("Usuário 'admin' já existe.")

    @app.cli.command("grant-full-access")
    def grant_full_access_command():
        """Garante que o usuário admin tenha acesso total."""
        admin_user = models.User.query.filter_by(username='admin').first()
        if not admin_user:
            print("Usuário 'admin' não encontrado. Crie o usuário primeiro.")
            return

        access_group = models.Group.query.filter_by(name='_acesso_total_').first()
        if not access_group:
            print("Criando o grupo '_acesso_total_'...")
            access_group = models.Group(name='_acesso_total_')
            db.session.add(access_group)
            db.session.commit()
            print("Grupo '_acesso_total_' criado.")

        if access_group not in admin_user.groups:
            print("Adicionando 'admin' ao grupo '_acesso_total_'...")
            admin_user.groups.append(access_group)
            db.session.commit()
            print("'admin' agora tem acesso total.")
        else:
            print("'admin' já possui acesso total.")

    return app