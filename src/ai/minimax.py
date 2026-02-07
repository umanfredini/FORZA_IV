"""
ai/minimax.py
Versione STABLE: Transposition Table con chiave sicura (Tupla).
"""
class MinimaxAgent:
    CENTER_ORDER = [3, 2, 4, 1, 5, 0, 6]
    FLAG_EXACT = 0
    FLAG_LOWERBOUND = 1
    FLAG_UPPERBOUND = 2

    def __init__(self, engine, evaluator, depth=4):
        self.engine = engine
        self.evaluator = evaluator
        self.depth = depth
        self.transposition_table = {}

    def choose_move(self, player_idx):
        # NOTA: La pulizia self.transposition_table.clear()
        # deve essere fatta SOLO all'inizio della partita nel controller!

        valid_moves = [c for c in self.CENTER_ORDER if self.engine.is_valid_location(c)]
        if not valid_moves: return None

        for col in valid_moves:
            if self.engine.is_winning_move(col, player_idx): return col

        best_score = float('-inf')
        best_col = valid_moves[0]
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
        alpha_orig = alpha

        # [CHIAVE SICURA] Usiamo la tupla dei bitboard. Infallibile.
        state_key = (self.engine.bitboards[0], self.engine.bitboards[1])

        # 1. TT Lookup
        if state_key in self.transposition_table:
            tt_val, tt_depth, tt_flag = self.transposition_table[state_key]
            if tt_depth >= depth:
                if tt_flag == self.FLAG_EXACT: return tt_val
                elif tt_flag == self.FLAG_LOWERBOUND: alpha = max(alpha, tt_val)
                elif tt_flag == self.FLAG_UPPERBOUND: beta = min(beta, tt_val)
                if alpha >= beta: return tt_val

        opponent_idx = (ai_player_idx + 1) % 2

        if depth == 0:
            return self.evaluator.evaluate(self.engine, ai_player_idx)

        if self.engine.check_victory(ai_player_idx): return 10000000 + depth
        if self.engine.check_victory(opponent_idx): return -10000000 - depth

        valid_moves = [c for c in self.CENTER_ORDER if self.engine.is_valid_location(c)]
        if not valid_moves: return 0

        best_val = 0
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

        # 2. TT Store
        tt_flag = self.FLAG_EXACT
        if best_val <= alpha_orig: tt_flag = self.FLAG_UPPERBOUND
        elif best_val >= beta: tt_flag = self.FLAG_LOWERBOUND

        self.transposition_table[state_key] = (best_val, depth, tt_flag)
        return best_val