
import os
from flask import Flask, send_from_directory, render_template
from src.steam_tables.routes import steam_tables_bp  # Corregido: el nombre es steam_tables_bp
from src.steam_tables.steam_calculator import POINT_DEFINITIONS

# --- Configuración de la Aplicación con Rutas Absolutas ---
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__,
            template_folder=os.path.join(basedir, 'src/steam_tables/templates'),
            static_folder=os.path.join(basedir, 'src/static'))

# Se registra el blueprint con el nombre de variable correcto
app.register_blueprint(steam_tables_bp, url_prefix='/steam') # Corregido: el nombre es steam_tables_bp


# --- Rutas Principales ---

@app.route('/')
def index():
    """
    Renderiza la plantilla principal de la calculadora en la ruta raíz.
    """
    initial_cycle_data = {
        p_id: {'desc': p_data['desc'], 'p': '', 't': '', 'h': '', 's': '', 'x': ''}
        for p_id, p_data in POINT_DEFINITIONS.items()
    }
    return render_template('steam_tables.html',
                           cycle_data=initial_cycle_data,
                           params={},
                           point_definitions=POINT_DEFINITIONS)

# --- Rutas para archivos de la PWA (Progressive Web App) ---

@app.route('/service-worker.js')
def serve_sw():
    return send_from_directory(os.path.join(basedir, 'src'), 'service-worker.js')

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory(os.path.join(basedir, 'src'), 'manifest.json')