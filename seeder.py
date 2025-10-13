
import click
from flask.cli import with_appcontext
from .app import db
from .app.models import Group, User

# Estrutura de Grupos e Subgrupos baseada nos templates
MENU_STRUCTURE = {
    "Inicio": [], 
    "Administrativo": ["Clientes", "Diretoria", "Gerencia"],
    "Financeiro": ["Administracao", "Contas a Pagar", "Contas a Receber", "Operacoes", "Relatorios"],
    "Marketing": ["Campanhas", "Publicacoes Marketing", "Clientes Marketing"],
    "RH": ["Administracao RH", "Avaliacoes", "Beneficios", "Folha de Pagamento", "Recrutamento"],
    "Sistemas": ["Acessos", "Geral", "Solicitacoes"],
    "TI": ["Administracao TI", "Chamados", "Infraestrutura", "Relatorios TI", "Seguranca"],
    "Eventos": ["Agendamentos", "Publicacoes Eventos"],
    "Publicacoes": ["Administracao Publicacoes"],
}

@click.command('seed')
@with_appcontext
def seed():
    """Popula o banco de dados com grupos e o usuário admin."""
    print("Iniciando o processo de seeding...")
    
    all_groups = []

    # Criar grupos e subgrupos
    for parent_name, children in MENU_STRUCTURE.items():
        parent_group = Group.query.filter_by(name=parent_name).first()
        if not parent_group:
            parent_group = Group(name=parent_name)
            db.session.add(parent_group)
            print(f"Grupo pai criado: {parent_name}")
        all_groups.append(parent_group)

        for child_name in children:
            # Correção: Busca o grupo filho pelo nome. Se não existir, cria.
            # Isso evita a violação da constraint UNIQUE no nome do grupo.
            child_group = Group.query.filter_by(name=child_name).first()
            if not child_group:
                child_group = Group(name=child_name, parent=parent_group)
                db.session.add(child_group)
                print(f"  - Subgrupo criado: {child_name} (filho de {parent_name})")
            else:
                # Se o grupo já existe, apenas garante a associação.
                if not child_group.parent:
                    child_group.parent = parent_group
                print(f"  - Subgrupo existente '{child_name}' associado a {parent_name}")
            all_groups.append(child_group)

    # Garantir a criação e acesso total do Admin
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(username='admin', is_admin=True)
        admin_user.set_password('admin') # Defina uma senha padrão segura
        db.session.add(admin_user)
        print("Usuário 'admin' criado com senha padrão.")

    # Associar TODOS os grupos ao admin
    admin_user.groups = list(set(all_groups)) # Usa set para evitar duplicatas
    
    db.session.commit()
    print("Processo de seeding concluído.")
    print("Usuário 'admin' agora tem acesso a todos os grupos criados.")

def init_app(app):
    """Registra o comando no Flask app."""
    app.cli.add_command(seed)
