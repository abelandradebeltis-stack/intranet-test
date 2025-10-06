# Este arquivo serve como o ponto de entrada para a Vercel.
# Ele importa a fábrica de aplicativos e a expõe como uma variável 'app'.

from my_intranet.app import create_app

app = create_app()
