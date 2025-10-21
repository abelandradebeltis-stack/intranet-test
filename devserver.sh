#!/bin/bash
set -e

# Opcional: Carregar variáveis de ambiente de um arquivo .env se estiver usando um
if [ -f .env ]; then
  export $(cat .env | sed 's/#.*//g' | xargs)
fi

export FLASK_APP=app:create_app

# Ativar ambiente virtual
source .venv/bin/activate

# Não há mais migrações de banco de dados para rodar com o MongoDB desta forma.

# O comando create-admin foi reescrito para funcionar com o MongoDB.
# Ele irá verificar se o admin já existe antes de tentar criar.
echo "Verificando/Criando usuário admin..."
flask create-admin

# Não há mais o comando grant-full-access. A lógica de grupo é diferente agora.

echo "Iniciando o servidor Flask..."
flask run --host=0.0.0.0 --port=8085 --debug
