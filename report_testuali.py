# report_testuali.py - 2025-06-12 - v1.0
import os
import pandas as pd

def salva_report_ascii(df: pd.DataFrame, nome_report: str, output_dir: str = "reports"):
    """
    Salva un DataFrame in un file .txt in formato tabellare ASCII.
    Esempio di formato:
    +-----------------------------+-----------+-----------+
    | Voce                       |   2021    |   2022    |
    +-----------------------------+-----------+-----------+
    | Totale Attivo              | 1.234.567 | 1.345.678 |
    | Patrimonio Netto           |   567.890 |   612.345 |
    """

    if df.empty:
        raise ValueError("Il DataFrame fornito è vuoto. Nessun report generato.")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Costruisci intestazione
    header = ["Voce"] + [str(col) for col in df.columns[1:]]

    # Righe con valori
    righe = []
    for _, row in df.iterrows():
        voce = str(row.iloc[0])
        valori = [f"{int(val):,}".replace(",", ".") if isinstance(val, (int, float)) else str(val) for val in row.iloc[1:]]
        righe.append([voce] + valori)

    # Calcolo larghezza colonne
    col_widths = [max(len(str(cell)) for cell in col) for col in zip(header, *righe)]

    def format_row(row):
        return "| " + " | ".join(cell.ljust(w) for cell, w in zip(row, col_widths)) + " |"

    def format_separator():
        return "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

    output = [format_separator(), format_row(header), format_separator()]
    output += [format_row(r) for r in righe]
    output.append(format_separator())

    output_path = os.path.join(output_dir, f"{nome_report}.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        for line in output:
            f.write(line + "\n")

    return output_path
