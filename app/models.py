
from flask_login import UserMixin
from werkzeug.security import check_password_hash

# Não há mais classes db.Model. Em vez disso, criamos uma classe User
# que atua como um invólucro para o documento recuperado do MongoDB para
# torná-lo compatível com o Flask-Login.

class User(UserMixin):
    """
    Uma classe invólucro para documentos de usuário do MongoDB para torná-los
    compatíveis com o Flask-Login.
    """
    def __init__(self, user_doc):
        self.user_doc = user_doc

    @property
    def id(self):
        # O Flask-Login espera que o id seja uma string.
        # O _id do MongoDB é um ObjectId, então nós o convertemos.
        return str(self.user_doc.get('_id'))

    @property
    def username(self):
        return self.user_doc.get('username')

    # Propriedades do Flask-Login
    @property
    def is_active(self):
        # Você pode definir o que "ativo" significa. Por exemplo, não suspenso ou bloqueado.
        return not self.user_doc.get('is_suspended', False) and not self.user_doc.get('is_blocked', False)

    def get_id(self):
        # Este método é exigido pelo Flask-Login.
        return self.id

    def check_password(self, password):
        """Verifica a senha fornecida contra o hash armazenado."""
        stored_password_hash = self.user_doc.get('password')
        if stored_password_hash:
            return check_password_hash(stored_password_hash, password)
        return False

    def is_in_group(self, group_name):
        """
        Verifica se o usuário pertence a um grupo.
        Isso assume que 'groups' é uma lista de nomes de grupos ou IDs de grupos
        armazenados dentro do documento do usuário.
        """
        from app import pymongo
        # Isso assume que o campo 'groups' no documento do usuário armazena ObjectIds para a coleção de grupos.
        group_ids = self.user_doc.get('groups', [])
        group = pymongo.db.groups.find_one({"name": group_name, "_id": {"$in": group_ids}})
        return group is not None

    def to_dict(self):
        """
        Serializa o objeto User para um dicionário, convertendo ObjectId.
        """
        doc = self.user_doc.copy()
        doc['id'] = str(doc.get('_id')) # Converte ObjectId para string para serialização JSON
        
        # Mapeia is_locked para is_login_blocked para compatibilidade com o frontend
        doc['is_login_blocked'] = doc.get('is_locked', False)
        
        # Remove dados sensíveis
        doc.pop('password', None)
        doc.pop('_id', None) # Remove o _id original para evitar redundância
        
        return doc

# Nota: As outras classes (Group, News, Event, etc.) DESAPARECERAM deste arquivo.
# Todas as operações nelas agora serão feitas diretamente no objeto pymongo.db
# no arquivo de rotas (por exemplo, pymongo.db.news.find_one(...)).
# Esta é uma mudança fundamental do padrão ORM.
