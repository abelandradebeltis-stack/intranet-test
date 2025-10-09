'''
Script para inicializar o banco de dados. 

Este script deve ser executado a partir da raiz do projeto (`intranet`)
para garantir que os caminhos de importação sejam resolvidos corretamente.

Uso:
cd /path/to/your/project/intranet
source .venv/bin/activate
python my_intranet/init_db.py
'''
import os
import sys

# Adiciona a raiz do projeto ('intranet') ao sys.path para que as importações absolutas funcionem.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Agora que o caminho está correto, usamos importações absolutas a partir da raiz do projeto.
from my_intranet.app import create_app, db
from my_intranet.app.models import User, Group

# Cria uma instância da aplicação Flask
app = create_app()

with app.app_context():
    print("Iniciando a criação do banco de dados...")
    db.drop_all()
    print("Tabelas existentes foram removidas.")
    db.create_all()
    print("Novas tabelas foram criadas com base nos modelos.")

    print("Criando grupos padrão...")
    # Grupo especial que concede todas as permissões
    acesso_total = Group(name='_acesso_total_')
    
    # Grupos de Departamentos Principais (Raiz)
    administrativo = Group(name='Administrativo')
    financeiro = Group(name='Financeiro')
    rh = Group(name='Recursos Humanos')
    ti = Group(name='TI')
    marketing = Group(name='Marketing')
    eventos = Group(name='Eventos')
    sistemas = Group(name='Sistemas')  # Adicionado para corresponder ao menu

    # Grupos que serão padrão para novos usuários
    inicio = Group(name='Inicio')
    contato = Group(name='Contato')
    rh_externo = Group(name='RH Externo')

    db.session.add_all([
        acesso_total, administrativo, financeiro, rh, ti, marketing, eventos, sistemas,
        inicio, contato, rh_externo
    ])
    db.session.commit()

    # Criando subgrupos (exemplo)
    adm_gerencia = Group(name='Gerência', parent_id=administrativo.id)
    adm_diretoria = Group(name='Diretoria', parent_id=administrativo.id)
    adm_clientes = Group(name='Clientes', parent_id=administrativo.id)
    
    db.session.add_all([adm_gerencia, adm_diretoria, adm_clientes])
    db.session.commit()
    
    print("Grupos e subgrupos criados.")

    print("Configurando usuário administrador...")
    # Garante que o usuário admin exista
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(username='admin')
        admin_user.set_password('admin')
        db.session.add(admin_user)
    
    # Adiciona o admin ao grupo de acesso total
    acesso_total_group = Group.query.filter_by(name='_acesso_total_').first()
    if acesso_total_group and acesso_total_group not in admin_user.groups:
        admin_user.groups.append(acesso_total_group)
    
    db.session.commit()

    print("Usuário administrador configurado com acesso total.")
    print("Banco de dados inicializado com sucesso!")
