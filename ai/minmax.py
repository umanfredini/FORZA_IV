"""
ai/minimax.py
Motore Decisionale Generico.
Implementa l'algoritmo Minimax con Alpha-Beta Pruning ottimizzato per Bitboard.
Include Move Ordering (Priorità al Centro).
"""
import random


class MinimaxAgent:
    # Ordine di ricerca ottimizzato: Centro -> Esterno
    # Questo massimizza l'efficacia dell'Alpha-Beta Pruning.
    CENTER_ORDER = [3, 2, 4, 1, 5, 0, 6]

    def __init__(self, engine, evaluator, depth=4):
        self.engine = engine
        self.evaluator = evaluator
        self.depth = depth

    def choose_move(self, player_idx):
        """
        Punto di ingresso pubblico.
        Restituisce l'indice della colonna migliore (0-6).
        """
        # 1. Recupero mosse valide (Ordinate dal centro)
        valid_moves = [c for c in self.CENTER_ORDER if self.engine.is_valid_location(c)]

        # 2. Ottimizzazione "Killer Move": Se c'è una vittoria immediata, prendila subito!
        for col in valid_moves:
            if self.engine.is_winning_move(col, player_idx):
                return col

        # 3. Avvio Ricorsione Minimax
        best_score = float('-inf')

        # Fallback: se non troviamo nulla di meglio, prendiamo la prima valida (che ora è la più centrale)
        best_col = valid_moves[0] if valid_moves else random.choice([0, 1, 2, 3, 4, 5, 6])

        alpha = float('-inf')
        beta = float('inf')

        for col in valid_moves:
            # --- SALVATAGGIO STATO VELOCE ---
            state_before = self.engine.get_state()

            # Simuliamo la mossa
            self.engine.drop_piece(col, player_idx)

            # Chiamiamo minimax per l'avversario (depth - 1)
            score = self.minimax(self.depth - 1, False, alpha, beta, player_idx)

            # --- RIPRISTINO STATO ---
            self.engine.set_state(state_before)

            if score > best_score:
                best_score = score
                best_col = col

            # Aggiornamento Alpha
            alpha = max(alpha, best_score)

        return best_col

    def minimax(self, depth, is_maximizing, alpha, beta, ai_player_idx):
        """
        Nucleo ricorsivo dell'algoritmo.
        """
        opponent_idx = (ai_player_idx + 1) % 2

        # CASO BASE
        if depth == 0:
            return self.evaluator.evaluate(self.engine, ai_player_idx)

        if self.engine.check_victory(ai_player_idx):
            return 10000000 + depth  # Preferiamo vincere prima

        if self.engine.check_victory(opponent_idx):
            return -10000000 - depth  # Preferiamo perdere il più tardi possibile

        # Generazione mosse con Move Ordering
        valid_moves = [c for c in self.CENTER_ORDER if self.engine.is_valid_location(c)]

        if not valid_moves:
            return 0  # Patta

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

    # --- METODI DI SUPPORTO ---

    def get_evaluation(self, engine):
        """Helper per UI"""
        return self.evaluator.evaluate(engine, 1)