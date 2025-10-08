import os
import sys

# Adiciona o caminho do projeto ao sys.path para permitir importações relativas
project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'app'))
sys.path.insert(0, project_path)

from app import create_app, db

# Cria uma instância da aplicação Flask
# Isso é necessário para que o contexto da aplicação esteja disponível
app = create_app()

# O 'app_context' garante que a aplicação Flask esteja ciente da operação atual.
# É uma boa prática usar o contexto ao interagir com extensões da aplicação, como o SQLAlchemy.
with app.app_context():
    print("Iniciando a criação do banco de dados...")
    
    # Apaga todas as tabelas existentes (se houver)
    # Útil para um reset limpo durante o desenvolvimento
    db.drop_all()
    print("Tabelas existentes foram removidas.")

    # Cria todas as tabelas definidas nos seus modelos (models.py)
    db.create_all()
    print("Novas tabelas foram criadas com base nos modelos.")

    print("Banco de dados inicializado com sucesso!")
