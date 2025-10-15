
from flask import Blueprint, render_template, request, jsonify
# Import the new catalog class
from .steam_calculator import SteamCycleCalculator, POINT_DEFINITIONS, CalculationCatalog

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

# --- NEW API ENDPOINTS FOR MODULAR CALCULATIONS ---

@steam_tables_blueprint.route('/api/calculations', methods=['GET'])
def get_calculations_catalog():
    """Returns the list of available modular calculations."""
    try:
        catalog = CalculationCatalog.get_catalog()
        return jsonify(catalog)
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {e}'}), 500

@steam_tables_blueprint.route('/api/execute', methods=['POST'])
def execute_calculation():
    """Executes a specific calculation based on its ID and the provided data."""
    try:
        data = request.get_json()
        calc_id = data.get('id')
        
        if not calc_id:
            return jsonify({'error': 'No se especificó un ID de cálculo.'}), 400

        # The CalculationCatalog's execute method handles the logic
        result = CalculationCatalog.execute(calc_id, data)

        if 'error' in result:
             return jsonify({'error': result['error']}), 400

        return jsonify(result)

    except (ValueError, NotImplementedError) as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor: {e}'}), 500

# The old '/calculate_balances' route is now removed.
