"""
scripts/analyze_results.py
Analizza il database SQLite e genera report statistici per la documentazione.
"""
import sqlite3
import json
import os


def analyze_all_data(db_path="data/connect4_factory.db"):
    if not os.path.exists(db_path):
        print("Errore: Database non trovato!")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Statistiche Generali per Bot
    cursor.execute('''
        SELECT opponent, 
               COUNT(*) as total,
               SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as wins,
               AVG(moves_count) as avg_moves
        FROM games 
        GROUP BY opponent
    ''')
    rows = cursor.fetchall()

    print("\n" + "=" * 50)
    print("📊 REPORT PERFORMANCE IA (Dati per Documentazione)")
    print("=" * 50)

    # Formattazione per tabella Markdown
    markdown_table = "| Bot Avversario | Partite | Win Rate | Avg Moves | Bias Finale Medio |\n"
    markdown_table += "| :--- | :---: | :---: | :---: | :--- |\n"

    for row in rows:
        opp, total, wins, avg_m = row
        win_rate = (wins / total) * 100

        # Estraiamo il bias medio per questo bot (es. quanto è salito diagonal_weakness)
        cursor.execute('SELECT biases_json FROM games WHERE opponent = ? ORDER BY id DESC LIMIT 10', (opp,))
        last_biases = cursor.fetchall()

        # Calcoliamo una media rapida dei bias rilevati nelle ultime 10 partite
        avg_bias_str = "N/A"
        if last_biases:
            # Esempio: prendiamo il diagonal_weakness o center_weight a seconda del bot
            sample = json.loads(last_biases[0][0])
            avg_bias_str = ", ".join([f"{k}: {v:.2f}" for k, v in sample.items() if v != 1.0])

        markdown_table += f"| {opp} | {total} | {win_rate:.1f}% | {avg_m:.1f} | {avg_bias_str} |\n"

    print(markdown_table)

    # 2. Analisi della Curva di Apprendimento
    # Controlliamo se la media delle mosse scende nelle ultime partite rispetto alle prime
    for opp in [r[0] for r in rows]:
        cursor.execute('SELECT moves_count FROM games WHERE opponent = ? AND result = "win" ORDER BY id ASC', (opp,))
        moves = [m[0] for m in cursor.fetchall()]
        if len(moves) > 20:
            first_avg = sum(moves[:10]) / 10
            last_avg = sum(moves[-10:]) / 10
            improvement = ((first_avg - last_avg) / first_avg) * 100
            print(f"📈 Apprendimento vs {opp}: Efficienza migliorata del {improvement:.1f}%")

    conn.close()


if __name__ == "__main__":
    analyze_all_data()