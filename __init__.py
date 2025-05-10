from flask import Flask
from jinja2 import Environment
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'minha_chave_secreta_123'  # Defina uma chave secreta
app.config['SESSION_TYPE'] = 'filesystem'  # Garante o armazenamento correto da sessão

# Filtro para timestamp (evita cache de imagens)
def timestamp_filter(value):
    return int(datetime.now().timestamp())

app.jinja_env.filters['timestamp'] = timestamp_filter

# Importação direta do blueprint (sem condição)
from routes import main_bp
app.register_blueprint(main_bp)

if __name__ == '__main__':
    app.run(debug=True)

app = app  # Exporta a aplicação para Vercel
