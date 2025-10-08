Depois de rodar o scaffold:
1) cd <project>
2) export FLASK_APP=app.py
3) docker-compose up --build
4) dentro do container web, rode: flask db init; flask db migrate; flask db upgrade
OBS: Você pode automatizar migrations/comandos no entrypoint.
