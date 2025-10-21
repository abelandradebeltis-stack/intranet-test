
import os
from flask import Flask
from flask_login import LoginManager, current_user
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from bson.objectid import ObjectId

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Instâncias das extensões
# Vamos inicializar pymongo depois, dentro de create_app
pymongo = PyMongo()
login_manager = LoginManager()
login_manager.login_view = 'main.login'

def create_app():
    app = Flask(__name__)

    # --- Configuração da Aplicação ---
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # --- Configuração do MongoDB ---
    # A URL de conexão deve ser armazenada em uma variável de ambiente
    app.config["MONGO_URI"] = os.environ.get('MONGO_URI')
    if not app.config["MONGO_URI"]:
        raise RuntimeError("A variável de ambiente MONGO_URI não foi definida!")

    # Inicializa as extensões com a app
    pymongo.init_app(app)
    login_manager.init_app(app)

    # --- Configuração do LoginManager ---
    from .models import User # Vamos reescrever este modelo a seguir

    @login_manager.user_loader
    def load_user(user_id):
        # MongoDB usa ObjectIds, não inteiros.
        user_doc = pymongo.db.users.find_one({'_id': ObjectId(user_id)})
        if user_doc:
            return User(user_doc)
        return None

    # --- Registro de Blueprints ---
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # --- Comandos CLI (precisarão ser reescritos) ---
    @app.cli.command("create-admin")
    def create_admin_command():
        """Cria o usuário admin padrão no MongoDB."""
        if not pymongo.db.users.find_one({'username': 'admin'}):
            print("Criando o usuário admin...")
            admin_user = {
                "username": "admin",
                "password": generate_password_hash('admin', method='pbkdf2:sha256'),
                # Adicione outros campos padrão se necessário
                "groups": []
            }
            pymongo.db.users.insert_one(admin_user)
            print("Usuário 'admin' criado com sucesso.")
        else:
            print("Usuário 'admin' já existe.")

    # Outros comandos CLI e context processors serão adaptados depois...

    return app
