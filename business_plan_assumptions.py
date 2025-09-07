# business_plan_assumptions.py - VERSIONE DEFINITIVA E CORRETTA - basata su originale
# Corretti tutti gli errori di sintassi precedenti.

import pandas as pd
import numpy as np
import sqlite3
import streamlit as st
from typing import Dict, List, Tuple, Optional

# Nome del database
def get_database_name():
    """Restituisce il database dell'utente corrente"""
    username = st.session_state.get('username')
    if username:
        return f"business_plan_{username}.db"
    return "business_plan_pro.db"

DATABASE_NAME = get_database_name()

# --- DEFINIZIONE DELLE ASSUMPTION ---
ASSUMPTION_DEFINITIONS = [
    {
        'id': 0,
        'nome': 'Ricavi di vendita',
        'descrizione': 'Incremento % previsto su anno precedente',
        'tipo': 'percentuale_incremento',
        'formula_storica': None,  # Calcolato come crescita anno su anno
        'unita': '%',
        'default_value': 3.0
    },
    {
        'id': 1,
        'nome': 'Altri ricavi/Ricavi vendite',
        'descrizione': 'Rapporto altri ricavi su ricavi vendite',
        'tipo': 'percentuale',
        'formula_storica': 'RI03/RI01',
        'unita': '%',
        'default_value': 2.0
    },
    {
        'id': 2,
        'nome': 'Oneri diversi (% su val. prod.)',
        'descrizione': 'Percentuale oneri diversi su valore produzione',
        'tipo': 'percentuale',
        'formula_storica': 'RI08/(RI01+RI02+RI03+RI04)',
        'unita': '%',
        'default_value': 1.5
    },
    {
        'id': 3,
        'nome': 'Rotazione magazzino',
        'descrizione': 'Indice di rotazione del magazzino',
        'tipo': 'indice',
        'formula_storica': 'RI01/RI25',
        'unita': 'volte',
        'default_value': 4.0
    },
    {
        'id': 4,
        'nome': 'Costo del venduto',
        'descrizione': 'Percentuale costo del venduto su ricavi',
        'tipo': 'percentuale',
        'formula_storica': 'RI05/RI01',  # Corretto
        'unita': '%',
        'default_value': 60.0
    },
    {
        'id': 5,
        'nome': 'Servizi/Val.produzione',
        'descrizione': 'Percentuale servizi su valore produzione',
        'tipo': 'percentuale',
        'formula_storica': 'RI06/(RI01+RI02+RI03+RI04)',
        'unita': '%',
        'default_value': 15.0
    },
    {
        'id': 6,
        'nome': 'Giorni dilazione clienti',
        'descrizione': 'Giorni medi di incasso crediti clienti',
        'tipo': 'giorni',
        'formula_storica': 'RI23*365/((RI01+RI02+RI03+RI04)*1.22)',
        'unita': 'giorni',
        'default_value': 60
    },
    {
        'id': 7,
        'nome': 'Giorni dilazione fornitori',
        'descrizione': 'Giorni medi di pagamento fornitori',
        'tipo': 'giorni',
        'formula_storica': '(RI24*365)/((RI05+RI06+RI07+RI08)*1.22)',
        'unita': 'giorni',
        'default_value': 45
    },
    {
        'id': 8,
        'nome': 'Costi capitalizzati',
        'descrizione': 'Percentuale costi capitalizzati su ricavi',
        'tipo': 'percentuale',
        'formula_storica': 'RI04/RI01',
        'unita': '%',
        'default_value': 0.5
    },
    {
        'id': 9,
        'nome': 'Altri crediti/Clienti',
        'descrizione': 'Rapporto altri crediti su crediti clienti',
        'tipo': 'percentuale',
        'formula_storica': 'RI26/RI23',
        'unita': '%',
        'default_value': 25.0
    },
    {
        'id': 10,
        'nome': 'Altri debiti/Fornitori',
        'descrizione': 'Rapporto altri debiti su debiti fornitori',
        'tipo': 'percentuale',
        'formula_storica': 'RI27/RI24',
        'unita': '%',
        'default_value': 30.0
    },
    {
        'id': 11,
        'nome': 'Tasso medio debiti banche',
        'descrizione': 'Tasso di interesse medio sui debiti bancari',
        'tipo': 'percentuale',
        'formula_storica': 'RI13/((RI33_current+RI33_previous)/2)',
        'unita': '%',
        'default_value': 4.5
    },
    {
        'id': 12,
        'nome': 'Incidenza costo del lavoro',
        'descrizione': 'Percentuale costo lavoro su valore produzione',
        'tipo': 'percentuale',
        'formula_storica': 'RI10/(RI01+RI02+RI03+RI04)',
        'unita': '%',
        'default_value': 25.0
    },
    {
        'id': 13,
        'nome': 'Godimento beni di terzi',
        'descrizione': 'Importo annuo per godimento beni di terzi',
        'tipo': 'importo',
        'formula_storica': None,
        'unita': '€',
        'default_value': 50000
    },
    # --- NUOVE ASSUMPTION AGGIUNTE QUI ---
    {
        'id': 14,
        'nome': 'Aliquota media Imm. immateriali',
        'descrizione': 'Aliquota di ammortamento media per le immobilizzazioni immateriali',
        'tipo': 'percentuale',
        'formula_storica': None,
        'unita': '%',
        'default_value': 20.0
    },
    {
        'id': 15,
        'nome': 'Aliquota media Imm. materiali',
        'descrizione': 'Aliquota di ammortamento media per le immobilizzazioni materiali',
        'tipo': 'percentuale',
        'formula_storica': None,
        'unita': '%',
        'default_value': 10.0
    },
    {
        'id': 16,
        'nome': 'Investimenti in Imm. immateriali',
        'descrizione': 'Importo annuo di nuovi investimenti in immobilizzazioni immateriali',
        'tipo': 'importo',
        'formula_storica': None,
        'unita': '€',
        'default_value': 0
    },
    {
        'id': 17,
        'nome': 'Investimenti in Imm. materiali',
        'descrizione': 'Importo annuo di nuovi investimenti in immobilizzazioni materiali',
        'tipo': 'importo',
        'formula_storica': None,
        'unita': '€',
        'default_value': 0
    },
    {
        'id': 18,
        'nome': 'Immobilizzazioni finanziarie (RI22)',
        'descrizione': 'Valore delle immobilizzazioni finanziarie (input manuale)',
        'tipo': 'importo',
        'formula_storica': 'RI22',
        'unita': '€',
        'default_value': 0
    },
    {
        'id': 19,
        'nome': 'TFR (RI28)',
        'descrizione': 'Fondo Trattamento di Fine Rapporto (input manuale)',
        'tipo': 'importo',
        'formula_storica': 'RI28',
        'unita': '€',
        'default_value': 0
    },
    {
        'id': 20,
        'nome': 'Fondi rischi e oneri (RI29)',
        'descrizione': 'Valore dei fondi per rischi e oneri (input manuale)',
        'tipo': 'importo',
        'formula_storica': 'RI29',
        'unita': '€',
        'default_value': 0
    },
    {
        'id': 21,
        'nome': 'Altri debiti m.l.t. (RI30)',
        'descrizione': 'Valore degli altri debiti a medio/lungo termine (input manuale)',
        'tipo': 'importo',
        'formula_storica': 'RI30',
        'unita': '€',
        'default_value': 0
    },
    {
        'id': 22,
        'nome': 'Accantonamenti e svalutazioni (RI12)',
        'descrizione': 'Importo annuo di accantonamenti e svalutazioni',
        'tipo': 'importo',
        'formula_storica': 'RI12',
        'unita': '€',
        'default_value': 0
    },
    {
        'id': 23,
        'nome': 'Proventi finanziari (RI14)',
        'descrizione': 'Importo annuo di proventi finanziari',
        'tipo': 'importo',
        'formula_storica': 'RI14',
        'unita': '€',
        'default_value': 0
    },
    {
        'id': 24,
        'nome': 'Altri costi non operativi (RI15)',
        'descrizione': 'Importo annuo di altri costi non operativi',
        'tipo': 'importo',
        'formula_storica': 'RI15',
        'unita': '€',
        'default_value': 0
    },
    {
        'id': 25,
        'nome': 'Altri ricavi non operativi (RI16)',
        'descrizione': 'Importo annuo di altri ricavi non operativi',
        'tipo': 'importo',
        'formula_storica': 'RI16',
        'unita': '€',
        'default_value': 0
    }
]

# --- MAPPATURA VOCI RI ---
RI_CODES = {
    'RI01': 'Ricavi dalle vendite e prestazioni',
    'RI02': 'Variazione rimanenze prodotti finiti',
    'RI03': 'Altri ricavi e proventi',
    'RI04': 'Costi capitalizzati',
    'RI05': 'Acquisti di merci',
    'RI06': 'Costi per servizi',
    'RI07': 'Godimento di beni di terzi',
    'RI08': 'Oneri diversi di gestione',
    'RI09': 'Variazione rim m.p. e merci',
    'RI10': 'Personale',
    'RI11': 'Ammortamenti',
    'RI12': 'Accantonamenti e sval. attivo corrente',
    'RI13': 'Oneri finanziari',
    'RI14': 'Proventi finanziari',
    'RI15': 'Altri costi non operativi',
    'RI16': 'Altri ricavi e proventi non operativi',
    'RI17': 'Imposte di esercizio',
    'RI18': 'RISULTATO NETTO',
    'RI19': 'Soci c/sottoscrizioni',
    'RI20': 'Immobilizzazioni immateriali',
    'RI21': 'Immobilizzazioni materiali',
    'RI22': 'Immobilizzazioni finanziarie',
    'RI23': 'Crediti verso clienti',
    'RI24': 'Debiti verso fornitori',
    'RI25': 'Rimanenze',
    'RI26': 'Altri crediti b.t.',
    'RI27': 'Altri debiti b.t.',
    'RI28': 'TFR',
    'RI29': 'Fondi rischi e oneri',
    'RI30': 'Altri debiti m.l.t.',
    'RI31': 'Liquidità',
    'RI32': 'Patrimonio netto',
    'RI33': 'Banche passive'
}


class BusinessPlanAssumptions:
    """Classe per gestire le assumption del Business Plan"""
    
    def __init__(self, cliente: str):
        self.cliente = cliente
        self.dati_storici = {}
        self.medie_storiche = {}
        self.assumptions = {}
    
    def carica_dati_storici(self, anni_storici: List[int]) -> Dict:
        """Carica i dati storici dal database per il calcolo delle medie"""
        
        conn = None
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            
            # Query per caricare tutti i dati storici
            query = """
            SELECT 
                r.anno, r.importo, c.ID_RI
            FROM righe r
            JOIN conti c ON r.Id_co = c.id_co
            WHERE r.anno IN ({}) AND r.cliente = ?
            ORDER BY r.anno, c.ID_RI
            """.format(','.join(['?' for _ in anni_storici]))
            
            params = [str(anno) for anno in anni_storici] + [self.cliente]
            df = pd.read_sql_query(query, conn, params=params)
            
            # Pivot per avere anni come colonne e ID_RI come righe
            pivot_df = df.pivot_table(
                index='ID_RI',
                columns='anno', 
                values='importo',
                aggfunc='sum'
            ).fillna(0)
            
            self.dati_storici = pivot_df.to_dict()
            return self.dati_storici
            
        except Exception as e:
            print(f"Errore nel caricamento dati storici: {e}")
            return {}
        finally:
            if conn:
                conn.close()
    
    def calcola_medie_storiche(self, anni_storici: List[int]) -> Dict:
        """Calcola le medie storiche per tutte le assumption"""
        
        if not self.dati_storici:
            self.carica_dati_storici(anni_storici)
        
        medie = {}
        
        for assumption in ASSUMPTION_DEFINITIONS:
            ass_id = assumption['id']
            formula = assumption['formula_storica']
            
            try:
                if formula and formula != 'None':
                    valori_anni = []
                    
                    for anno in anni_storici:
                        if anno in self.dati_storici:
                            valore_calcolato = self._calcola_formula_storica(formula, anno)
                            if valore_calcolato is not None and not np.isnan(valore_calcolato):
                                valori_anni.append(valore_calcolato)
                    
                    if valori_anni:
                        if assumption['tipo'] == 'percentuale_incremento':
                            # Per i ricavi, calcola la crescita media
                            crescite = []
                            for i in range(1, len(valori_anni)):
                                if valori_anni[i-1] != 0:
                                    crescita = ((valori_anni[i] / valori_anni[i-1]) - 1) * 100
                                    crescite.append(crescita)
                            media = np.mean(crescite) if crescite else assumption['default_value']
                        else:
                            media = np.mean(valori_anni)
                        
                        medie[ass_id] = round(media, 2)
                    else:
                        medie[ass_id] = assumption['default_value']
                else:
                    medie[ass_id] = assumption['default_value']
                    
            except Exception as e:
                print(f"Errore nel calcolo assumption {ass_id}: {e}")
                medie[ass_id] = assumption['default_value']
        
        self.medie_storiche = medie
        return medie
    
    def _calcola_formula_storica(self, formula: str, anno: int) -> Optional[float]:
        """Calcola il valore di una formula per un anno specifico"""
        
        try:
            # Sostituisce i codici RI con i valori effettivi
            formula_eval = formula
            
            # Gestione formule speciali
            if 'RI33_current' in formula and 'RI33_previous' in formula:
                # Formula per tasso bancario
                ri33_current = self._get_valore_ri('RI33', anno)
                ri33_previous = self._get_valore_ri('RI33', anno - 1)
                ri13 = self._get_valore_ri('RI13', anno)
                
                if ri33_current is not None and ri33_previous is not None and ri13 is not None:
                    media_debiti = (ri33_current + ri33_previous) / 2
                    if media_debiti != 0:
                        return (ri13 / media_debiti) * 100
                return None
            else:
                # Sostituisce tutti i codici RI
                import re
                codici_ri = re.findall(r'RI\d+', formula)
                
                for codice in set(codici_ri):
                    valore = self._get_valore_ri(codice, anno)
                    if valore is None:
                        return None
                    formula_eval = formula_eval.replace(codice, str(valore))
                
                # Valuta la formula
                result = eval(formula_eval)
                
                # Converti in percentuale se necessario
                assumption = next((a for a in ASSUMPTION_DEFINITIONS if a['formula_storica'] == formula), None)
                if assumption and assumption['tipo'] in ['percentuale'] and result is not None:
                    result = result * 100
                
                return result
                
        except Exception as e:
            print(f"Errore nella formula {formula} per anno {anno}: {e}")
            return None
    
    def _get_valore_ri(self, codice_ri: str, anno: int) -> Optional[float]:
        """Ottiene il valore di un codice RI per un anno specifico"""
        
        try:
            if anno in self.dati_storici and codice_ri in self.dati_storici[anno]:
                return float(self.dati_storici[anno][codice_ri])
            return 0.0  # Se non esiste, restituisce 0
        except:
            return None
    
    def imposta_assumptions_manuali(self, assumptions_dict: Dict[int, Dict[int, float]]):
        """Imposta le assumption manuali per gli anni del BP"""
        self.assumptions = assumptions_dict
    
    def get_assumption_value(self, assumption_id: int, anno_index: int) -> float:
        """
        Ottiene il valore di un'assumption per un dato indice (1=primo anno dopo base).
        Converte l'indice in anno effettivo se necessario.
        """
        try:
            anni_disponibili = list(sorted(next(iter(self.assumptions.values())).keys()))
            if 0 <= anno_index - 1 < len(anni_disponibili):
                anno_bp = anni_disponibili[anno_index - 1]
            else:
                return 0.0
            if assumption_id in self.assumptions and anno_bp in self.assumptions[assumption_id]:
                return self.assumptions[assumption_id][anno_bp]
            if assumption_id in self.medie_storiche:
                return self.medie_storiche[assumption_id]
            assumption = next((a for a in ASSUMPTION_DEFINITIONS if a['id'] == assumption_id), None)
            return assumption['default_value'] if assumption else 0.0
        except Exception as e:
            print(f"❌ Errore get_assumption_value({assumption_id}, {anno_index}): {e}")
            return 0.0
def get_anni_disponibili(cliente: str) -> List[int]:
    """Ottiene la lista degli anni disponibili per un cliente"""
    
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        
        query = """
        SELECT DISTINCT anno 
        FROM righe 
        WHERE cliente = ? 
        ORDER BY anno DESC
        """
        
        df = pd.read_sql_query(query, conn, params=[cliente])
        return [int(anno) for anno in df['anno'].tolist()]
        
    except Exception as e:
        print(f"Errore nel recupero anni: {e}")
        return []
    finally:
        if conn:
            conn.close()


def determina_anno_base(cliente: str) -> Optional[int]:
    """Determina l'anno più recente (N0) per un cliente"""
    
    anni = get_anni_disponibili(cliente)
    return max(anni) if anni else None


def genera_anni_business_plan(anno_base: int, durata: int) -> List[int]:
    """Genera la lista degli anni del Business Plan"""
    
    return [anno_base + i for i in range(durata + 1)]  # Include anno base + anni futuri