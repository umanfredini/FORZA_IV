"""
ai/minimax.py
Motore Decisionale Generico.
Implementa l'algoritmo Minimax con Alpha-Beta Pruning ottimizzato per Bitboard.
Include:
1. Move Ordering (Centro -> Esterno)
2. Transposition Table (Memoria Cache)
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
        # Dizionario per la memoria: Key=(p1_bitboard, p2_bitboard), Value=(score, depth, flag)
        self.transposition_table = {}

    def choose_move(self, player_idx):
        """
        Punto di ingresso pubblico.
        """
        # Pulizia parziale o totale della tabella?
        # Per ora la manteniamo tra le mosse della stessa partita per massimizzare la velocità.
        # (Opzionale: self.transposition_table.clear() se si vuole meno memoria usata)

        # 1. Recupero mosse valide (Move Ordering)
        valid_moves = [c for c in self.CENTER_ORDER if self.engine.is_valid_location(c)]

        # 2. Killer Move
        for col in valid_moves:
            if self.engine.is_winning_move(col, player_idx):
                return col

        # 3. Minimax
        best_score = float('-inf')
        best_col = valid_moves[0] if valid_moves else random.choice([0, 1, 2, 3, 4, 5, 6])
        alpha = float('-inf')
        beta = float('inf')

        for col in valid_moves:
            state_before = self.engine.get_state()
            self.engine.drop_piece(col, player_idx)

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
        # Creiamo una chiave unica basata sulle bitboard (che rappresentano univocamente lo stato)
        # Nota: Includiamo 'is_maximizing' nella logica o assumiamo che lo stato implichi il turno?
        # Per sicurezza usiamo le bitboard.
        state_key = (self.engine.bitboards[0], self.engine.bitboards[1])

        if state_key in self.transposition_table:
            tt_entry = self.transposition_table[state_key]
            tt_val, tt_depth, tt_flag = tt_entry

            # Usiamo il valore solo se la profondità salvata è >= a quella richiesta
            # (ovvero abbiamo analizzato questo stato "abbastanza a fondo" in passato)
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

        if depth == 0:
            return self.evaluator.evaluate(self.engine, ai_player_idx)

        if self.engine.check_victory(ai_player_idx):
            return 10000000 + depth

        if self.engine.check_victory(opponent_idx):
            return -10000000 - depth

        valid_moves = [c for c in self.CENTER_ORDER if self.engine.is_valid_location(c)]
        if not valid_moves:
            return 0

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

    def get_evaluation(self, engine):
        return self.evaluator.evaluate(engine, 1)