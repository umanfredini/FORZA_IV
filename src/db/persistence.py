import sqlite3
import json
from datetime import datetime
import os

# Calcolo automatico del percorso
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "connect4_factory.db")


class GamePersistence:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        # Crea la cartella 'data' se non esiste
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        """ Crea le tabelle necessarie se non esistono. """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 1. Tabella Storico Partite
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

        # 2. Tabella Opening Book (Apprendimento Aperture)
        # Chiave primaria composta (stato + mossa) per evitare duplicati
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS opening_book
                       (
                           state_hash
                           TEXT,
                           move_col
                           INTEGER,
                           visits
                           INTEGER
                           DEFAULT
                           0,
                           total_score
                           INTEGER
                           DEFAULT
                           0,
                           PRIMARY
                           KEY
                       (
                           state_hash,
                           move_col
                       )
                           )
                       ''')

        conn.commit()
        conn.close()

    def save_game_result(self, opponent_name, result, final_biases, moves_count):
        """
        Salva i dati della partita.
        result: deve essere una stringa tipo 'win', 'loss', 'draw'
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        biases_str = json.dumps(final_biases)

        cursor.execute('''
                       INSERT INTO games (timestamp, opponent, result, moves_count, biases_json)
                       VALUES (?, ?, ?, ?, ?)
                       ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                             opponent_name, result, moves_count, biases_str))

        conn.commit()
        conn.close()

    def get_latest_biases(self, opponent_name):
        """ Recupera l'ultimo profilo psicologico noto di questo avversario. """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
                       SELECT biases_json
                       FROM games
                       WHERE opponent = ?
                       ORDER BY id DESC LIMIT 1
                       ''', (opponent_name,))

        row = cursor.fetchone()
        conn.close()

        if row:
            try:
                return json.loads(row[0])
            except json.JSONDecodeError:
                return None
        return None

    # --- METODI OTTIMIZZATI PER L'APERTURA ---

    def update_opening_move(self, state_hash, move_col, score_delta):
        """
        Aggiorna statistiche mossa usando UPSERT (Insert o Update atomico).
        Molto più veloce e sicuro del "Select -> If -> Update/Insert".
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Questa query fa tutto da sola:
        # 1. Prova a INSERIRE una nuova riga.
        # 2. Se esiste già (conflitto su Primary Key), AGGIORNA i valori esistenti.
        cursor.execute('''
                       INSERT INTO opening_book (state_hash, move_col, visits, total_score)
                       VALUES (?, ?, 1, ?) ON CONFLICT(state_hash, move_col) DO
                       UPDATE SET
                           visits = visits + 1,
                           total_score = total_score + excluded.total_score
                       ''', (state_hash, move_col, score_delta))

        conn.commit()
        conn.close()

    def get_opening_stats(self, state_hash):
        """
        Restituisce tutte le mosse note per questo stato.
        Output: lista di tuple [(move_col, visits, total_score), ...]
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
                       SELECT move_col, visits, total_score
                       FROM opening_book
                       WHERE state_hash = ?
                       ''', (state_hash,))

        results = cursor.fetchall()
        conn.close()
        return results

    def get_stats_for_docs(self, opponent_name):
        """ Calcola statistiche aggregate per visualizzazione. """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Assumiamo che 'result' sia salvato come 'win' nel DB quando vince l'umano
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
            "avg_moves": round(avg_moves if avg_moves else 0, 2)
        }

    def get_total_stats_by_bot(self, opponent_name):
        """ Recupera vittorie, sconfitte e pareggi storici contro un bot specifico. """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END),
                SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END),
                SUM(CASE WHEN result = 'draw' THEN 1 ELSE 0 END)
            FROM games
            WHERE opponent = ?
        ''', (opponent_name,))

        stats = cursor.fetchone()
        conn.close()

        # Restituisce (0, 0, 0) se non ci sono partite nel DB
        return tuple(s if s is not None else 0 for s in stats)