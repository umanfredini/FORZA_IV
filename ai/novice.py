import math
import random
import copy


class MinimaxBotNovice:
    """
    * Implementazione dell'agente AI "Novice".
    * Depth ridotta a 3.
    * Comportamento umano imperfetto: non sceglie sempre la mossa ottimale.
    * Probabilità: 40% Migliore, 20% Seconda, 40% Terza.
    """

    def __init__(self, depth):
        self.depth = depth
        self.PLAYER_PIECE = 1
        self.BOT_PIECE = 2
        self.EMPTY = 0
        self.WINDOW_LENGTH = 4

    def evaluate_window(self, window, piece):
        """ Assegna un punteggio a una finestra di 4 celle. """
        score = 0
        opp_piece = self.PLAYER_PIECE if piece == self.BOT_PIECE else self.BOT_PIECE

        if window.count(piece) == 4:
            score += 100
        elif window.count(piece) == 3 and window.count(self.EMPTY) == 1:
            score += 5
        elif window.count(piece) == 2 and window.count(self.EMPTY) == 2:
            score += 2

        if window.count(opp_piece) == 3 and window.count(self.EMPTY) == 1:
            score -= 4

        return score

    def score_position(self, board_matrix, piece):
        """ Valuta l'intera scacchiera. """
        score = 0
        # Preferenza centro
        center_array = [int(i) for i in list(board_matrix[:, 3])]
        center_count = center_array.count(piece)
        score += center_count * 3

        # Orizzontale
        for r in range(6):
            row_array = [int(i) for i in list(board_matrix[r, :])]
            for c in range(7 - 3):
                window = row_array[c:c + self.WINDOW_LENGTH]
                score += self.evaluate_window(window, piece)

        # Verticale
        for c in range(7):
            col_array = [int(i) for i in list(board_matrix[:, c])]
            for r in range(6 - 3):
                window = col_array[r:r + self.WINDOW_LENGTH]
                score += self.evaluate_window(window, piece)

        # Diagonali
        for r in range(6 - 3):
            for c in range(7 - 3):
                window = [board_matrix[r + i][c + i] for i in range(self.WINDOW_LENGTH)]
                score += self.evaluate_window(window, piece)

        for r in range(6 - 3):
            for c in range(7 - 3):
                window = [board_matrix[r + 3 - i][c + i] for i in range(self.WINDOW_LENGTH)]
                score += self.evaluate_window(window, piece)

        return score

    def is_terminal_node(self, engine):
        return engine.check_victory(0) or engine.check_victory(1) or len(self.get_valid_locations(engine)) == 0

    def get_valid_locations(self, engine):
        valid_locations = []
        for col in range(7):
            if engine.is_valid_location(col):
                valid_locations.append(col)
        return valid_locations

    def minimax(self, engine, depth, alpha, beta, maximizingPlayer):
        """
        Algoritmo Minimax standard (usato per calcolare i punteggi delle mosse future).
        """
        valid_locations = self.get_valid_locations(engine)
        is_terminal = self.is_terminal_node(engine)

        if depth == 0 or is_terminal:
            if is_terminal:
                if engine.check_victory(1):
                    return (None, 100000000000000)
                elif engine.check_victory(0):
                    return (None, -10000000000000)
                else:
                    return (None, 0)
            else:
                return (None, self.score_position(engine.get_board_matrix(), self.BOT_PIECE))

        if maximizingPlayer:
            value = -math.inf
            column = random.choice(valid_locations)
            for col in valid_locations:
                temp_engine = copy.deepcopy(engine)
                temp_engine.drop_piece(col, 1)
                new_score = self.minimax(temp_engine, depth - 1, alpha, beta, False)[1]
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta: break
            return column, value
        else:
            value = math.inf
            column = random.choice(valid_locations)
            for col in valid_locations:
                temp_engine = copy.deepcopy(engine)
                temp_engine.drop_piece(col, 0)
                new_score = self.minimax(temp_engine, depth - 1, alpha, beta, True)[1]
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta: break
            return column, value

    def get_best_move(self, engine):
        """
        * Logica "Novice": Calcola tutte le mosse possibili e sceglie in base alle probabilità.
        """
        valid_moves = self.get_valid_locations(engine)

        if not valid_moves:
            return None, 0
        if len(valid_moves) == 1:
            # Qui usiamo True che nel minimax mappa correttamente agli indici
            score = self.minimax(copy.deepcopy(engine), 1, -math.inf, math.inf, True)[1]
            return valid_moves[0], score

        # 1. Calcoliamo il punteggio Minimax per OGNI mossa valida al livello radice
        scored_moves = []
        for col in valid_moves:
            temp_engine = copy.deepcopy(engine)

            # --- CORREZIONE QUI SOTTO ---
            # ERRORE PRECEDENTE: temp_engine.drop_piece(col, self.BOT_PIECE) -> passava 2
            # CORREZIONE: Passiamo 1 (l'indice della bitboard del Player 2/Bot)
            temp_engine.drop_piece(col, 1)

            # Chiamiamo minimax per l'avversario (depth - 1)
            score = self.minimax(temp_engine, self.depth - 1, -math.inf, math.inf, False)[1]
            scored_moves.append((col, score))

        # 2. Ordiniamo le mosse dalla migliore alla peggiore (punteggio decrescente)
        scored_moves.sort(key=lambda x: x[1], reverse=True)

        # 3. Logica probabilistica (Resto del codice invariato)
        rand_val = random.random()
        chosen_index = 0

        # Distribuzione: 40% Best, 20% 2nd, 40% 3rd
        if rand_val < 0.40:
            chosen_index = 0  # Migliore
        elif rand_val < 0.60:
            chosen_index = 1  # Seconda migliore
        else:
            chosen_index = 2  # Terza migliore

        if chosen_index >= len(scored_moves):
            chosen_index = 0

        final_move = scored_moves[chosen_index]
        return final_move[0], final_move[1]

    def get_evaluation(self, engine):
        return self.score_position(engine.get_board_matrix(), self.BOT_PIECE)