
import os
from flask import Blueprint, render_template, request, jsonify, send_from_directory
from .steam_calculator import SteamCycleCalculator, POINT_DEFINITIONS, CalculationCatalog

# Obtener la ruta base del proyecto para servir archivos estáticos de forma segura
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

steam_tables_bp = Blueprint('steam_tables', __name__, template_folder='templates')

# --- RUTAS DE LA API DE CÁLCULO ---

@steam_tables_bp.route('/calculate_point', methods=['POST'])
def calculate_point():
    data = request.get_json()
    point_data = data.get('point_data', {})
    try:
        calculator = SteamCycleCalculator()
        calculated_point = calculator.calculate_single_point(point_data)
        return jsonify({'status': 'success', 'point': calculated_point})
    except Exception as e:
        # Si pyXSteam falla, devolvemos un error 400 (Bad Request)
        error_message = f"Error al calcular el punto: Los valores de entrada son inválidos o no corresponden a un estado termodinámico real. ({str(e)})"
        return jsonify({'status': 'error', 'message': error_message}), 400

@steam_tables_bp.route('/calculate_expansions', methods=['POST'])
def calculate_expansions():
    data = request.get_json()
    try:
        calculator = SteamCycleCalculator()
        # Los datos del ciclo y los rendimientos vienen en el cuerpo de la solicitud
        result = calculator.calculate_expansions_and_efficiencies(
            cycle_data=data.get('cycle_data', {}),
            eta_hp=data.get('eta_hp'),
            eta_lp=data.get('eta_lp')
        )
        return jsonify({'status': 'success', **result})
    except Exception as e:
        error_message = f"Error al calcular la expansión: {str(e)}"
        return jsonify({'status': 'error', 'message': error_message}), 400

# --- RUTAS DEL CATÁLOGO DE CÁLCULOS ---

@steam_tables_bp.route('/calculations/catalog', methods=['GET'])
def get_calculation_catalog():
    """Devuelve el catálogo de cálculos disponibles."""
    return jsonify(CalculationCatalog.get_catalog())

@steam_tables_bp.route('/calculations/execute/<string:calc_id>', methods=['POST'])
def execute_calculation(calc_id):
    """Ejecuta un cálculo específico del catálogo."""
    data = request.get_json()
    points_data = data.get('points', {})
    params_data = data.get('params', {})
    try:
        # La clase catálogo maneja la ejecución
        results = CalculationCatalog.execute(calc_id, {'points': points_data, 'params': params_data})
        return jsonify({'status': 'success', 'results': results})
    except Exception as e:
        # También manejamos errores para los cálculos complejos
        return jsonify({'status': 'error', 'message': str(e)}), 400

