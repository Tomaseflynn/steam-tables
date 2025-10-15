
from flask import Flask, send_from_directory, render_template
from src.steam_tables.routes import steam_tables_blueprint

app = Flask(__name__, template_folder='src/steam_tables/templates', static_folder='src')
app.register_blueprint(steam_tables_blueprint, url_prefix='/steam')

# Servir archivos estáticos (service worker, manifest)
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# Ruta principal que renderiza la calculadora
@app.route('/')
def index():
    return render_template('steam_tables.html')
