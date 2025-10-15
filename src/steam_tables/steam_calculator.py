
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

    # The old calculate_balances function is now deprecated and will be removed.
    # def calculate_balances(self, balance_data): ...

    def _complete_point_properties(self, p):
        try:
            p_bar, t_c, h_kcal, s_kcal, x_frac = p.get('p'), p.get('t'), p.get('h'), p.get('s'), p.get('x')
            h_kj = kcal_to_kj(h_kcal) if h_kcal is not None else None
            s_kj = kcal_to_kj(s_kcal) if s_kcal is not None else None
            if p_bar is not None and t_c is not None: h_kcal, s_kcal = kj_to_kcal(self.steam_table.h_pt(p_bar, t_c)), kj_to_kcal(self.steam_table.s_pt(p_bar, t_c))
            elif p_bar is not None and h_kcal is not None: t_c, s_kcal = self.steam_table.t_ph(p_bar, h_kj), kj_to_kcal(self.steam_table.s_ph(p_bar, h_kj))
            elif p_bar is not None and s_kcal is not None: t_c, h_kcal = self.steam_table.t_ps(p_bar, s_kj), kj_to_kcal(self.steam_table.h_ps(p_bar, s_kj))
            elif h_kcal is not None and s_kcal is not None: p_bar, t_c = self.steam_table.p_hs(h_kj, s_kj), self.steam_table.t_hs(h_kj, s_kj)
            elif p_bar is not None and x_frac is not None: t_c, h_kcal, s_kcal = self.steam_table.tsat_p(p_bar), kj_to_kcal(self.steam_table.h_px(p_bar, x_frac)), kj_to_kcal(self.steam_table.sL_p(p_bar) + x_frac * (self.steam_table.sV_p(p_bar) - self.steam_table.sL_p(p_bar)))
            elif t_c is not None and x_frac is not None:
                p_bar = self.steam_table.psat_t(t_c)
                if p_bar: h_kcal, s_kcal = kj_to_kcal(self.steam_table.h_px(p_bar, x_frac)), kj_to_kcal(self.steam_table.sL_p(p_bar) + x_frac * (self.steam_table.sV_p(p_bar) - self.steam_table.sL_p(p_bar)))
            if x_frac is None and p_bar and h_kcal:
                try:
                    h_kj_check = kcal_to_kj(h_kcal)
                    t_sat = self.steam_table.tsat_p(p_bar)
                    if abs(self.steam_table.t_ph(p_bar, h_kj_check) - t_sat) < 0.1:
                        x_frac = self.steam_table.x_ph(p_bar, h_kj_check)
                        if not (0 <= x_frac <= 1): x_frac = None
                except (ValueError, TypeError): pass
            p.update({'p': p_bar, 't': t_c, 'h': h_kcal, 's': s_kcal, 'x': x_frac})
        except (ValueError, TypeError) as e: p['error'] = f"Error de cálculo: {e}. Verifique la consistencia de los datos."
        except Exception as e: p['error'] = f"Error inesperado: {e}"

# --- NEW MODULAR CALCULATION CATALOG ---

class CalculationCatalog:
    CATALOG = {
        'mass_balance_preheater': {
            'id': 'mass_balance_preheater',
            'name': 'Balance de Masa en Precalentador',
            'inputs': {'points': ['h2', 'hn', 'hx', 'hn_prime'], 'params': ['Gv', 'Gx', 'Gc']},
            'outputs': ['Gv', 'Gx', 'Gc'],
            'description': 'Calcula los flujos másicos (Gv, Gx, Gc). Proporcione uno de los tres para calcular los otros dos.'
        },
        'condenser_balance': {
            'id': 'condenser_balance',
            'name': 'Balance de Energía en Condensador',
            'inputs': {'points': ['h1', 'h6'], 'params': ['Gc', 'Qc', 'W', 'ts', 'te', 'Cp']},
            'outputs': ['Qc', 'W', 'ts', 'te'],
            'description': 'Calcula el calor intercambiado (Qc) o el estado del agua de refrigeración.'
        },
        'steam_generator_performance': {
            'id': 'steam_generator_performance',
            'name': 'Rendimiento del Generador de Vapor',
            'inputs': {'points': ['h3', 'h4', 'h5', 'hn'], 'params': ['Gv', 'Gc', 'rgv', 'Gco', 'Pci']},
            'outputs': ['rgv', 'Gco'],
            'description': 'Calcula el rendimiento de la caldera (rgv) o el consumo de combustible (Gco).'
        },
        'net_power': {
            'id': 'net_power',
            'name': 'Potencia Neta del Ciclo',
            'inputs': {'points': ['h3', 'h4', 'h5', 'h6'], 'params': ['Gv', 'Gc']},
            'outputs': ['potencia_kw'],
            'description': 'Calcula la potencia neta en bornes del generador eléctrico.'
        },
        'regenerative_gain': {
            'id': 'regenerative_gain',
            'name': 'Ganancia por Regeneración',
            'inputs': {'points': ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hn'], 'params': ['Gv', 'Gc']},
            'outputs': ['ganancia_regeneracion'],
            'description': 'Compara la eficiencia del ciclo regenerativo con un ciclo simple sin extracción.'
        }
    }

    @staticmethod
    def mass_balance_preheater(points, params):
        h = lambda p_id: points.get(p_id, {}).get('h')
        h2, hn, hx, hn_prime = h('2'), h('n'), h('x'), h('n_prime')
        Gv, Gx, Gc = params.get('Gv'), params.get('Gx'), params.get('Gc')

        if all(v is not None for v in [h2, hn, hx, hn_prime]):
            delta_h_condensate = hn - h2
            delta_h_extraction = hx - hn_prime
            if delta_h_condensate > 0 and delta_h_extraction > 0:
                if Gv is None and Gx is not None:
                    Gc = Gx * delta_h_extraction / delta_h_condensate
                    Gv = Gx + Gc
                elif Gv is None and Gc is not None:
                    Gx = Gc * delta_h_condensate / delta_h_extraction
                    Gv = Gx + Gc
                elif Gv is not None:
                    Gx = Gv * delta_h_condensate / (delta_h_extraction + delta_h_condensate)
                    Gc = Gv - Gx
                params.update({'Gv': Gv, 'Gx': Gx, 'Gc': Gc})
        return params

    @staticmethod
    def condenser_balance(points, params):
        h = lambda p_id: points.get(p_id, {}).get('h')
        h1, h6 = h('1'), h('6')
        Gc, Qc, W, ts, te, Cp = params.get('Gc'), params.get('Qc'), params.get('W'), params.get('ts'), params.get('te'), params.get('Cp')

        if Qc is None and all(v is not None for v in [Gc, h6, h1]) and h6 > h1:
            params['Qc'] = Gc * (h6 - h1)
        elif Qc is None and all(v is not None for v in [W, ts, te, Cp]) and ts > te:
            params['Qc'] = W * Cp * (ts - te)
        
        Qc = params.get('Qc') # Re-fetch in case it was just calculated
        if Qc is not None and Cp is not None and Cp > 0:
            if W is None and all(v is not None for v in [ts, te]) and ts > te:
                params['W'] = Qc / (Cp * (ts - te))
            elif ts is None and all(v is not None for v in [W, te]) and W > 0:
                params['ts'] = te + (Qc / (W * Cp))
            elif te is None and all(v is not None for v in [W, ts]) and W > 0:
                params['te'] = ts - (Qc / (W * Cp))
        return params

    @staticmethod
    def steam_generator_performance(points, params):
        h = lambda p_id: points.get(p_id, {}).get('h')
        h3, h4, h5, hn = h('3'), h('4'), h('5'), h('n')
        Gv, Gc = params.get('Gv'), params.get('Gc')
        rgv, Gco, Pci = params.get('rgv'), params.get('Gco'), params.get('Pci')

        if all(v is not None for v in [Gv, Gc, h3, h4, h5, hn]):
            heat_added = Gv * (h3 - hn) + Gc * (h5 - h4)
            if heat_added > 0:
                if all(v is not None for v in [Gco, Pci]) and Gco > 0 and Pci > 0:
                    params['rgv'] = (heat_added / (Gco * Pci)) * 100
                elif all(v is not None for v in [rgv, Pci]) and rgv > 0 and Pci > 0:
                    params['Gco'] = heat_added / (Pci * (rgv / 100))
        return params
        
    @staticmethod
    def net_power(points, params):
        h = lambda p_id: points.get(p_id, {}).get('h')
        h3, h4, h5, h6 = h('3'), h('4'), h('5'), h('6')
        Gv, Gc = params.get('Gv'), params.get('Gc')
        if all(v is not None for v in [Gv, Gc, h3, h4, h5, h6]):
            work_total_kcal_h = Gv * (h3 - h4) + Gc * (h5 - h6)
            if work_total_kcal_h > 0:
                params['potencia_kw'] = work_total_kcal_h / 860.421
        return params

    @staticmethod
    def regenerative_gain(points, params):
        h = lambda p_id: points.get(p_id, {}).get('h')
        h1, h2, h3, h4, h5, h6, hn = h('1'), h('2'), h('3'), h('4'), h('5'), h('6'), h('n')
        Gv, Gc = params.get('Gv'), params.get('Gc')

        if all(v is not None for v in [Gv, Gc, h1, h2, h3, h4, h5, h6, hn]) and Gv > 0:
            q_in_regen = (h3 - hn) + (Gc/Gv * (h5 - h4))
            w_out_regen = (h3 - h4) + (Gc/Gv * (h5 - h6))
            w_in_pump = h2 - h1
            w_net_regen = w_out_regen - w_in_pump
            if q_in_regen > 0:
                rend_regen = w_net_regen / q_in_regen
                q_in_no_regen = (h3 - h2) + (h5 - h4) # Approximated without Gc/Gv factor for simplicity
                w_net_no_regen = (h3 - h4) + (h5 - h6) - (h2 - h1)
                if q_in_no_regen > 0:
                    rend_no_regen = w_net_no_regen / q_in_no_regen
                    if rend_no_regen > 0:
                        params['ganancia_regeneracion'] = ((rend_regen - rend_no_regen) / rend_no_regen) * 100
        return params

    @classmethod
    def get_catalog(cls):
        # Return a list of dictionaries, without the implementation details
        return [v for k, v in cls.CATALOG.items()]

    @classmethod
    def execute(cls, calc_id, data):
        if calc_id not in cls.CATALOG:
            raise ValueError(f"Cálculo '{calc_id}' no encontrado.")
        
        calculation_method = getattr(cls, calc_id, None)
        if not callable(calculation_method):
             raise NotImplementedError(f"La función para '{calc_id}' no está implementada.")

        points = data.get('points', {})
        params = data.get('params', {})
        
        # Execute the static method
        updated_params = calculation_method(points, params)
        return {'params': updated_params}

