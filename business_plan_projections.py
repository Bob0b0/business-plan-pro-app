# business_plan_projections.py - Progetto Business Plan Pro - versione 1.2 - 2025-06-21
# Modulo per le proiezioni del Business Plan basate su assumption
# AGGIUNTO CALCOLO ITERATIVO PER ONERI FINANZIARI (RI13)

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from business_plan_assumptions import BusinessPlanAssumptions, ASSUMPTION_DEFINITIONS, RI_CODES


class BusinessPlanProjections:
    """Classe per gestire le proiezioni del Business Plan"""
    
    def __init__(self, cliente: str, anno_base: int, durata: int):
        self.cliente = cliente
        self.anno_base = anno_base
        self.durata = durata
        self.anni_bp = [anno_base + i for i in range(durata + 1)]
        self.assumptions = BusinessPlanAssumptions(cliente)
        self.dati_proiettati = {}
        
    def inizializza_con_dati_storici(self, dati_storici: Dict) -> None:
        """Inizializza le proiezioni con i dati dell'anno base"""
        for codice_ri in RI_CODES.keys():
            if self.anno_base not in self.dati_proiettati:
                self.dati_proiettati[self.anno_base] = {}
            valore_base = dati_storici.get(self.anno_base, {}).get(codice_ri, 0)
            self.dati_proiettati[self.anno_base][codice_ri] = valore_base
    
    def calcola_proiezioni(self) -> Dict:
        """Calcola tutte le proiezioni per gli anni del Business Plan"""
        for i, anno in enumerate(self.anni_bp[1:], 1):
            self.dati_proiettati[anno] = {}
            self._calcola_anno_proiezione(anno, i)
        return self.dati_proiettati
    
    def _calcola_anno_proiezione(self, anno: int, anno_indice: int) -> None:
        """Calcola le proiezioni per un singolo anno utilizzando un ciclo iterativo per risolvere la circolarità."""
        
        anno_precedente = anno - 1
        dati_prec = self.dati_proiettati[anno_precedente]
        dati_curr = self.dati_proiettati[anno]

        # --- INIZIO CICLO ITERATIVO PER LA CIRCOLARITÀ ---
        
        iteration_count = 0
        max_iterations = 100  # Limite di sicurezza per evitare loop infiniti
        tolerance = 0.01  # Tolleranza di 1 centesimo per la convergenza

        # Stima iniziale per RI13 (Oneri Finanziari)
        tasso_interesse = self.assumptions.get_assumption_value(11, anno_indice) / 100
        dati_curr['RI13'] = dati_prec.get('RI33', 0) * tasso_interesse

        while True:
            iteration_count += 1
            ri13_inizio_ciclo = dati_curr['RI13']

            # --- FASE 1: CALCOLO CONTO ECONOMICO FINO A EBIT ---
            crescita_ricavi = self.assumptions.get_assumption_value(0, anno_indice) / 100
            dati_curr['RI01'] = dati_prec['RI01'] * (1 + crescita_ricavi)
            
            perc_altri_ricavi = self.assumptions.get_assumption_value(1, anno_indice) / 100
            dati_curr['RI03'] = dati_curr['RI01'] * perc_altri_ricavi
            
            perc_costi_cap = self.assumptions.get_assumption_value(8, anno_indice) / 100
            dati_curr['RI04'] = dati_curr['RI01'] * perc_costi_cap

            rotazione_magazzino = self.assumptions.get_assumption_value(3, anno_indice)
            dati_curr['RI25'] = dati_curr['RI01'] / rotazione_magazzino if rotazione_magazzino > 0 else dati_prec['RI25']
            dati_curr['RI02'] = dati_curr['RI25'] - dati_prec['RI25']

            valore_produzione = dati_curr['RI01'] + dati_curr['RI02'] + dati_curr['RI03'] + dati_curr['RI04']

            # Costi
            dati_curr['RI05'] = dati_curr['RI01'] * (self.assumptions.get_assumption_value(4, anno_indice) / 100)
            dati_curr['RI06'] = valore_produzione * (self.assumptions.get_assumption_value(5, anno_indice) / 100)
            dati_curr['RI07'] = self.assumptions.get_assumption_value(13, anno_indice)
            dati_curr['RI08'] = valore_produzione * (self.assumptions.get_assumption_value(2, anno_indice) / 100)
            dati_curr['RI10'] = valore_produzione * (self.assumptions.get_assumption_value(12, anno_indice) / 100)
            dati_curr['RI09'] = 0

            # Ammortamenti
            aliquota_A = self.assumptions.get_assumption_value(14, anno_indice) / 100
            aliquota_B = self.assumptions.get_assumption_value(15, anno_indice) / 100
            investimenti_C = self.assumptions.get_assumption_value(16, anno_indice)
            investimenti_D = self.assumptions.get_assumption_value(17, anno_indice)
            ammortamenti_immateriali_E = (dati_prec['RI20'] + investimenti_C) * aliquota_A
            ammortamenti_materiali_F = (dati_prec['RI21'] + investimenti_D) * aliquota_B
            dati_curr['RI11'] = ammortamenti_immateriali_E + ammortamenti_materiali_F

            # Altri input manuali
            dati_curr['RI12'] = self.assumptions.get_assumption_value(22, anno_indice)
            dati_curr['RI14'] = self.assumptions.get_assumption_value(23, anno_indice)
            dati_curr['RI15'] = self.assumptions.get_assumption_value(24, anno_indice)
            dati_curr['RI16'] = self.assumptions.get_assumption_value(25, anno_indice)

            # Calcolo EBIT
            costi_produzione = (dati_curr['RI05'] + dati_curr['RI06'] + dati_curr['RI07'] + dati_curr['RI08'] + dati_curr['RI09'])
            ebitda = valore_produzione - costi_produzione - dati_curr['RI10']
            ebit = ebitda - dati_curr['RI11'] - dati_curr['RI12']

            # --- FASE 2: CALCOLO RISULTATO NETTO E PATRIMONIO NETTO ---
            # Usa il valore di RI13 calcolato nel ciclo precedente (o la stima iniziale)
            risultato_lordo = ebit + dati_curr['RI14'] - dati_curr['RI13'] + dati_curr['RI16'] - dati_curr['RI15']
            dati_curr['RI17'] = risultato_lordo * 0.28 if risultato_lordo > 0 else 0
            dati_curr['RI18'] = risultato_lordo - dati_curr['RI17']
            dati_curr['RI32'] = dati_prec['RI32'] + dati_curr['RI18']
            
            # --- FASE 3: CALCOLO STATO PATRIMONIALE ---
            dati_curr['RI20'] = dati_prec['RI20'] + investimenti_C - ammortamenti_immateriali_E
            dati_curr['RI21'] = dati_prec['RI21'] + investimenti_D - ammortamenti_materiali_F
            dati_curr['RI22'] = self.assumptions.get_assumption_value(18, anno_indice)
            dati_curr['RI28'] = self.assumptions.get_assumption_value(19, anno_indice)
            dati_curr['RI29'] = self.assumptions.get_assumption_value(20, anno_indice)
            dati_curr['RI30'] = self.assumptions.get_assumption_value(21, anno_indice)
            dati_curr['RI19'] = dati_prec['RI19']

            giorni_clienti = self.assumptions.get_assumption_value(6, anno_indice)
            dati_curr['RI23'] = (valore_produzione * 1.22 * giorni_clienti) / 365
            costi_fornitori = dati_curr['RI05'] + dati_curr['RI06'] + dati_curr['RI07'] + dati_curr['RI08']
            giorni_fornitori = self.assumptions.get_assumption_value(7, anno_indice)
            dati_curr['RI24'] = (costi_fornitori * 1.22 * giorni_fornitori) / 365
            dati_curr['RI26'] = dati_curr['RI23'] * (self.assumptions.get_assumption_value(9, anno_indice) / 100)
            dati_curr['RI27'] = dati_curr['RI24'] * (self.assumptions.get_assumption_value(10, anno_indice) / 100)

            # --- FASE 4: CHIUSURA FINANZIARIA E RICALCOLO DI RI13 ---
            pfn_corrente = self._calcola_equilibrio_finanziario(anno, anno_precedente)
            pfn_precedente = self.dati_proiettati[anno_precedente].get('RI33', 0) - self.dati_proiettati[anno_precedente].get('RI31', 0)
            
            # Ricalcola RI13 con la PFN media corretta
            pfn_media = (pfn_precedente + pfn_corrente) / 2
            ri13_fine_ciclo = pfn_media * tasso_interesse
            
            # Aggiorna il valore di RI13 per il prossimo ciclo (o per il valore finale)
            dati_curr['RI13'] = ri13_fine_ciclo

            # --- FASE 5: CONTROLLO CONVERGENZA ---
            if abs(ri13_fine_ciclo - ri13_inizio_ciclo) < tolerance:
                break  # Il valore si è stabilizzato, esci dal loop
            
            if iteration_count > max_iterations:
                print(f"ATTENZIONE: Il calcolo iterativo per l'anno {anno} non è convergente dopo {max_iterations} iterazioni.")
                break # Esce per sicurezza

    def _calcola_equilibrio_finanziario(self, anno: int, anno_precedente: int) -> float:
        """
        Calcola l'equilibrio finanziario per determinare liquidità e debiti bancari.
        Restituisce la Posizione Finanziaria Netta (PFN) calcolata.
        """
        dati_curr = self.dati_proiettati[anno]
        dati_prec = self.dati_proiettati[anno_precedente]

        ccn = (dati_curr.get('RI23',0) - dati_curr.get('RI24',0) + dati_curr.get('RI25',0) + 
               dati_curr.get('RI26',0) - dati_curr.get('RI27',0))
        
        immobilizzazioni = (dati_curr.get('RI20',0) + dati_curr.get('RI21',0) + dati_curr.get('RI22',0))
        
        capitale_investito = (dati_curr.get('RI19',0) + immobilizzazioni + ccn - 
                              dati_curr.get('RI28',0) - dati_curr.get('RI29',0) - dati_curr.get('RI30',0))
        
        pfn_target = capitale_investito - dati_curr.get('RI32',0)
        
        dati_curr['RI31'] = dati_prec.get('RI31', 0)
        dati_curr['RI33'] = pfn_target + dati_curr['RI31']
        
        if dati_curr['RI33'] < 0:
            dati_curr['RI31'] -= dati_curr['RI33']
            dati_curr['RI33'] = 0
            
        # Calcola e restituisce la PFN finale
        pfn_calcolata = dati_curr['RI33'] - dati_curr['RI31']
        return pfn_calcolata

    # ... (gli altri metodi get_dataframe_proiezioni, get_report_ce, ecc. rimangono invariati) ...
    def get_dataframe_proiezioni(self) -> pd.DataFrame:
        """Restituisce un DataFrame con tutte le proiezioni"""
        if not self.dati_proiettati: return pd.DataFrame()
        df_list = []
        for codice_ri, descrizione in RI_CODES.items():
            row = {'Codice': codice_ri, 'Descrizione': descrizione}
            for anno in self.anni_bp:
                row[str(anno)] = self.dati_proiettati.get(anno, {}).get(codice_ri, 0)
            df_list.append(row)
        return pd.DataFrame(df_list)
    
    def get_report_ce_proiezioni(self) -> pd.DataFrame:
        """Restituisce il Conto Economico proiettato"""
        import financial_model
        return self._build_report_from_structure(financial_model.report_structure_ce, "Conto Economico Business Plan")
    
    def get_report_sp_proiezioni(self) -> pd.DataFrame:
        """Restituisce lo Stato Patrimoniale proiettato"""
        import financial_model
        return self._build_report_from_structure(financial_model.report_structure_sp, "Stato Patrimoniale Business Plan")
    
    def _build_report_from_structure(self, structure: List[Dict], title: str) -> pd.DataFrame:
        """Costruisce un report utilizzando la struttura e i dati proiettati"""
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
                    except Exception as e:
                        print(f"Errore nel calcolo {voce_name} per anno {anno}: {e}")
                        calculated_values_by_year[anno][voce_name] = 0
        
        for item in structure:
            if not item.get('Visibile', True): continue
            row = {'Voce': item['Voce'].upper() if item.get('Maiuscolo', False) else item['Voce']}
            for anno in self.anni_bp:
                if item['Tipo'] == 'Intestazione': val = ""
                elif item['Tipo'] == 'Dettaglio' and 'ID_RI' in item: val = self.dati_proiettati.get(anno, {}).get(item['ID_RI'], 0)
                elif item['Tipo'] == 'Calcolo': val = calculated_values_by_year[anno].get(item['Voce'], 0)
                else: val = 0
                row[str(anno)] = val
            report_data.append(row)
        
        return pd.DataFrame(report_data)