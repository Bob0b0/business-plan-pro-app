# manutenzione.py - Versione 1.0 - 2025-06-12 17:55
import sqlite3

def aggiorna_cliente(nuovo_cliente):
    # Connessione al database SQLite
    conn = sqlite3.connect("business_plan_pro.db")
    cursor = conn.cursor()

    try:
        # Aggiorna tutti i record
        cursor.execute("UPDATE righe SET cliente = ?", (nuovo_cliente,))
        conn.commit()
        print(f"Tutti i record aggiornati con cliente = '{nuovo_cliente}'")
    except Exception as e:
        print("Errore durante l'aggiornamento:", e)
    finally:
        conn.close()

# Esegui direttamente se lo script è lanciato da terminale
if __name__ == "__main__":
    nuovo_cliente = input("Inserisci il nuovo nome cliente: ")
    aggiorna_cliente(nuovo_cliente)
