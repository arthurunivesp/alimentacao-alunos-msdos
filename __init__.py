from flask import Flask
from jinja2 import Environment
from datetime import datetime
import os

# ✅ Corrige erro do Matplotlib no Vercel
os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib'  # Diretório temporário para evitar erro no Vercel

app = Flask(__name__)
app.secret_key = 'minha_chave_secreta_123'  # Defina uma chave secreta
app.config['SESSION_TYPE'] = 'filesystem'  # Garante o armazenamento correto da sessão

# ✅ Corrige erro de arquivos temporários do ReportLab
os.environ["HOME"] = "/tmp"

# 🔹 Filtro para timestamp (evita cache de imagens)
def timestamp_filter(value):
    return int(datetime.now().timestamp())

app.jinja_env.filters['timestamp'] = timestamp_filter

# ✅ Importação direta do blueprint (sem condição)
from routes import main_bp
app.register_blueprint(main_bp)

if __name__ == '__main__':
    app.run(debug=True)

app = app  # ✅ Exporta a aplicação para Vercel
