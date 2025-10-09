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
from my_intranet.app.models import User, Group, AccessRequest

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
    administrativo = Group(name='Administração')
    financeiro = Group(name='Financeiro')
    rh = Group(name='Recursos Humanos')
    ti = Group(name='TI')
    marketing = Group(name='Marketing')
    sistemas = Group(name='Sistemas')

    # Grupos que serão padrão para novos usuários (também principais)
    inicio = Group(name='Inicio')
    contato = Group(name='Contato')
    rh_externo = Group(name='RH Externo')

    db.session.add_all([
        acesso_total, administrativo, financeiro, rh, ti, marketing, sistemas,
        inicio, contato, rh_externo
    ])
    db.session.commit()

    # Criando subgrupos para controle de acesso mais fino
    adm_painel = Group(name='Administração - Painel', parent_id=administrativo.id)
    adm_usuarios = Group(name='Administração - Usuários', parent_id=administrativo.id)
    adm_solicitacoes = Group(name='Administração - Solicitações', parent_id=administrativo.id)
    
    mkt_admin = Group(name='Marketing - Administração', parent_id=marketing.id)
    mkt_noticia = Group(name='Marketing - Publicar Notícia', parent_id=marketing.id)
    mkt_evento = Group(name='Marketing - Publicar Evento', parent_id=marketing.id)

    db.session.add_all([
        adm_painel, adm_usuarios, adm_solicitacoes,
        mkt_admin, mkt_noticia, mkt_evento
    ])
    db.session.commit()
    
    print("Grupos e subgrupos criados.")

    print("Configurando usuário administrador...")
    # Garante que o usuário admin exista
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(username='admin')
        admin_user.set_password('admin')
        db.session.add(admin_user)
        db.session.commit() # Commit para que o usuário tenha um ID
    
    # Busca TODOS os grupos existentes no banco de dados
    all_groups = Group.query.all()
    
    # Garante que o admin seja membro de todos os grupos
    admin_user.groups = list(set(all_groups))
    
    db.session.commit()

    print("Usuário administrador configurado com acesso a TODOS os grupos.")
    print("Banco de dados inicializado com sucesso!")
