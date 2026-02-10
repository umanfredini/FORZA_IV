import random
# Assicurati che questo file esista in ai/profiler.py e sia nel PYTHONPATH corretto
from src.ai.profiler import OpponentProfiler


class GameController:
    def __init__(self, engine, view):
        self.engine = engine
        self.view = view

        # --- PROFILER ---
        # Il profiler persiste tra i round per imparare i bias dell'avversario
        self.profiler = OpponentProfiler()

        # --- GESTIONE TURNI ---
        self.first_player_of_match = random.choice([0, 1])
        self.turn = self.first_player_of_match
        self.game_over = False

        # --- VARIABILI DI STATO ---
        # FIX: Inizializziamo moves_count qui per evitare AttributeError
        self.moves_count = 0

        self.stats = {
            "wins_p1": 0, "wins_p2": 0,
            "moves_p1": 0, "moves_p2": 0,
            "ai_eval": 0
        }

    def process_turn(self, x_input):
        """
        Gestisce l'input del giocatore (o del bot), aggiorna il modello
        e notifica il profiler.
        """
        if self.game_over: return False, None

        # Conversione da coordinate pixel (mouse) a indice colonna (0-6)
        col = int(x_input // self.view.sq_size)

        if not self.engine.is_valid_location(col):
            return False, None

        # 1. CATTURA DELLO STATO *PRIMA* DELLA MOSSA
        # Questo è fondamentale per il Profiler, che deve confrontare "prima" e "dopo".
        # IMPORTANTE: engine.get_state() ora restituisce [p1, p2, heights, counter]
        state_before = self.engine.get_state()

        # 2. ESECUZIONE DELLA MOSSA
        row = self.engine.drop_piece(col, self.turn)

        # Aggiornamento statistiche mosse per giocatore specifico
        if self.turn == 0:
            self.stats["moves_p1"] += 1
        else:
            self.stats["moves_p2"] += 1

        # 3. CONTROLLO VITTORIA
        if self.engine.check_victory(self.turn):
            self.game_over = True

            # Aggiorniamo il contatore delle vittorie totali
            if self.turn == 0:
                self.stats["wins_p1"] += 1
            else:
                self.stats["wins_p2"] += 1

            return True, self.turn

        # 4. AGGIORNAMENTO PROFILER (Solo se ha mosso l'avversario umano/bot profilato)
        # Se tocca all'IA (turn=1) e sta giocando contro un umano, l'IA analizza la mossa dell'umano (turn=0).
        # Ma qui, nel controller generico, aggiorniamo il profiler sulla mossa APPENA FATTA.
        # Se ha mosso il Giocatore 0 (Umano/Bot A), il Profiler analizza la mossa di 0.
        self.profiler.update(state_before, col, self.turn)

        # 5. CAMBIO TURNO
        self.turn = (self.turn + 1) % 2

        # FIX: Ora moves_count è inizializzato, quindi possiamo incrementarlo
        self.moves_count += 1

        return False, None

    def reset_for_new_round(self):
        """
        Prepara il controller per una nuova partita, resettando la scacchiera
        ma mantenendo la memoria del Profiler (Bias appresi).
        """
        self.engine.reset()
        self.game_over = False

        # Alterniamo chi inizia la partita
        self.first_player_of_match = 1 - self.first_player_of_match
        self.turn = self.first_player_of_match

        # FIX: Resettiamo il contatore globale delle mosse
        self.moves_count = 0

        # Resettiamo solo le statistiche relative al round corrente
        self.stats["moves_p1"] = 0
        self.stats["moves_p2"] = 0
        self.stats["ai_eval"] = 0