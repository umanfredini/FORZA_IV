import sqlite3
import json
from datetime import datetime
import os


class GamePersistence:
    def __init__(self, db_path="data/connect4_factory.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        """ Crea la tabella delle partite se non esiste. """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS games
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           timestamp
                           TEXT,
                           opponent
                           TEXT,
                           result
                           TEXT,
                           moves_count
                           INTEGER,
                           biases_json
                           TEXT
                       )
                       ''')
        conn.commit()
        conn.close()

    def save_game_result(self, opponent_name, result, final_biases, moves_count):
        """ Salva i dati della partita nel database. """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Convertiamo il dizionario dei bias in stringa JSON per salvarlo nel DB
        biases_str = json.dumps(final_biases)

        cursor.execute('''
                       INSERT INTO games (timestamp, opponent, result, moves_count, biases_json)
                       VALUES (?, ?, ?, ?, ?)
                       ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                             opponent_name, result, moves_count, biases_str))

        conn.commit()
        conn.close()
        print(f"[DATABASE] Partita contro {opponent_name} archiviata.")

    def get_stats_for_docs(self, opponent_name):
        """ Estrae i dati pronti per la documentazione finale. """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
                       SELECT COUNT(*),
                              AVG(moves_count),
                              SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END)
                       FROM games
                       WHERE opponent = ?
                       ''', (opponent_name,))

        total, avg_moves, wins = cursor.fetchone()
        conn.close()

        if total == 0: return None

        return {
            "total_games": total,
            "win_rate": (wins / total) * 100 if wins else 0,
            "avg_moves": round(avg_moves, 2)
        }