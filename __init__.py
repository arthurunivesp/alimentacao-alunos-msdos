from flask import Flask
from .routes import main_bp

app = Flask(__name__)
app.secret_key = "chave_secreta_demo_msdos"
app.register_blueprint(main_bp)

if __name__ == '__main__':
    app.run(debug=True)