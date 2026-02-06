"""
ai/minimax.py
Motore Decisionale Generico.
Implementa l'algoritmo Minimax con Alpha-Beta Pruning ottimizzato per Bitboard.
Include:
1. Move Ordering (Centro -> Esterno)
2. Transposition Table (Reset ad ogni mossa per coerenza con i Bias)
"""
import random

class MinimaxAgent:
    # Ordine di ricerca ottimizzato: Centro -> Esterno
    CENTER_ORDER = [3, 2, 4, 1, 5, 0, 6]

    # Flag per la Transposition Table
    FLAG_EXACT = 0
    FLAG_LOWERBOUND = 1 # Alpha
    FLAG_UPPERBOUND = 2 # Beta

    def __init__(self, engine, evaluator, depth=4):
        self.engine = engine
        self.evaluator = evaluator
        self.depth = depth
        # Dizionario per la memoria: Key=(p1, p2), Value=(score, depth, flag)
        self.transposition_table = {}

    def choose_move(self, player_idx):
        """
        Punto di ingresso pubblico.
        """
        # --- FIX 1: PULIZIA CACHE ---
        # Fondamentale per l'AI Adattiva: i bias cambiano nel tempo.
        # Se non puliamo, l'IA usa valutazioni vecchie basate su bias diversi.
        self.transposition_table.clear()

        # 1. Recupero mosse valide (Move Ordering)
        valid_moves = [c for c in self.CENTER_ORDER if self.engine.is_valid_location(c)]

        # --- FIX 2: PREVENZIONE CRASH/OVERFLOW ---
        if not valid_moves:
            return None # Nessuna mossa possibile (Pareggio o Game Over)

        # 2. Killer Move (Vittoria Immediata)
        # Controlliamo subito se possiamo vincere in 1 mossa senza sprecare calcoli
        for col in valid_moves:
            if self.engine.is_winning_move(col, player_idx):
                return col

        # 3. Minimax Start
        best_score = float('-inf')
        best_col = valid_moves[0]
        alpha = float('-inf')
        beta = float('inf')

        for col in valid_moves:
            state_before = self.engine.get_state()
            self.engine.drop_piece(col, player_idx)

            # Chiamata ricorsiva
            score = self.minimax(self.depth - 1, False, alpha, beta, player_idx)

            self.engine.set_state(state_before)

            if score > best_score:
                best_score = score
                best_col = col

            alpha = max(alpha, best_score)

        return best_col

    def minimax(self, depth, is_maximizing, alpha, beta, ai_player_idx):
        # Salviamo alpha originale per determinare il flag della TT alla fine
        alpha_orig = alpha

        # --- 1. TRANSPOSITION TABLE LOOKUP ---
        # Chiave univoca dello stato
        state_key = (self.engine.bitboards[0], self.engine.bitboards[1])

        if state_key in self.transposition_table:
            tt_val, tt_depth, tt_flag = self.transposition_table[state_key]

            # Usiamo il valore solo se la profondità salvata è sufficiente
            if tt_depth >= depth:
                if tt_flag == self.FLAG_EXACT:
                    return tt_val
                elif tt_flag == self.FLAG_LOWERBOUND:
                    alpha = max(alpha, tt_val)
                elif tt_flag == self.FLAG_UPPERBOUND:
                    beta = min(beta, tt_val)

                if alpha >= beta:
                    return tt_val

        # --- Logica Standard Minimax ---
        opponent_idx = (ai_player_idx + 1) % 2

        # A. Valutazione Foglia o Profondità 0
        if depth == 0:
            # Qui chiamiamo l'evaluator corretto (con i bias attuali)
            return self.evaluator.evaluate(self.engine, ai_player_idx)

        # B. Controllo Terminale (Vittoria/Sconfitta)
        # Nota: Questi valori devono essere ASSOLUTI, non toccati dall'Evaluator
        if self.engine.check_victory(ai_player_idx):
            return 10000000 + depth # Preferiamo vittorie veloci
        if self.engine.check_victory(opponent_idx):
            return -10000000 - depth # Preferiamo sconfitte lente

        valid_moves = [c for c in self.CENTER_ORDER if self.engine.is_valid_location(c)]
        if not valid_moves:
            return 0 # Pareggio

        best_val = 0 # Placeholder

        if is_maximizing:
            best_val = float('-inf')
            for col in valid_moves:
                state_before = self.engine.get_state()
                self.engine.drop_piece(col, ai_player_idx)

                eval = self.minimax(depth - 1, False, alpha, beta, ai_player_idx)

                self.engine.set_state(state_before)
                best_val = max(best_val, eval)
                alpha = max(alpha, eval)
                if beta <= alpha: break
        else:
            best_val = float('inf')
            for col in valid_moves:
                state_before = self.engine.get_state()
                self.engine.drop_piece(col, opponent_idx)

                eval = self.minimax(depth - 1, True, alpha, beta, ai_player_idx)

                self.engine.set_state(state_before)
                best_val = min(best_val, eval)
                beta = min(beta, eval)
                if beta <= alpha: break

        # --- 2. TRANSPOSITION TABLE STORE ---
        tt_flag = self.FLAG_EXACT
        if best_val <= alpha_orig:
            tt_flag = self.FLAG_UPPERBOUND
        elif best_val >= beta:
            tt_flag = self.FLAG_LOWERBOUND

        self.transposition_table[state_key] = (best_val, depth, tt_flag)

        return best_val