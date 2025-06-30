# business_plan_projections.py - Progetto Business Plan Pro - versione 1.9 - 2025-06-25
# MODIFICA: Ripristinata la logica di _build_report_from_structure originale e stabile.
#           Adattata per gestire i flussi di cassa senza rompere CE e SP.

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from business_plan_assumptions import BusinessPlanAssumptions, ASSUMPTION_DEFINITIONS, RI_CODES
import financial_model


class BusinessPlanProjections:
    """Classe per gestire le proiezioni del Business Plan"""
    
    def __init__(self, cliente: str, anno_base: int, durata: int, assumptions: Optional[BusinessPlanAssumptions] = None):
        self.cliente = cliente
        self.anno_base = anno_base
        self.durata = durata
        self.anni_bp = [anno_base + i for i in range(durata + 1)]
        self.assumptions = assumptions if assumptions else BusinessPlanAssumptions(cliente)
        self.dati_proiettati = {}
        
    def inizializza_con_dati_storici(self, dati_storici: Dict) -> None:
        for codice_ri in RI_CODES.keys():
            if self.anno_base not in self.dati_proiettati:
                self.dati_proiettati[self.anno_base] = {}
            valore_base = dati_storici.get(self.anno_base, {}).get(codice_ri, 0)
            self.dati_proiettati[self.anno_base][codice_ri] = valore_base
    
    def calcola_proiezioni(self) -> Dict:
        for i, anno in enumerate(self.anni_bp[1:], 1):
            self.dati_proiettati[anno] = {}
            self._calcola_anno_proiezione(anno, i)
        return self.dati_proiettati
    
    def _calcola_anno_proiezione(self, anno: int, anno_indice: int) -> None:
        # Questa funzione rimane invariata dalla v1.5, che era corretta
        anno_precedente = anno - 1
        dati_prec = self.dati_proiettati.get(anno_precedente, {})
        dati_curr = self.dati_proiettati[anno]
        iteration_count, max_iterations, tolerance = 0, 100, 0.01
        tasso_interesse = self.assumptions.get_assumption_value(11, anno_indice) / 100
        dati_curr['RI13'] = dati_prec.get('RI33', 0) * tasso_interesse
        while True:
            iteration_count += 1
            ri13_inizio_ciclo = dati_curr['RI13']
            crescita_ricavi = self.assumptions.get_assumption_value(0, anno_indice) / 100
            dati_curr['RI01'] = dati_prec.get('RI01', 0) * (1 + crescita_ricavi)
            rotazione_magazzino = self.assumptions.get_assumption_value(3, anno_indice)
            dati_curr['RI25'] = dati_curr['RI01'] / rotazione_magazzino if rotazione_magazzino > 0 else dati_prec.get('RI25', 0)
            dati_curr['RI09'] = dati_curr.get('RI25', 0) - dati_prec.get('RI25', 0)
            dati_curr['RI02'] = 0.0
            percentuale_costo_su_ricavi = self.assumptions.get_assumption_value(4, anno_indice) / 100
            costo_del_venduto = dati_curr.get('RI01', 0) * percentuale_costo_su_ricavi
            dati_curr['RI05'] = costo_del_venduto + dati_curr.get('RI09', 0)
            dati_curr['RI03'] = dati_curr.get('RI01', 0) * (self.assumptions.get_assumption_value(1, anno_indice) / 100)
            dati_curr['RI04'] = dati_curr.get('RI01', 0) * (self.assumptions.get_assumption_value(8, anno_indice) / 100)
            valore_produzione = dati_curr.get('RI01', 0) + dati_curr.get('RI03', 0) + dati_curr.get('RI04', 0)
            dati_curr['RI06'] = valore_produzione * (self.assumptions.get_assumption_value(5, anno_indice) / 100)
            dati_curr['RI08'] = valore_produzione * (self.assumptions.get_assumption_value(2, anno_indice) / 100)
            costi_esterni_operativi = (dati_curr.get('RI05', 0) + dati_curr.get('RI06', 0) + dati_curr.get('RI08', 0))
            valore_aggiunto = valore_produzione - costi_esterni_operativi + dati_curr.get('RI09', 0)
            dati_curr['RI07'] = self.assumptions.get_assumption_value(13, anno_indice)
            ebitda = valore_aggiunto - dati_curr.get('RI07', 0)
            dati_curr['RI10'] = valore_produzione * (self.assumptions.get_assumption_value(12, anno_indice) / 100)
            dati_curr['RI12'] = self.assumptions.get_assumption_value(22, anno_indice)
            investimenti_C = self.assumptions.get_assumption_value(16, anno_indice)
            investimenti_D = self.assumptions.get_assumption_value(17, anno_indice)
            aliquota_A = self.assumptions.get_assumption_value(14, anno_indice) / 100
            aliquota_B = self.assumptions.get_assumption_value(15, anno_indice) / 100
            ammortamenti_immateriali_E = (dati_prec.get('RI20', 0) + investimenti_C) * aliquota_A
            ammortamenti_materiali_F = (dati_prec.get('RI21', 0) + investimenti_D) * aliquota_B
            dati_curr['RI11'] = ammortamenti_immateriali_E + ammortamenti_materiali_F
            ebit = ebitda - dati_curr.get('RI11', 0) - dati_curr.get('RI10', 0) - dati_curr.get('RI12', 0)
            dati_curr['RI14'] = self.assumptions.get_assumption_value(23, anno_indice)
            dati_curr['RI15'] = self.assumptions.get_assumption_value(24, anno_indice)
            dati_curr['RI16'] = self.assumptions.get_assumption_value(25, anno_indice)
            risultato_lordo = ebit + dati_curr.get('RI14', 0) - dati_curr.get('RI13', 0) + dati_curr.get('RI16', 0) - dati_curr.get('RI15', 0)
            dati_curr['RI17'] = risultato_lordo * 0.28 if risultato_lordo > 0 else 0
            dati_curr['RI18'] = risultato_lordo - dati_curr.get('RI17', 0)
            dati_curr['RI32'] = dati_prec.get('RI32', 0) + dati_curr.get('RI18', 0)
            dati_curr['RI20'] = dati_prec.get('RI20', 0) + investimenti_C - ammortamenti_immateriali_E
            dati_curr['RI21'] = dati_prec.get('RI21', 0) + investimenti_D - ammortamenti_materiali_F
            dati_curr['RI22'] = self.assumptions.get_assumption_value(18, anno_indice)
            dati_curr['RI28'] = self.assumptions.get_assumption_value(19, anno_indice)
            dati_curr['RI29'] = self.assumptions.get_assumption_value(20, anno_indice)
            dati_curr['RI30'] = self.assumptions.get_assumption_value(21, anno_indice)
            dati_curr['RI19'] = dati_prec.get('RI19', 0)
            giorni_clienti = self.assumptions.get_assumption_value(6, anno_indice)
            dati_curr['RI23'] = (valore_produzione * 1.22 * giorni_clienti) / 365
            costi_fornitori = dati_curr.get('RI05', 0) + dati_curr.get('RI06', 0) + dati_curr.get('RI08', 0)
            giorni_fornitori = self.assumptions.get_assumption_value(7, anno_indice)
            dati_curr['RI24'] = (costi_fornitori * 1.22 * giorni_fornitori) / 365
            dati_curr['RI26'] = dati_curr.get('RI23', 0) * (self.assumptions.get_assumption_value(9, anno_indice) / 100)
            dati_curr['RI27'] = dati_curr.get('RI24', 0) * (self.assumptions.get_assumption_value(10, anno_indice) / 100)
            pfn_corrente = self._calcola_equilibrio_finanziario(anno, anno_precedente)
            pfn_precedente = dati_prec.get('RI33', 0) - dati_prec.get('RI31', 0)
            pfn_media = (pfn_precedente + pfn_corrente) / 2 if (pfn_precedente + pfn_corrente) > 0 else 0
            ri13_fine_ciclo = pfn_media * tasso_interesse
            dati_curr['RI13'] = ri13_fine_ciclo
            if abs(ri13_fine_ciclo - ri13_inizio_ciclo) < tolerance: break
            if iteration_count > max_iterations: print(f"ATTENZIONE: Calcolo iterativo per l'anno {anno} non convergente."); break

    def _calcola_equilibrio_finanziario(self, anno: int, anno_precedente: int) -> float:
        dati_curr = self.dati_proiettati[anno]
        dati_prec = self.dati_proiettati.get(anno_precedente, {})
        ccn = (dati_curr.get('RI23', 0) - dati_curr.get('RI24', 0) + dati_curr.get('RI25', 0) + 
               dati_curr.get('RI26', 0) - dati_curr.get('RI27', 0))
        immobilizzazioni = (dati_curr.get('RI20', 0) + dati_curr.get('RI21', 0) + dati_curr.get('RI22', 0))
        capitale_investito = (dati_curr.get('RI19', 0) + immobilizzazioni + ccn - 
                              dati_curr.get('RI28', 0) - dati_curr.get('RI29', 0) - dati_curr.get('RI30', 0))
        pfn_target = capitale_investito - dati_curr.get('RI32', 0)
        dati_curr['RI31'] = dati_prec.get('RI31', 0)
        dati_curr['RI33'] = pfn_target + dati_curr.get('RI31', 0)
        if dati_curr.get('RI33', 0) < 0:
            dati_curr['RI31'] = dati_curr.get('RI31', 0) - dati_curr.get('RI33', 0)
            dati_curr['RI33'] = 0
        return dati_curr.get('RI33', 0) - dati_curr.get('RI31', 0)

    def get_dataframe_proiezioni(self) -> pd.DataFrame:
        if not self.dati_proiettati: return pd.DataFrame()
        df_list = []
        for codice_ri in RI_CODES.keys():
            row = {'Codice': codice_ri, 'Descrizione': RI_CODES[codice_ri]}
            for anno in self.anni_bp:
                row[str(anno)] = self.dati_proiettati.get(anno, {}).get(codice_ri, 0)
            df_list.append(row)
        return pd.DataFrame(df_list)
    
    def _build_report_from_structure(self, structure: List[Dict]) -> pd.DataFrame:
        report_data = []
        calculated_values_by_year = {anno: {} for anno in self.anni_bp}
        for anno in self.anni_bp:
            for item in structure:
                if item['Tipo'] == 'Dettaglio' and 'ID_RI' in item:
                    calculated_values_by_year[anno][item.get('ID_RI')] = self.dati_proiettati.get(anno, {}).get(item['ID_RI'], 0)
        for item in sorted(structure, key=lambda x: x.get('Ordine', 0)):
            if item['Tipo'] == 'Calcolo':
                voce_name = item['Voce']
                for anno in self.anni_bp:
                    try:
                        formula_input = {ref: calculated_values_by_year[anno].get(ref, 0) for ref in item['Formula_Refs']}
                        calculated_values_by_year[anno][voce_name] = item['Formula'](formula_input)
                    except Exception:
                        calculated_values_by_year[anno][voce_name] = 0
        for item in structure:
            if not item.get('Visibile', True): continue
            row = {'Voce': item['Voce'].upper() if item.get('Maiuscolo', False) else item['Voce']}
            for anno in self.anni_bp:
                val = calculated_values_by_year.get(anno, {}).get(item.get('ID_RI', item.get('Voce')), "")
                if item['Tipo'] == 'Intestazione': val = ""
                row[str(anno)] = val
            report_data.append(row)
        return pd.DataFrame(report_data)

    def get_report_ce_proiezioni(self) -> pd.DataFrame:
        return self._build_report_from_structure(financial_model.report_structure_ce)
    
    def get_report_sp_proiezioni(self) -> pd.DataFrame:
        return self._build_report_from_structure(financial_model.report_structure_sp)
        
    def get_report_full_cf_proiezioni(self) -> pd.DataFrame:
        structure_ff = financial_model.report_structure_ff
        df_ce = self.get_report_ce_proiezioni().set_index('Voce')
        df_sp = self.get_report_sp_proiezioni().set_index('Voce')
        df_full = pd.concat([df_ce, df_sp])
        report_columns = ['Voce'] + [str(anno) for anno in self.anni_bp[1:]]
        final_df = pd.DataFrame(columns=report_columns)
        final_df['Voce'] = [item['Voce'] for item in structure_ff]
        for anno in self.anni_bp[1:]:
            anno_str = str(anno)
            anno_prec_str = str(anno - 1)
            flows_input = {}
            for voce in df_full.index:
                flows_input[f"{voce}_current"] = df_full.loc[voce, anno_str] if anno_str in df_full.columns and voce in df_full.index else 0
                flows_input[f"{voce}_previous"] = df_full.loc[voce, anno_prec_str] if anno_prec_str in df_full.columns and voce in df_full.index else 0
            for ri_code in self.dati_proiettati.get(anno, {}):
                flows_input[f"{ri_code}_current"] = self.dati_proiettati[anno].get(ri_code, 0)
            for ri_code in self.dati_proiettati.get(anno-1, {}):
                flows_input[f"{ri_code}_previous"] = self.dati_proiettati[anno-1].get(ri_code, 0)
            calculated_flows_for_year = {}
            for item in sorted(structure_ff, key=lambda x: x.get('Ordine', 0)):
                if item.get('Tipo') == 'Calcolo':
                    voce_name = item['Voce']
                    try:
                        valore_calcolato = item['Formula'](flows_input)
                        calculated_flows_for_year[voce_name] = valore_calcolato
                        flows_input[voce_name] = valore_calcolato
                    except Exception:
                        calculated_flows_for_year[voce_name] = 0
            final_df[anno_str] = final_df['Voce'].map(calculated_flows_for_year).fillna("")
        return final_df
# business_plan_projections.py - Progetto Business Plan Pro - versione 1.9 - 2025-06-25
# MODIFICA: Ripristinata la logica di _build_report_from_structure originale e stabile.
#           Adattata per gestire i flussi di cassa senza rompere CE e SP.

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from business_plan_assumptions import BusinessPlanAssumptions, ASSUMPTION_DEFINITIONS, RI_CODES
import financial_model


class BusinessPlanProjections:
    """Classe per gestire le proiezioni del Business Plan"""
    
    def __init__(self, cliente: str, anno_base: int, durata: int, assumptions: Optional[BusinessPlanAssumptions] = None):
        self.cliente = cliente
        self.anno_base = anno_base
        self.durata = durata
        self.anni_bp = [anno_base + i for i in range(durata + 1)]
        self.assumptions = assumptions if assumptions else BusinessPlanAssumptions(cliente)
        self.dati_proiettati = {}
        
    def inizializza_con_dati_storici(self, dati_storici: Dict) -> None:
        for codice_ri in RI_CODES.keys():
            if self.anno_base not in self.dati_proiettati:
                self.dati_proiettati[self.anno_base] = {}
            valore_base = dati_storici.get(self.anno_base, {}).get(codice_ri, 0)
            self.dati_proiettati[self.anno_base][codice_ri] = valore_base
    
    def calcola_proiezioni(self) -> Dict:
        for i, anno in enumerate(self.anni_bp[1:], 1):
            self.dati_proiettati[anno] = {}
            self._calcola_anno_proiezione(anno, i)
        return self.dati_proiettati
    
    def _calcola_anno_proiezione(self, anno: int, anno_indice: int) -> None:
        # Questa funzione rimane invariata dalla v1.5, che era corretta
        anno_precedente = anno - 1
        dati_prec = self.dati_proiettati.get(anno_precedente, {})
        dati_curr = self.dati_proiettati[anno]
        iteration_count, max_iterations, tolerance = 0, 100, 0.01
        tasso_interesse = self.assumptions.get_assumption_value(11, anno_indice) / 100
        dati_curr['RI13'] = dati_prec.get('RI33', 0) * tasso_interesse
        while True:
            iteration_count += 1
            ri13_inizio_ciclo = dati_curr['RI13']
            crescita_ricavi = self.assumptions.get_assumption_value(0, anno_indice) / 100
            dati_curr['RI01'] = dati_prec.get('RI01', 0) * (1 + crescita_ricavi)
            rotazione_magazzino = self.assumptions.get_assumption_value(3, anno_indice)
            dati_curr['RI25'] = dati_curr['RI01'] / rotazione_magazzino if rotazione_magazzino > 0 else dati_prec.get('RI25', 0)
            dati_curr['RI09'] = dati_curr.get('RI25', 0) - dati_prec.get('RI25', 0)
            dati_curr['RI02'] = 0.0
            percentuale_costo_su_ricavi = self.assumptions.get_assumption_value(4, anno_indice) / 100
            costo_del_venduto = dati_curr.get('RI01', 0) * percentuale_costo_su_ricavi
            dati_curr['RI05'] = costo_del_venduto + dati_curr.get('RI09', 0)
            dati_curr['RI03'] = dati_curr.get('RI01', 0) * (self.assumptions.get_assumption_value(1, anno_indice) / 100)
            dati_curr['RI04'] = dati_curr.get('RI01', 0) * (self.assumptions.get_assumption_value(8, anno_indice) / 100)
            valore_produzione = dati_curr.get('RI01', 0) + dati_curr.get('RI03', 0) + dati_curr.get('RI04', 0)
            dati_curr['RI06'] = valore_produzione * (self.assumptions.get_assumption_value(5, anno_indice) / 100)
            dati_curr['RI08'] = valore_produzione * (self.assumptions.get_assumption_value(2, anno_indice) / 100)
            costi_esterni_operativi = (dati_curr.get('RI05', 0) + dati_curr.get('RI06', 0) + dati_curr.get('RI08', 0))
            valore_aggiunto = valore_produzione - costi_esterni_operativi + dati_curr.get('RI09', 0)
            dati_curr['RI07'] = self.assumptions.get_assumption_value(13, anno_indice)
            ebitda = valore_aggiunto - dati_curr.get('RI07', 0)
            dati_curr['RI10'] = valore_produzione * (self.assumptions.get_assumption_value(12, anno_indice) / 100)
            dati_curr['RI12'] = self.assumptions.get_assumption_value(22, anno_indice)
            investimenti_C = self.assumptions.get_assumption_value(16, anno_indice)
            investimenti_D = self.assumptions.get_assumption_value(17, anno_indice)
            aliquota_A = self.assumptions.get_assumption_value(14, anno_indice) / 100
            aliquota_B = self.assumptions.get_assumption_value(15, anno_indice) / 100
            ammortamenti_immateriali_E = (dati_prec.get('RI20', 0) + investimenti_C) * aliquota_A
            ammortamenti_materiali_F = (dati_prec.get('RI21', 0) + investimenti_D) * aliquota_B
            dati_curr['RI11'] = ammortamenti_immateriali_E + ammortamenti_materiali_F
            ebit = ebitda - dati_curr.get('RI11', 0) - dati_curr.get('RI10', 0) - dati_curr.get('RI12', 0)
            dati_curr['RI14'] = self.assumptions.get_assumption_value(23, anno_indice)
            dati_curr['RI15'] = self.assumptions.get_assumption_value(24, anno_indice)
            dati_curr['RI16'] = self.assumptions.get_assumption_value(25, anno_indice)
            risultato_lordo = ebit + dati_curr.get('RI14', 0) - dati_curr.get('RI13', 0) + dati_curr.get('RI16', 0) - dati_curr.get('RI15', 0)
            dati_curr['RI17'] = risultato_lordo * 0.28 if risultato_lordo > 0 else 0
            dati_curr['RI18'] = risultato_lordo - dati_curr.get('RI17', 0)
            dati_curr['RI32'] = dati_prec.get('RI32', 0) + dati_curr.get('RI18', 0)
            dati_curr['RI20'] = dati_prec.get('RI20', 0) + investimenti_C - ammortamenti_immateriali_E
            dati_curr['RI21'] = dati_prec.get('RI21', 0) + investimenti_D - ammortamenti_materiali_F
            dati_curr['RI22'] = self.assumptions.get_assumption_value(18, anno_indice)
            dati_curr['RI28'] = self.assumptions.get_assumption_value(19, anno_indice)
            dati_curr['RI29'] = self.assumptions.get_assumption_value(20, anno_indice)
            dati_curr['RI30'] = self.assumptions.get_assumption_value(21, anno_indice)
            dati_curr['RI19'] = dati_prec.get('RI19', 0)
            giorni_clienti = self.assumptions.get_assumption_value(6, anno_indice)
            dati_curr['RI23'] = (valore_produzione * 1.22 * giorni_clienti) / 365
            costi_fornitori = dati_curr.get('RI05', 0) + dati_curr.get('RI06', 0) + dati_curr.get('RI08', 0)
            giorni_fornitori = self.assumptions.get_assumption_value(7, anno_indice)
            dati_curr['RI24'] = (costi_fornitori * 1.22 * giorni_fornitori) / 365
            dati_curr['RI26'] = dati_curr.get('RI23', 0) * (self.assumptions.get_assumption_value(9, anno_indice) / 100)
            dati_curr['RI27'] = dati_curr.get('RI24', 0) * (self.assumptions.get_assumption_value(10, anno_indice) / 100)
            pfn_corrente = self._calcola_equilibrio_finanziario(anno, anno_precedente)
            pfn_precedente = dati_prec.get('RI33', 0) - dati_prec.get('RI31', 0)
            pfn_media = (pfn_precedente + pfn_corrente) / 2 if (pfn_precedente + pfn_corrente) > 0 else 0
            ri13_fine_ciclo = pfn_media * tasso_interesse
            dati_curr['RI13'] = ri13_fine_ciclo
            if abs(ri13_fine_ciclo - ri13_inizio_ciclo) < tolerance: break
            if iteration_count > max_iterations: print(f"ATTENZIONE: Calcolo iterativo per l'anno {anno} non convergente."); break

    def _calcola_equilibrio_finanziario(self, anno: int, anno_precedente: int) -> float:
        dati_curr = self.dati_proiettati[anno]
        dati_prec = self.dati_proiettati.get(anno_precedente, {})
        ccn = (dati_curr.get('RI23', 0) - dati_curr.get('RI24', 0) + dati_curr.get('RI25', 0) + 
               dati_curr.get('RI26', 0) - dati_curr.get('RI27', 0))
        immobilizzazioni = (dati_curr.get('RI20', 0) + dati_curr.get('RI21', 0) + dati_curr.get('RI22', 0))
        capitale_investito = (dati_curr.get('RI19', 0) + immobilizzazioni + ccn - 
                              dati_curr.get('RI28', 0) - dati_curr.get('RI29', 0) - dati_curr.get('RI30', 0))
        pfn_target = capitale_investito - dati_curr.get('RI32', 0)
        dati_curr['RI31'] = dati_prec.get('RI31', 0)
        dati_curr['RI33'] = pfn_target + dati_curr.get('RI31', 0)
        if dati_curr.get('RI33', 0) < 0:
            dati_curr['RI31'] = dati_curr.get('RI31', 0) - dati_curr.get('RI33', 0)
            dati_curr['RI33'] = 0
        return dati_curr.get('RI33', 0) - dati_curr.get('RI31', 0)

    def get_dataframe_proiezioni(self) -> pd.DataFrame:
        if not self.dati_proiettati: return pd.DataFrame()
        df_list = []
        for codice_ri in RI_CODES.keys():
            row = {'Codice': codice_ri, 'Descrizione': RI_CODES[codice_ri]}
            for anno in self.anni_bp:
                row[str(anno)] = self.dati_proiettati.get(anno, {}).get(codice_ri, 0)
            df_list.append(row)
        return pd.DataFrame(df_list)
    
    def _build_report_from_structure(self, structure: List[Dict]) -> pd.DataFrame:
        report_data = []
        calculated_values_by_year = {anno: {} for anno in self.anni_bp}
        for anno in self.anni_bp:
            for item in structure:
                if item['Tipo'] == 'Dettaglio' and 'ID_RI' in item:
                    calculated_values_by_year[anno][item.get('ID_RI')] = self.dati_proiettati.get(anno, {}).get(item['ID_RI'], 0)
        for item in sorted(structure, key=lambda x: x.get('Ordine', 0)):
            if item['Tipo'] == 'Calcolo':
                voce_name = item['Voce']
                for anno in self.anni_bp:
                    try:
                        formula_input = {ref: calculated_values_by_year[anno].get(ref, 0) for ref in item['Formula_Refs']}
                        calculated_values_by_year[anno][voce_name] = item['Formula'](formula_input)
                    except Exception:
                        calculated_values_by_year[anno][voce_name] = 0
        for item in structure:
            if not item.get('Visibile', True): continue
            row = {'Voce': item['Voce'].upper() if item.get('Maiuscolo', False) else item['Voce']}
            for anno in self.anni_bp:
                val = calculated_values_by_year.get(anno, {}).get(item.get('ID_RI', item.get('Voce')), "")
                if item['Tipo'] == 'Intestazione': val = ""
                row[str(anno)] = val
            report_data.append(row)
        return pd.DataFrame(report_data)

    def get_report_ce_proiezioni(self) -> pd.DataFrame:
        return self._build_report_from_structure(financial_model.report_structure_ce)
    
    def get_report_sp_proiezioni(self) -> pd.DataFrame:
        return self._build_report_from_structure(financial_model.report_structure_sp)
        
    def get_report_full_cf_proiezioni(self) -> pd.DataFrame:
        structure_ff = financial_model.report_structure_ff
        df_ce = self.get_report_ce_proiezioni().set_index('Voce')
        df_sp = self.get_report_sp_proiezioni().set_index('Voce')
        df_full = pd.concat([df_ce, df_sp])
        report_columns = ['Voce'] + [str(anno) for anno in self.anni_bp[1:]]
        final_df = pd.DataFrame(columns=report_columns)
        final_df['Voce'] = [item['Voce'] for item in structure_ff]
        for anno in self.anni_bp[1:]:
            anno_str = str(anno)
            anno_prec_str = str(anno - 1)
            flows_input = {}
            for voce in df_full.index:
                flows_input[f"{voce}_current"] = df_full.loc[voce, anno_str] if anno_str in df_full.columns and voce in df_full.index else 0
                flows_input[f"{voce}_previous"] = df_full.loc[voce, anno_prec_str] if anno_prec_str in df_full.columns and voce in df_full.index else 0
            for ri_code in self.dati_proiettati.get(anno, {}):
                flows_input[f"{ri_code}_current"] = self.dati_proiettati[anno].get(ri_code, 0)
            for ri_code in self.dati_proiettati.get(anno-1, {}):
                flows_input[f"{ri_code}_previous"] = self.dati_proiettati[anno-1].get(ri_code, 0)
            calculated_flows_for_year = {}
            for item in sorted(structure_ff, key=lambda x: x.get('Ordine', 0)):
                if item.get('Tipo') == 'Calcolo':
                    voce_name = item['Voce']
                    try:
                        valore_calcolato = item['Formula'](flows_input)
                        calculated_flows_for_year[voce_name] = valore_calcolato
                        flows_input[voce_name] = valore_calcolato
                    except Exception:
                        calculated_flows_for_year[voce_name] = 0
            final_df[anno_str] = final_df['Voce'].map(calculated_flows_for_year).fillna("")
        return final_df
