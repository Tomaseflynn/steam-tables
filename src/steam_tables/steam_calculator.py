
from pyXSteam.XSteam import XSteam

# ... (Helper functions and POINT_DEFINITIONS remain the same) ...
def kcal_to_kj(kcal):
    if kcal is None: return None
    return kcal * 4.184

def kj_to_kcal(kj):
    if kj is None: return None
    return kj / 4.184

POINT_DEFINITIONS = {
    '1': {'desc': 'Salida Condensador (Líq. Sat.)'},
    '2_prime': {'desc': 'Salida Bomba (Ideal)'},
    '2': {'desc': 'Salida Bomba (Real)'},
    'n': {'desc': 'Salida Precalentador (Agua)'},
    'n_prime': {'desc': 'Drenaje Precalentador (Líq. Sat.)'},
    '3': {'desc': 'Entrada Turbina AP'},
    '4_prime': {'desc': 'Salida Turbina AP (Ideal)'},
    '4': {'desc': 'Salida Turbina AP (Real)'},
    '5': {'desc': 'Entrada Turbina BP'},
    'x_prime': {'desc': 'Extracción Turbina (Ideal)'},
    'x': {'desc': 'Extracción Turbina (Real)'},
    '6_prime': {'desc': 'Salida Turbina BP (Ideal)'},
    '6': {'desc': 'Salida Turbina BP (Real)'},
}


class SteamCycleCalculator:
    def __init__(self):
        self.steam_table = XSteam(XSteam.UNIT_SYSTEM_MKS)

    def calculate_single_point(self, point_data):
        point_to_calculate = {prop: point_data.get(prop) for prop in ['p', 't', 'h', 's', 'x']}
        self._complete_point_properties(point_to_calculate)
        return point_to_calculate

    def calculate_expansions_and_efficiencies(self, cycle_data, eta_hp, eta_lp):
        points = cycle_data['points']
        def h(p_id): return points.get(p_id, {}).get('h')
        h3, h4_prime, h4 = h('3'), h('4_prime'), h('4')
        if h3 and h4_prime:
            if eta_hp is not None and h4 is None:                
                h4_real_kj = kcal_to_kj(h3) - (kcal_to_kj(h3) - kcal_to_kj(h4_prime)) * (eta_hp / 100.0)
                points['4']['h'] = kj_to_kcal(h4_real_kj)
            elif h4 is not None and eta_hp is None:
                if (h3 - h4_prime) > 0:
                    eta_hp = (h3 - h4) / (h3 - h4_prime) * 100
        hx_prime, hx = h('x_prime'), h('x')
        if h3 and hx_prime:
            p_x = points.get('x', {}).get('p')
            p_3 = points.get('3', {}).get('p')
            p_5 = points.get('5', {}).get('p')
            if p_x and p_3 and p_5 and p_5 <= p_x <= p_3:
                if eta_hp is not None and hx is None:
                    hx_real_kj = kcal_to_kj(h3) - (kcal_to_kj(h3) - kcal_to_kj(hx_prime)) * (eta_hp / 100.0)
                    points['x']['h'] = kj_to_kcal(hx_real_kj)
                elif hx is not None and eta_hp is None:
                    if (h3 - hx_prime) > 0:
                         eta_hp = (h3 - hx) / (h3 - hx_prime) * 100
        h5, h6_prime, h6 = h('5'), h('6_prime'), h('6')
        if h5 and h6_prime:
            if eta_lp is not None and h6 is None:
                h6_real_kj = kcal_to_kj(h5) - (kcal_to_kj(h5) - kcal_to_kj(h6_prime)) * (eta_lp / 100.0)
                points['6']['h'] = kj_to_kcal(h6_real_kj)
            elif h6 is not None and eta_lp is None:
                if (h5 - h6_prime) > 0:
                    eta_lp = (h5 - h6) / (h5 - h6_prime) * 100
        for p_id in ['4', '6', 'x']:
            if points.get(p_id, {}).get('h') is not None:
                p_data = points[p_id]
                p_bar = points.get(p_id, {}).get('p')
                p_data = { 'p': p_bar, 'h': points[p_id]['h'] } 
                self._complete_point_properties(p_data)
                points[p_id] = p_data
        return {'points': points, 'eta_hp': eta_hp, 'eta_lp': eta_lp}

    def _complete_point_properties(self, p):
        # ... (código sin cambios)
        pass # Logic is correct from previous steps


# --- NEW MODULAR CALCULATION CATALOG ---

class CalculationCatalog:
    CATALOG = {
        'mass_balance_preheater': {
            'id': 'mass_balance_preheater',
            'name': 'Balance de Masa en Precalentador',
            'inputs': {'points': ['h_2', 'h_n', 'h_x', 'h_n_prime'], 'params': ['Gv', 'Gx', 'Gc']},
            'outputs': ['Gv', 'Gx', 'Gc'],
            'description': 'Calcula los flujos másicos (Gv, Gx, Gc). Proporcione uno de los tres para calcular los otros dos.'
        },
        'condenser_balance': {
            'id': 'condenser_balance',
            'name': 'Balance de Energía en Condensador',
            'inputs': {'points': ['h_1', 'h_6'], 'params': ['Gc', 'Qc', 'W', 'ts', 'te', 'Cp']},
            'outputs': ['Qc', 'W', 'ts', 'te'],
            'description': 'Calcula el calor intercambiado (Qc) o el estado del agua de refrigeración.'
        },
        'steam_generator_performance': {
            'id': 'steam_generator_performance',
            'name': 'Rendimiento del Generador de Vapor',
            'inputs': {'points': ['h_3', 'h_4', 'h_5', 'h_n'], 'params': ['Gv', 'Gc', 'rgv', 'Gco', 'Pci']},
            'outputs': ['rgv', 'Gco'],
            'description': 'Calcula el rendimiento de la caldera (rgv) o el consumo de combustible (Gco).'
        },
        'net_power': {
            'id': 'net_power',
            'name': 'Potencia Neta del Ciclo',
            'inputs': {'points': ['h_3', 'h_4', 'h_5', 'h_6'], 'params': ['Gv', 'Gc']},
            'outputs': ['potencia_kw'],
            'description': 'Calcula la potencia neta en bornes del generador eléctrico.'
        },
        'regenerative_gain': {
            'id': 'regenerative_gain',
            'name': 'Ganancia por Regeneración',
            'inputs': {'points': ['h_1', 'h_2', 'h_3', 'h_4', 'h_5', 'h_6', 'h_n'], 'params': ['Gv', 'Gc']},
            'outputs': ['ganancia_regeneracion'],
            'description': 'Compara la eficiencia del ciclo regenerativo con un ciclo simple sin extracción.'
        },
        'chained_rgv_from_condenser': {
            'id': 'chained_rgv_from_condenser',
            'name': '[Secuencia] Calcular RGV desde Condensador',
            'inputs': {
                'points': ['h_1', 'h_6', 'h_2', 'h_n', 'h_x', 'h_n_prime', 'h_3', 'h_4', 'h_5'],
                'params': ['W', 'ts', 'te', 'Cp', 'Gco', 'Pci']
            },
            'outputs': ['Qc', 'Gc', 'Gx', 'Gv', 'rgv'],
            'description': 'Calcula el rendimiento de la caldera (rgv) siguiendo una secuencia lógica a partir de los datos del agua de refrigeración del condensador.'
        }
    }

    # ... (Static methods for individual calculations remain the same) ...
    @staticmethod
    def mass_balance_preheater(points, params): # ...
        pass
    @staticmethod
    def condenser_balance(points, params): # ...
        pass
    @staticmethod
    def steam_generator_performance(points, params): # ...
        pass
    @staticmethod
    def net_power(points, params): # ...
        pass
    @staticmethod
    def regenerative_gain(points, params): # ...
        pass

    @classmethod
    def get_catalog(cls):
        return [v for k, v in cls.CATALOG.items()]

    @classmethod
    def execute(cls, calc_id, data):
        # ... (Execute logic remains the same) ...
        pass

    # --- NEW CHAINED CALCULATION ---
    @staticmethod
    def chained_rgv_from_condenser(points, params):
        # Step 1: Calculate Qc from cooling water data
        temp_params = CalculationCatalog.condenser_balance(points, params.copy())
        
        # Step 2: Calculate Gc from Qc
        h = lambda p_id: points.get(p_id, {}).get('h')
        h1, h6 = h('1'), h('6')
        Qc = temp_params.get('Qc')
        if Qc is not None and h1 is not None and h6 is not None and (h6 - h1) > 0:
            temp_params['Gc'] = Qc / (h6 - h1)
        else:
            # Can't proceed if Gc can't be determined
            return temp_params # Return intermediate results

        # Step 3: Use Gc to resolve mass flows in preheater
        # We pass the updated params with Gc calculated
        temp_params = CalculationCatalog.mass_balance_preheater(points, temp_params)

        # Step 4: With all flows known, calculate steam generator performance
        final_params = CalculationCatalog.steam_generator_performance(points, temp_params)

        return final_params