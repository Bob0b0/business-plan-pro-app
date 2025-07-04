# financial_model.py - Progetto Business Plan Pro - versione 1.9 - 2025-06-25
# DEFINITIVO: Contiene la struttura originale e stabile per i flussi di cassa.

import pandas as pd

def format_number(x, pdf_format=False):
    try:
        num = int(x)
        if num < 0:
            abs_num = abs(num)
            formatted = f"({abs_num:,})".replace(",", ".")
        else:
            formatted = f"{num:,}".replace(",", ".")
        return formatted
    except (ValueError, TypeError):
        return str(x)

report_structure_ce = [
    {'Voce': 'CONTO ECONOMICO', 'Tipo': 'Intestazione', 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 100},
    {'Voce': 'Ricavi dalle vendite e prestazioni', 'Tipo': 'Dettaglio', 'ID_RI': 'RI01', 'Ordine': 110},
    {'Voce': 'Variazione rimanenze prodotti finiti', 'Tipo': 'Dettaglio', 'ID_RI': 'RI02', 'Ordine': 120},
    {'Voce': 'Altri ricavi e proventi', 'Tipo': 'Dettaglio', 'ID_RI': 'RI03', 'Ordine': 130},
    {'Voce': 'Costi capitalizzati', 'Tipo': 'Dettaglio', 'ID_RI': 'RI04', 'Ordine': 140}, 
    {'Voce': 'VALORE DELLA PRODUZIONE', 'Tipo': 'Calcolo', 'Formula_Refs': ['RI01', 'RI02', 'RI03', 'RI04'], 'Formula': lambda d: d.get('RI01', 0) + d.get('RI02', 0) + d.get('RI03', 0) + d.get('RI04', 0), 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 150},
    {'Voce': 'Acquisti di merci', 'Tipo': 'Dettaglio', 'ID_RI': 'RI05', 'Ordine': 160},
    {'Voce': 'Costi per servizi', 'Tipo': 'Dettaglio', 'ID_RI': 'RI06', 'Ordine': 170},
    {'Voce': 'Godimento di beni di terzi', 'Tipo': 'Dettaglio', 'ID_RI': 'RI07', 'Ordine': 180},
    {'Voce': 'Oneri diversi di gestione', 'Tipo': 'Dettaglio', 'ID_RI': 'RI08', 'Ordine': 190},
    {'Voce': 'Variazione rim. m.p. e merci', 'Tipo': 'Dettaglio', 'ID_RI': 'RI09', 'Ordine': 200},
    {'Voce': 'COSTI DELLA PRODUZIONE', 'Tipo': 'Calcolo', 'Formula_Refs': ['RI05', 'RI06', 'RI07', 'RI08', 'RI09'], 'Formula': lambda d: d.get('RI05', 0) + d.get('RI06', 0) + d.get('RI07', 0) + d.get('RI08', 0) - d.get('RI09', 0), 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 210},
    {'Voce': 'VALORE AGGIUNTO', 'Tipo': 'Calcolo', 'Formula_Refs': ['VALORE DELLA PRODUZIONE', 'COSTI DELLA PRODUZIONE'], 'Formula': lambda d: d.get('VALORE DELLA PRODUZIONE', 0) - d.get('COSTI DELLA PRODUZIONE', 0), 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 220},
    {'Voce': 'Personale', 'Tipo': 'Dettaglio', 'ID_RI': 'RI10', 'Ordine': 230},
    {'Voce': 'MARGINE OPERATIVO LORDO (EBITDA)', 'Tipo': 'Calcolo', 'Formula_Refs': ['VALORE AGGIUNTO', 'RI10'], 'Formula': lambda d: d.get('VALORE AGGIUNTO', 0) - d.get('RI10', 0), 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 240},
    {'Voce': 'Ammortamenti', 'Tipo': 'Dettaglio', 'ID_RI': 'RI11', 'Ordine': 250},
    {'Voce': 'Accantonamenti e sval. attivo corrente', 'Tipo': 'Dettaglio', 'ID_RI': 'RI12', 'Ordine': 260},
    {'Voce': 'RISULTATO OPERATIVO (EBIT)', 'Tipo': 'Calcolo', 'Formula_Refs': ['MARGINE OPERATIVO LORDO (EBITDA)', 'RI11', 'RI12'], 'Formula': lambda d: d.get('MARGINE OPERATIVO LORDO (EBITDA)', 0) - d.get('RI11', 0) - d.get('RI12', 0), 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 270},
    {'Voce': 'Proventi finanziari', 'Tipo': 'Dettaglio', 'ID_RI': 'RI14', 'Ordine': 280},
    {'Voce': 'Oneri finanziari', 'Tipo': 'Dettaglio', 'ID_RI': 'RI13', 'Ordine': 290},
    {'Voce': 'SALDO GESTIONE FINANZIARIA', 'Tipo': 'Calcolo', 'Formula_Refs': ['RI14', 'RI13'], 'Formula': lambda d: d.get('RI14', 0) - d.get('RI13', 0), 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 300},
    {'Voce': 'Altri ricavi e proventi non operativi', 'Tipo': 'Dettaglio', 'ID_RI': 'RI15', 'Ordine': 310},
    {'Voce': 'Altri costi non operativi', 'Tipo': 'Dettaglio', 'ID_RI': 'RI16', 'Ordine': 320},
    {'Voce': 'ALTRI COSTI E PROV. NON OP.', 'Tipo': 'Calcolo', 'Formula_Refs': ['RI15', 'RI16'], 'Formula': lambda d: d.get('RI15', 0) - d.get('RI16', 0), 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 330},
    {'Voce': 'RISULTATO LORDO (EBT)', 'Tipo': 'Calcolo', 'Formula_Refs': ['RISULTATO OPERATIVO (EBIT)', 'SALDO GESTIONE FINANZIARIA', 'ALTRI COSTI E PROV. NON OP.'], 'Formula': lambda d: d.get('RISULTATO OPERATIVO (EBIT)', 0) + d.get('SALDO GESTIONE FINANZIARIA', 0) + d.get('ALTRI COSTI E PROV. NON OP.', 0), 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 340},
    {'Voce': 'Imposte di esercizio', 'Tipo': 'Dettaglio', 'ID_RI': 'RI17', 'Ordine': 350},
    {'Voce': 'RISULTATO NETTO', 'Tipo': 'Dettaglio', 'ID_RI': 'RI18', 'Ordine': 360}, 
]

report_structure_sp = [
    {'Voce': 'STATO PATRIMONIALE', 'Tipo': 'Intestazione', 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 400},
    {'Voce': 'Soci c/sottoscrizioni', 'Tipo': 'Dettaglio', 'ID_RI': 'RI19', 'Ordine': 405},
    {'Voce': 'Immobilizzazioni immateriali', 'Tipo': 'Dettaglio', 'ID_RI': 'RI20', 'Ordine': 410},
    {'Voce': 'Immobilizzazioni materiali', 'Tipo': 'Dettaglio', 'ID_RI': 'RI21', 'Ordine': 420},
    {'Voce': 'Immobilizzazioni finanziarie', 'Tipo': 'Dettaglio', 'ID_RI': 'RI22', 'Ordine': 430},
    {'Voce': 'TOTALE IMMOBILIZZAZIONI', 'Tipo': 'Calcolo', 'Formula_Refs': ['RI20', 'RI21', 'RI22'], 'Formula': lambda d: d.get('RI20', 0) + d.get('RI21', 0) + d.get('RI22', 0), 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 440},
    {'Voce': 'Crediti verso clienti', 'Tipo': 'Dettaglio', 'ID_RI': 'RI23', 'Ordine': 450},
    {'Voce': 'Debiti verso fornitori', 'Tipo': 'Dettaglio', 'ID_RI': 'RI24', 'Ordine': 460},
    {'Voce': 'Rimanenze', 'Tipo': 'Dettaglio', 'ID_RI': 'RI25', 'Ordine': 470},
    {'Voce': 'Altri crediti b.t.', 'Tipo': 'Dettaglio', 'ID_RI': 'RI26', 'Ordine': 480},
    {'Voce': 'Altri debiti b.t.', 'Tipo': 'Dettaglio', 'ID_RI': 'RI27', 'Ordine': 490},
    {'Voce': 'CAPITALE CIRCOLANTE NETTO (CCN)', 'Tipo': 'Calcolo', 'Formula_Refs': ['RI23', 'RI24', 'RI25', 'RI26', 'RI27'], 'Formula': lambda d: d.get('RI23', 0) - d.get('RI24', 0) + d.get('RI25', 0) + d.get('RI26', 0) - d.get('RI27', 0), 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 500},
    {'Voce': 'TFR', 'Tipo': 'Dettaglio', 'ID_RI': 'RI28', 'Ordine': 510},
    {'Voce': 'Fondi rischi e oneri', 'Tipo': 'Dettaglio', 'ID_RI': 'RI29', 'Ordine': 520},
    {'Voce': 'Altri debiti m.l.t.', 'Tipo': 'Dettaglio', 'ID_RI': 'RI30', 'Ordine': 530},
    {'Voce': 'CAPITALE INVESTITO', 'Tipo': 'Calcolo', 'Formula_Refs': ['RI19', 'RI20', 'RI21', 'RI22', 'RI23', 'RI24', 'RI25', 'RI26', 'RI27', 'RI28', 'RI29', 'RI30'], 'Formula': lambda d: d.get('RI19', 0) + d.get('RI20', 0) + d.get('RI21', 0) + d.get('RI22', 0) + d.get('RI23', 0) - d.get('RI24', 0) + d.get('RI25', 0) + d.get('RI26', 0) - d.get('RI27', 0) - d.get('RI28', 0) - d.get('RI29', 0) - d.get('RI30', 0), 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 540},
    {'Voce': 'Liquidità', 'Tipo': 'Dettaglio', 'ID_RI': 'RI31', 'Ordine': 550, 'Visibile': False}, 
    {'Voce': 'Banche passive', 'Tipo': 'Dettaglio', 'ID_RI': 'RI33', 'Ordine': 552, 'Visibile': False}, 
    {'Voce': 'Posizione finanziaria netta', 'Tipo': 'Calcolo', 'Formula_Refs': ['RI33', 'RI31'], 'Formula': lambda d: d.get('RI33', 0) - d.get('RI31', 0), 'Grassetto': True, 'Maiuscolo': False, 'Ordine': 556}, 
    {'Voce': 'Patrimonio netto', 'Tipo': 'Dettaglio', 'ID_RI': 'RI32', 'Ordine': 560},
    {'Voce': 'CAPITALE IMPIEGATO', 'Tipo': 'Calcolo', 'Formula_Refs': ['RI31', 'RI32', 'RI33'], 'Formula': lambda d: -d.get('RI31', 0) + d.get('RI32', 0) + d.get('RI33', 0), 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 570}, 
]

report_structure_ff = [
    {'Voce': 'ANALISI DEI FLUSSI FINANZIARI', 'Tipo': 'Intestazione', 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 100},
    {'Voce': 'EBITDA', 'Tipo': 'Calcolo', 'Formula_Refs': ['MARGINE OPERATIVO LORDO (EBITDA)_current'], 'Formula': lambda d: d.get('MARGINE OPERATIVO LORDO (EBITDA)_current', 0), 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 110},
    {'Voce': 'Variazioni CCN', 'Tipo': 'Calcolo', 'Formula_Refs': ['CAPITALE CIRCOLANTE NETTO (CCN)_current', 'CAPITALE CIRCOLANTE NETTO (CCN)_previous'], 'Formula': lambda d: -(d.get('CAPITALE CIRCOLANTE NETTO (CCN)_current', 0) - d.get('CAPITALE CIRCOLANTE NETTO (CCN)_previous', 0)), 'Grassetto': False, 'Maiuscolo': False, 'Ordine': 120},
    {'Voce': 'Variazione TFR, fondi e altri mlt', 'Tipo': 'Calcolo', 'Formula_Refs': ['RI28_current', 'RI29_current', 'RI30_current', 'RI28_previous', 'RI29_previous', 'RI30_previous'], 'Formula': lambda d: (d.get('RI28_current', 0) + d.get('RI29_current', 0) + d.get('RI30_current', 0)) - (d.get('RI28_previous', 0) + d.get('RI29_previous', 0) + d.get('RI30_previous', 0)), 'Grassetto': False, 'Maiuscolo': False, 'Ordine': 130},
    {'Voce': 'FLUSSO MONETARIO OPERATIVO', 'Tipo': 'Calcolo', 'Formula_Refs': ['EBITDA', 'Variazioni CCN', 'Variazione TFR, fondi e altri mlt'], 'Formula': lambda d: d.get('EBITDA', 0) + d.get('Variazioni CCN', 0) + d.get('Variazione TFR, fondi e altri mlt', 0), 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 140},
    {'Voce': 'Flusso mon. da attività di investimento', 'Tipo': 'Calcolo', 'Formula_Refs': ['TOTALE IMMOBILIZZAZIONI_current', 'TOTALE IMMOBILIZZAZIONI_previous', 'RI11_current'], 'Formula': lambda d: -(d.get('TOTALE IMMOBILIZZAZIONI_current', 0) - d.get('TOTALE IMMOBILIZZAZIONI_previous', 0) + d.get('RI11_current', 0)), 'Grassetto': False, 'Maiuscolo': False, 'Ordine': 150},
    {'Voce': 'Aumenti di capitale', 'Tipo': 'Calcolo', 'Formula_Refs': ['RI32_current', 'RI32_previous', 'RI18_current'], 'Formula': lambda d: (d.get('RI32_current', 0) - d.get('RI32_previous', 0) - d.get('RI18_current', 0)), 'Grassetto': False, 'Maiuscolo': False, 'Ordine': 160},
    {'Voce': 'Gestione finanziaria', 'Tipo': 'Calcolo', 'Formula_Refs': ['SALDO GESTIONE FINANZIARIA_current'], 'Formula': lambda d: d.get('SALDO GESTIONE FINANZIARIA_current', 0), 'Grassetto': False, 'Maiuscolo': False, 'Ordine': 170},
    {'Voce': 'Gestione non operativa, accantonamenti e sval.', 'Tipo': 'Calcolo', 'Formula_Refs': ['RI12_current'], 'Formula': lambda d: -d.get('RI12_current', 0), 'Grassetto': False, 'Maiuscolo': False, 'Ordine': 180},
    {'Voce': 'Imposte', 'Tipo': 'Calcolo', 'Formula_Refs': ['RI17_current'], 'Formula': lambda d: -d.get('RI17_current', 0), 'Grassetto': False, 'Maiuscolo': False, 'Ordine': 190},
    {'Voce': 'FLUSSO MONETARIO NETTO', 'Tipo': 'Calcolo', 'Formula_Refs': ['FLUSSO MONETARIO OPERATIVO', 'Flusso mon. da attività di investimento', 'Aumenti di capitale', 'Gestione finanziaria', 'Gestione non operativa, accantonamenti e sval.', 'Imposte'], 'Formula': lambda d: sum(d.get(k, 0) for k in ['FLUSSO MONETARIO OPERATIVO', 'Flusso mon. da attività di investimento', 'Aumenti di capitale', 'Gestione finanziaria', 'Gestione non operativa, accantonamenti e sval.', 'Imposte']), 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 200},
    {'Voce': '', 'Tipo': 'Intestazione', 'Grassetto': False, 'Maiuscolo': False, 'Ordine': 210}, 
    {'Voce': 'Calcolo di conferma', 'Tipo': 'Intestazione', 'Grassetto': True, 'Maiuscolo': False, 'Ordine': 220},
    {'Voce': 'PFN INIZIO PERIODO', 'Tipo': 'Calcolo', 'Formula_Refs': ['Posizione finanziaria netta_previous'], 'Formula': lambda d: d.get('Posizione finanziaria netta_previous', 0), 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 230},
    {'Voce': 'PFN FINE PERIODO', 'Tipo': 'Calcolo', 'Formula_Refs': ['Posizione finanziaria netta_current'], 'Formula': lambda d: d.get('Posizione finanziaria netta_current', 0), 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 240},
    {'Voce': 'Variazione', 'Tipo': 'Calcolo', 'Formula_Refs': ['PFN FINE PERIODO', 'PFN INIZIO PERIODO'], 'Formula': lambda d: d.get('PFN FINE PERIODO', 0) - d.get('PFN INIZIO PERIODO', 0), 'Grassetto': True, 'Maiuscolo': True, 'Ordine': 250},
]

def calculate_all_reports(df_full_data, years_to_display, report_structure_ce, report_structure_sp, report_structure_ff):
    """
    Calcola tutti i valori per i report CE, SP e Flussi Finanziari per gli anni specificati.
    Restituisce un dizionario con i DataFrame finali per CE, SP e Flussi.
    """
    if df_full_data.empty:
        return {'ce': pd.DataFrame(), 'sp': pd.DataFrame(), 'ff': pd.DataFrame(), 
                'ce_export': pd.DataFrame(), 'sp_export': pd.DataFrame(), 
                'ff_export': pd.DataFrame(), 'error': "Nessun dato per il calcolo dei report."}

    df_full_data['importo'] = pd.to_numeric(df_full_data['importo'], errors='coerce').fillna(0).astype(int)
    
    df_pivot_by_id_ri_year = df_full_data.pivot_table(
        index='ID_RI',      
        columns='anno',     
        values='importo',   
        aggfunc='sum'       
    ).fillna(0).astype(int) 

    id_ri_to_ricla_name = df_full_data[['ID_RI', 'Ricla']].drop_duplicates().set_index('ID_RI')['Ricla'].to_dict()

    all_calculated_values_by_year = {year: {} for year in years_to_display}

    # Passo 1: Popolare i valori di dettaglio (RIxx) per tutti gli anni e report
    all_id_ris = set()
    for structure in [report_structure_ce, report_structure_sp, report_structure_ff]: 
        for item in structure:
            if item['Tipo'] == 'Dettaglio' and 'ID_RI' in item: 
                all_id_ris.add(item['ID_RI'])
    
    for year in years_to_display:
        for id_ri_val in all_id_ris:
            if year in df_pivot_by_id_ri_year.columns and id_ri_val in df_pivot_by_id_ri_year.index:
                value = df_pivot_by_id_ri_year.loc[id_ri_val, year]
                all_calculated_values_by_year[year][id_ri_val] = value
            else:
                all_calculated_values_by_year[year][id_ri_val] = 0

    # Passo 2: Risolvere le formule di CE e SP in ordine (per tutti gli anni)
    for structure in [report_structure_ce, report_structure_sp]:
        for item in sorted(structure, key=lambda x: x['Ordine']):
            if item['Tipo'] == 'Calcolo':
                voce_calcolata_name = item['Voce']
                for year in years_to_display:
                    try:
                        formula_input_dict = {}
                        for ref in item['Formula_Refs']:
                            val_ref = all_calculated_values_by_year[year].get(ref, 0)
                            formula_input_dict[ref] = val_ref
                            
                        calculated_value = item['Formula'](formula_input_dict)
                        all_calculated_values_by_year[year][voce_calcolata_name] = calculated_value
                    except KeyError as ke:
                        all_calculated_values_by_year[year][voce_calcolata_name] = 0
                    except Exception as e:
                        all_calculated_values_by_year[year][voce_calcolata_name] = 0

    # Passo 3: Risolvere le formule dei Flussi Finanziari
    current_year_val = years_to_display[-1] if years_to_display else None
    previous_year_val = years_to_display[0] if len(years_to_display) > 1 else (current_year_val - 1 if current_year_val else None)

    all_flows_input_values = {}
    
    if current_year_val is not None:
        # Aggiungi tutti i valori dell'anno corrente con suffisso _current
        for voce_or_id_ri, value in all_calculated_values_by_year[current_year_val].items():
            all_flows_input_values[f"{voce_or_id_ri}_current"] = value
        
        # Aggiungi tutti i valori dell'anno precedente con suffisso _previous
        if previous_year_val is not None and previous_year_val in all_calculated_values_by_year:
            for voce_or_id_ri, value in all_calculated_values_by_year[previous_year_val].items():
                all_flows_input_values[f"{voce_or_id_ri}_previous"] = value
        else: 
            # Se non ci sono dati per l'anno precedente, imposta tutti i valori _previous a 0
            for voce_or_id_ri in all_calculated_values_by_year[current_year_val].keys():
                all_flows_input_values[f"{voce_or_id_ri}_previous"] = 0

    calculated_flow_values = {}
    for item in sorted(report_structure_ff, key=lambda x: x['Ordine']):
        if item['Tipo'] == 'Calcolo':
            voce_name = item['Voce']
            try:
                calculated_value = item['Formula'](all_flows_input_values)
                calculated_flow_values[voce_name] = calculated_value
                all_flows_input_values[voce_name] = calculated_value
            except KeyError as ke:
                calculated_flow_values[voce_name] = 0
                all_flows_input_values[voce_name] = 0
            except Exception as e:
                calculated_flow_values[voce_name] = 0
                all_flows_input_values[voce_name] = 0

    # Costruzione DataFrame Finali
    final_reports = {} 
    
    # Costruzione CE
    report_data_ce_display = []
    for item in report_structure_ce:
        row = {'Voce': item['Voce']}
        if item.get('Maiuscolo', False): row['Voce'] = row['Voce'].upper()
        
        for year in years_to_display:
            val = all_calculated_values_by_year[year].get(item.get('ID_RI', item['Voce']), 0) 
            if item['Tipo'] == 'Intestazione': val = ""
            row[str(year)] = format_number(val) if val != 0 else ("0" if item['Tipo'] != 'Intestazione' else "")
        report_data_ce_display.append(row)
    final_reports['ce'] = pd.DataFrame(report_data_ce_display)

    # Costruzione SP
    report_data_sp_display = []
    for item in report_structure_sp:
        if item.get('Visibile', True) == False: continue
        row = {'Voce': item['Voce']}
        if item.get('Maiuscolo', False): row['Voce'] = row['Voce'].upper()
        for year in years_to_display:
            val = all_calculated_values_by_year[year].get(item.get('ID_RI', item['Voce']), 0) 
            if item['Tipo'] == 'Intestazione': val = ""
            row[str(year)] = format_number(val) if val != 0 else ("0" if item['Tipo'] != 'Intestazione' else "")
        report_data_sp_display.append(row)
    final_reports['sp'] = pd.DataFrame(report_data_sp_display)

    # Costruzione Flussi Finanziari
    report_data_ff_display = []
    for item in report_structure_ff:
        row = {'Voce': item['Voce']}
        if item.get('Maiuscolo', False): row['Voce'] = row['Voce'].upper()
        
        val = calculated_flow_values.get(item['Voce'], 0)
        if item['Tipo'] == 'Intestazione': val = ""
        row[str(current_year_val)] = format_number(val) if val != 0 else ("0" if item['Tipo'] != 'Intestazione' else "")
        
        report_data_ff_display.append(row)
    final_reports['ff'] = pd.DataFrame(report_data_ff_display)

    # DataFrame per Export (numerici, non formattati come stringhe)
    # Costruzione CE Export
    export_rows_ce = []
    for item in report_structure_ce:
        row_values = {'Voce': item['Voce']}
        if item.get('Maiuscolo', False): row_values['Voce'] = row_values['Voce'].upper()
        for year in years_to_display:
            val = all_calculated_values_by_year[year].get(item.get('ID_RI', item['Voce']), 0)
            if item['Tipo'] == 'Intestazione': val = ""
            row_values[str(year)] = val
        export_rows_ce.append(row_values)
    final_reports['ce_export'] = pd.DataFrame(export_rows_ce)

    # Costruzione SP Export
    export_rows_sp = []
    for item in report_structure_sp:
        if item.get('Visibile', True) == False: continue
        row_values = {'Voce': item['Voce']}
        if item.get('Maiuscolo', False): row_values['Voce'] = row_values['Voce'].upper()
        for year in years_to_display:
            val = all_calculated_values_by_year[year].get(item.get('ID_RI', item['Voce']), 0)
            if item['Tipo'] == 'Intestazione': val = ""
            row_values[str(year)] = val
        export_rows_sp.append(row_values)
    final_reports['sp_export'] = pd.DataFrame(export_rows_sp)
    
    # Costruzione Flussi Finanziari Export
    export_rows_ff = []
    for item in report_structure_ff:
        row_values = {'Voce': item['Voce']}
        if item.get('Maiuscolo', False): row_values['Voce'] = row_values['Voce'].upper()
        val = calculated_flow_values.get(item['Voce'], 0)
        if item['Tipo'] == 'Intestazione': val = ""
        row_values[str(current_year_val)] = val 
        export_rows_ff.append(row_values)
    final_reports['ff_export'] = pd.DataFrame(export_rows_ff)

    return final_reports

def format_number_html(x, add_euro=False):
    """
    Restituisce un numero formattato per l'HTML:
    - punto migliaia
    - negativi tra parentesi
    - opzionale ' €' alla fine
    """
    try:
        import pandas as pd
        if pd.isna(x) or float(x) == 0:
            return ""
        x = float(x)
        formatted = f"({abs(x):,.0f})" if x < 0 else f"{x:,.0f}"
        formatted = formatted.replace(",", ".")
        return formatted + " €" if add_euro else formatted
    except:
        return str(x)