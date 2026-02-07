import sqlite3
import json
from datetime import datetime
import os

# Trova la cartella del progetto (due livelli sopra questo file se è in src/db/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "connect4_factory.db")

class GamePersistence:
    def __init__(self, db_path=DB_PATH):
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

        # --- NUOVA TABELLA: OPENING BOOK ---
        # State_Hash: Stringa univoca "BitboardP1_BitboardP2"
        # Move: La colonna giocata (0-6)
        # Visits: Quante volte abbiamo visto questa mossa in questo stato
        # Wins: Quante volte chi ha fatto questa mossa ha poi vinto
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
                           wins
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

    def get_latest_biases(self, opponent_name):
        """
        Recupera l'ultimo set di bias salvato per questo avversario.
        Permette all'IA di 'ricordare' le debolezze scoperte in sessioni passate.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Ordiniamo per ID decrescente per prendere l'ultima partita giocata
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

        # --- METODI PER L'APPRENDIMENTO APERTURE ---

        def update_opening_move(self, state_hash, move_col, won):
            """
            Aggiorna le statistiche per una mossa specifica.
            Se won=True, incrementa wins e visits.
            Se won=False, incrementa solo visits.
            """
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Verifica se esiste già
            cursor.execute('SELECT visits, wins FROM opening_book WHERE state_hash=? AND move_col=?',
                           (state_hash, move_col))
            row = cursor.fetchone()

            win_increment = 1 if won else 0

            if row:
                new_visits = row[0] + 1
                new_wins = row[1] + win_increment
                cursor.execute('''
                               UPDATE opening_book
                               SET visits=?,
                                   wins=?
                               WHERE state_hash = ?
                                 AND move_col = ?
                               ''', (new_visits, new_wins, state_hash, move_col))
            else:
                cursor.execute('''
                               INSERT INTO opening_book (state_hash, move_col, visits, wins)
                               VALUES (?, ?, 1, ?)
                               ''', (state_hash, move_col, win_increment))

            conn.commit()
            conn.close()

        def get_opening_stats(self, state_hash):
            """
            Restituisce tutte le mosse conosciute per questo stato.
            Return: List of (move_col, visits, wins)
            """
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT move_col, visits, wins FROM opening_book WHERE state_hash=?', (state_hash,))
            results = cursor.fetchall()

            conn.close()
            return results