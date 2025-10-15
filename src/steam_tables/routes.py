
from flask import Blueprint, render_template, request, jsonify
from .steam_calculator import SteamCycleCalculator, POINT_DEFINITIONS

steam_tables_blueprint = Blueprint('steam_tables', __name__, template_folder='templates')

# --- Instancia única del calculador ---
cycle_calculator = SteamCycleCalculator()

@steam_tables_blueprint.route('/steam_tables', methods=['GET'])
def steam_tables():
    """Renders the main page with the steam table structure."""
    cycle_data = {p_id: defs.copy() for p_id, defs in POINT_DEFINITIONS.items()}
    return render_template('steam_tables.html', cycle_data=cycle_data)

@steam_tables_blueprint.route('/calculate_point', methods=['POST'])
def calculate_point():
    """Calculates the properties of a single point based on JSON data."""
    try:
        point_data = request.get_json()
        if not point_data or len(point_data) < 3:
            return jsonify({'error': 'Datos de entrada insuficientes.'}), 400

        calculated_point = cycle_calculator.calculate_single_point(point_data)
        
        if 'error' in calculated_point:
            return jsonify({'error': calculated_point['error']}), 400

        return jsonify(calculated_point)

    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {e}'}), 500

@steam_tables_blueprint.route('/calculate_cycle', methods=['POST'])
def calculate_cycle():
    """Receives all cycle data and calculates expansions and/or efficiencies."""
    try:
        data = request.get_json()
        result = cycle_calculator.calculate_expansions_and_efficiencies(
            cycle_data=data,
            eta_hp=data.get('eta_hp'),
            eta_lp=data.get('eta_lp')
        )
        if 'error' in result:
            return jsonify({'error': result['error']}), 400
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {e}'}), 500

@steam_tables_blueprint.route('/calculate_balances', methods=['POST'])
def calculate_balances():
    """Receives all page data and calculates mass/energy balances."""
    try:
        data = request.get_json()
        result = cycle_calculator.calculate_balances(data)

        if 'error' in result:
            return jsonify({'error': result['error']}), 400

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {e}'}), 500
