
from pyXSteam.XSteam import XSteam

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
        # ... (código sin cambios)
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

    def calculate_balances(self, balance_data):
        points = balance_data.get('points', {})
        params = balance_data.get('params', {})
        def h(p_id): return points.get(p_id, {}).get('h')

        h1, h2, h3, h4, h5, h6 = h('1'), h('2'), h('3'), h('4'), h('5'), h('6')
        hn, hx, hn_prime = h('n'), h('x'), h('n_prime')
        Gv, Gx, Gc = params.get('Gv'), params.get('Gx'), params.get('Gc')

        if all(v is not None for v in [h2, hn, hx, hn_prime]):
            delta_h_condensate = hn - h2
            delta_h_extraction = hx - hn_prime
            if delta_h_condensate > 0 and delta_h_extraction > 0:
                if Gv is None and Gx is not None: Gc, Gv = Gx * delta_h_extraction / delta_h_condensate, Gx + Gc
                elif Gv is None and Gc is not None: Gx, Gv = Gc * delta_h_condensate / delta_h_extraction, Gx + Gc
                elif Gv is not None: Gx, Gc = Gv * delta_h_condensate / (delta_h_extraction + delta_h_condensate), Gv - Gx
                params.update({'Gv': Gv, 'Gx': Gx, 'Gc': Gc})

        Gv, Gc = params.get('Gv'), params.get('Gc')
        Qc, W, ts, te, Cp = params.get('Qc'), params.get('W'), params.get('ts'), params.get('te'), params.get('Cp')
        if Qc is None and all(v is not None for v in [W, ts, te, Cp]) and ts > te: params['Qc'] = W * Cp * (ts - te)
        elif Qc is None and all(v is not None for v in [Gc, h6, h1]) and h6 > h1: params['Qc'] = Gc * (h6 - h1)
        
        Qc = params.get('Qc')
        if Qc is not None and Cp is not None and Cp > 0:
            if W is None and all(v is not None for v in [ts, te]) and ts > te: params['W'] = Qc / (Cp * (ts - te))
            elif ts is None and all(v is not None for v in [W, te]) and W > 0: params['ts'] = te + (Qc / (W * Cp))
            elif te is None and all(v is not None for v in [W, ts]) and W > 0: params['te'] = ts - (Qc / (W * Cp))

        rgv, Gco, Pci = params.get('rgv'), params.get('Gco'), params.get('Pci')
        if all(v is not None for v in [Gv, Gc, h3, h4, h5, hn]):
            heat_added = Gv * (h3 - hn) + Gc * (h5 - h4)
            if heat_added > 0:
                if all(v is not None for v in [Gco, Pci]) and Gco > 0 and Pci > 0: params['rgv'] = (heat_added / (Gco * Pci)) * 100
                elif all(v is not None for v in [rgv, Pci]) and rgv > 0 and Pci > 0: params['Gco'] = heat_added / (Pci * (rgv / 100))

        if all(v is not None for v in [Gv, Gc, h3, h4, h5, h6]):
            work_total_kcal_h = Gv * (h3 - h4) + Gc * (h5 - h6)
            if work_total_kcal_h > 0: params['potencia_kw'] = work_total_kcal_h / 860.421

        if all(v is not None for v in [Gv, Gc, h1, h2, h3, h4, h5, h6, hn]) and Gv > 0:
            q_in_regen = (h3 - hn) + (Gc/Gv * (h5 - h4)); w_out_regen = (h3 - h4) + (Gc/Gv * (h5 - h6)); w_in_pump = (h2 - h1)
            w_net_regen = w_out_regen - w_in_pump
            if q_in_regen > 0:
                rend_regen = w_net_regen / q_in_regen
                q_in_no_regen = (h3 - h2) + (h5 - h4); w_net_no_regen = (h3 - h4) + (h5 - h6) - (h2 - h1)
                if q_in_no_regen > 0:
                    rend_no_regen = w_net_no_regen / q_in_no_regen
                    if rend_no_regen > 0: params['ganancia_regeneracion'] = ((rend_regen - rend_no_regen) / rend_no_regen) * 100

        return {'params': params}

    def _complete_point_properties(self, p):
        # ... (código sin cambios)
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
