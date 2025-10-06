import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from my_intranet.app import create_app, db
from my_intranet.app.models import User, Group

app = create_app()

with app.app_context():
    user = User.query.filter_by(username='admin').first()
    if not user:
        print("Usuário 'admin' não encontrado.")
        exit()

    group = Group.query.filter_by(name='_acesso_total_').first()
    if not group:
        print("Grupo '_acesso_total_' não encontrado. Criando...")
        group = Group(name='_acesso_total_')
        db.session.add(group)

    if group in user.groups:
        print("Usuário 'admin' já está no grupo '_acesso_total_'.")
    else:
        user.groups.append(group)
        db.session.commit()
        print("Usuário 'admin' adicionado ao grupo '_acesso_total_' com sucesso.")
