import random
# Assicurati che questo file esista in ai/profiler.py
from ai.profiler import OpponentProfiler


class GameController:
    def __init__(self, engine, view):
        self.engine = engine
        self.view = view

        # --- PROFILER ---
        self.profiler = OpponentProfiler()

        # --- GESTIONE TURNI ---
        self.first_player_of_match = random.choice([0, 1])
        self.turn = self.first_player_of_match
        self.game_over = False

        self.stats = {
            "wins_p1": 0, "wins_p2": 0,
            "moves_p1": 0, "moves_p2": 0,
            "ai_eval": 0
        }

    def process_turn(self, posx):
        if self.game_over: return False, None

        col = int(posx // self.view.sq_size)

        if 0 <= col < 7 and self.engine.is_valid_location(col):

            # 1. Aggiornamento Statistiche Mosse
            if self.turn == 0:
                self.stats["moves_p1"] += 1
            else:
                self.stats["moves_p2"] += 1

            # --- CORREZIONE QUI SOTTO ---

            # 2. Cattura lo stato PRIMA della mossa (Snapshot)
            # Il profiler deve sapere com'era la scacchiera per giudicare se la mossa era buona o no.
            # Usiamo .copy() perché le liste sono mutabili in Python.
            state_before = self.engine.bitboards.copy()

            # 3. Esecuzione Mossa (La scacchiera cambia qui)
            self.engine.drop_piece(col, self.turn)

            # 4. Aggiornamento Profiler
            # Registriamo la mossa solo se l'ha fatta l'umano (Player 0)
            if self.turn == 0:
                # Passiamo i 3 argomenti richiesti dall'errore:
                # 1. state_before: com'era la board
                # 2. col: dove ha mosso
                # 3. 0: l'indice del giocatore umano
                self.profiler.update(state_before, col, 0)

            # -----------------------------

            win = self.engine.check_victory(self.turn)
            last_player = self.turn

            if win:
                if self.turn == 0:
                    self.stats["wins_p1"] += 1
                else:
                    self.stats["wins_p2"] += 1
                self.game_over = True
            else:
                self.turn = (self.turn + 1) % 2

            return win, last_player

        return False, None

    def reset_for_new_round(self):
        self.engine.reset()
        self.game_over = False
        self.first_player_of_match = 1 - self.first_player_of_match
        self.turn = self.first_player_of_match
        self.stats["moves_p1"] = 0
        self.stats["moves_p2"] = 0
        self.stats["ai_eval"] = 0