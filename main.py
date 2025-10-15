
import os
from flask import Flask, send_from_directory, render_template
from src.steam_tables.routes import steam_tables_blueprint
from src.steam_tables.steam_calculator import POINT_DEFINITIONS

# --- Configuración de la Aplicación con Rutas Absolutas ---
# Se obtiene la ruta absoluta del directorio donde se encuentra este archivo (main.py)
basedir = os.path.abspath(os.path.dirname(__file__))

# Se crean las rutas absolutas para las carpetas de plantillas y estáticos
# Esto garantiza que la app encuentre los archivos sin importar desde dónde se ejecute.
app = Flask(__name__,
            template_folder=os.path.join(basedir, 'src/steam_tables/templates'),
            static_folder=os.path.join(basedir, 'src/static'))

# Se registra el blueprint que contiene la lógica de cálculo.
app.register_blueprint(steam_tables_blueprint, url_prefix='/steam')


# --- Rutas Principales ---

@app.route('/')
def index():
    """
    Renderiza la plantilla principal de la calculadora en la ruta raíz.
    Crea un diccionario de ciclo vacío para que la plantilla se renderice
    correctamente la primera vez, sin necesidad de recibir datos de un formulario.
    """
    initial_cycle_data = {
        p_id: {'desc': p_data['desc'], 'p': '', 't': '', 'h': '', 's': '', 'x': ''}
        for p_id, p_data in POINT_DEFINITIONS.items()
    }
    # Se pasan todos los datos que la plantilla podría necesitar.
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
