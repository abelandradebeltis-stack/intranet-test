from functools import wraps
from flask import redirect, url_for, flash, render_template, request
from flask_login import current_user

def group_required(*group_names):
    """ 
    Decorator que restringe o acesso a uma rota para usuários em grupos específicos.
    O acesso é sempre concedido se o usuário pertencer ao grupo '_acesso_total_'.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Você precisa estar logado para acessar esta página.", "warning")
                return redirect(url_for('main.login', next=request.url))

            user_group_names = {group.name for group in current_user.groups}

            if '_acesso_total_' in user_group_names:
                return f(*args, **kwargs)

            required_groups = set(group_names)
            if not user_group_names.intersection(required_groups):
                return render_template('unauthorized.html'), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
