"""
ai/minimax.py
Motore Decisionale Generico.
Implementa l'algoritmo Minimax con Alpha-Beta Pruning ottimizzato per Bitboard.
Non contiene logica di punteggio: delega tutto all'Evaluator passato nel costruttore.
"""
import random


class MinimaxAgent:
    def __init__(self, engine, evaluator, depth=4):
        self.engine = engine
        self.evaluator = evaluator
        self.depth = depth

    def choose_move(self, player_idx):
        """
        Punto di ingresso pubblico.
        Restituisce l'indice della colonna migliore (0-6).
        """
        # 1. Recupero mosse valide
        valid_moves = [c for c in range(7) if self.engine.is_valid_location(c)]

        # 2. Ottimizzazione "Killer Move": Se c'è una vittoria immediata, prendila subito!
        # Questo evita di lanciare l'intera ricorsione per una scelta ovvia.
        for col in valid_moves:
            if self.engine.is_winning_move(col, player_idx):
                return col

        # 3. Avvio Ricorsione Minimax
        best_score = float('-inf')
        best_col = random.choice(valid_moves)  # Fallback casuale

        alpha = float('-inf')
        beta = float('inf')

        # Ordiniamo le mosse? Per ora casuale, ma potremmo ordinare per colonna centrale
        # per migliorare l'alpha-beta pruning (il centro è spesso migliore).

        for col in valid_moves:
            # --- SALVATAGGIO STATO VELOCE (No deepcopy!) ---
            # Bitboard engine permette di salvare lo stato con pochi interi
            state_before = self.engine.get_state()

            # Simuliamo la mossa
            self.engine.drop_piece(col, player_idx)

            # Chiamiamo minimax per l'avversario (depth - 1)
            # Passiamo False perché ora tocca all'avversario (minimizzare il nostro score)
            score = self.minimax(self.depth - 1, False, alpha, beta, player_idx)

            # --- RIPRISTINO STATO ---
            self.engine.set_state(state_before)

            if score > best_score:
                best_score = score
                best_col = col

            # Aggiornamento Alpha (miglior risultato che possiamo assicurarci)
            alpha = max(alpha, best_score)

        return best_col

    def minimax(self, depth, is_maximizing, alpha, beta, ai_player_idx):
        """
        Nucleo ricorsivo dell'algoritmo.
        ai_player_idx: Chi è il bot che sta pensando (sempre fisso).
        is_maximizing: True se tocca al bot, False se tocca all'avversario.
        """
        # Identifichiamo l'avversario
        opponent_idx = (ai_player_idx + 1) % 2

        # CASO BASE: Foglia raggiunta o Partita Finita
        if depth == 0:
            return self.evaluator.evaluate(self.engine, ai_player_idx)

        if self.engine.check_victory(ai_player_idx):
            return 10000000 + depth  # Preferiamo vincere prima (depth più alta)

        if self.engine.check_victory(opponent_idx):
            return -10000000 - depth  # Preferiamo perdere il più tardi possibile

        valid_moves = [c for c in range(7) if self.engine.is_valid_location(c)]

        # Se non ci sono mosse valide è patta
        if not valid_moves:
            return 0

        if is_maximizing:
            max_eval = float('-inf')
            for col in valid_moves:
                state_before = self.engine.get_state()
                self.engine.drop_piece(col, ai_player_idx)

                eval = self.minimax(depth - 1, False, alpha, beta, ai_player_idx)

                self.engine.set_state(state_before)

                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha: break  # Pruning
            return max_eval

        else:  # Minimizing Player (Avversario)
            min_eval = float('inf')
            for col in valid_moves:
                state_before = self.engine.get_state()
                self.engine.drop_piece(col, opponent_idx)

                eval = self.minimax(depth - 1, True, alpha, beta, ai_player_idx)

                self.engine.set_state(state_before)

                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha: break  # Pruning
            return min_eval

    # --- METODI DI SUPPORTO PER IL MAIN ---

    def get_evaluation(self, engine):
        """Metodo helper per mostrare la barra della valutazione nella UI"""
        # Nota: Qui assumiamo che il bot sia sempre Player 1 (Giallo/Indice 1) nel PvE
        return self.evaluator.evaluate(engine, 1)