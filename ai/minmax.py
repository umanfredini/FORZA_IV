import math
import random
import copy


class MinimaxBot:
    """
    * Implementazione dell'agente AI basato su Minimax con Alpha-Beta Pruning.
    """

    def __init__(self, depth):
        self.depth = depth
        self.PLAYER_PIECE = 1
        self.BOT_PIECE = 2
        self.EMPTY = 0
        self.WINDOW_LENGTH = 4

    def evaluate_window(self, window, piece):
        """
        * Assegna un punteggio a una finestra di 4 celle.
        *
        * @param window Lista di 4 interi rappresentanti le celle.
        * @param piece Il pezzo del giocatore corrente.
        * @return int Il punteggio calcolato.
        """
        score = 0
        opp_piece = self.PLAYER_PIECE if piece == self.BOT_PIECE else self.BOT_PIECE

        if window.count(piece) == 4:
            score += 100
        elif window.count(piece) == 3 and window.count(self.EMPTY) == 1:
            score += 5
        elif window.count(piece) == 2 and window.count(self.EMPTY) == 2:
            score += 2

        if window.count(opp_piece) == 3 and window.count(self.EMPTY) == 1:
            score -= 4  # Penalità forte se l'avversario sta per vincere

        return score

    def score_position(self, board_matrix, piece):
        """
        * Valuta l'intera scacchiera per determinare quanto è favorevole per il bot.
        *
        * @param board_matrix La matrice 6x7 dello stato attuale.
        * @param piece Il pezzo da valutare.
        * @return int Punteggio totale.
        """
        score = 0

        # Preferenza per la colonna centrale
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

        # Diagonale positiva
        for r in range(6 - 3):
            for c in range(7 - 3):
                window = [board_matrix[r + i][c + i] for i in range(self.WINDOW_LENGTH)]
                score += self.evaluate_window(window, piece)

        # Diagonale negativa
        for r in range(6 - 3):
            for c in range(7 - 3):
                window = [board_matrix[r + 3 - i][c + i] for i in range(self.WINDOW_LENGTH)]
                score += self.evaluate_window(window, piece)

        return score

    def is_terminal_node(self, engine):
        """
        * Verifica se il gioco è finito (vittoria o scacchiera piena).
        """
        return engine.check_victory(0) or engine.check_victory(1) or len(self.get_valid_locations(engine)) == 0

    def get_valid_locations(self, engine):
        """
        * Ritorna le colonne dove è possibile giocare.
        """
        valid_locations = []
        for col in range(7):
            if engine.is_valid_location(col):
                valid_locations.append(col)
        return valid_locations

    def minimax(self, engine, depth, alpha, beta, maximizingPlayer):
        """
        * Algoritmo ricorsivo Minimax con Alpha-Beta Pruning.
        *
        * @param engine Copia dell'engine di gioco.
        * @param depth Profondità residua.
        * @param alpha Valore Alpha per pruning.
        * @param beta Valore Beta per pruning.
        * @param maximizingPlayer Booleano (True se tocca al Bot).
        * @return tuple (colonna_migliore, punteggio)
        """
        valid_locations = self.get_valid_locations(engine)
        is_terminal = self.is_terminal_node(engine)

        if depth == 0 or is_terminal:
            if is_terminal:
                if engine.check_victory(1):  # Bot vince (P2 è index 1)
                    return (None, 100000000000000)
                elif engine.check_victory(0):  # Umano vince (P1 è index 0)
                    return (None, -10000000000000)
                else:  # Pareggio
                    return (None, 0)
            else:  # Profondità 0
                return (None, self.score_position(engine.get_board_matrix(), self.BOT_PIECE))

        if maximizingPlayer:
            value = -math.inf
            column = random.choice(valid_locations)
            for col in valid_locations:
                temp_engine = copy.deepcopy(engine)
                temp_engine.drop_piece(col, 1)  # Bot index 1
                new_score = self.minimax(temp_engine, depth - 1, alpha, beta, False)[1]
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value
        else:  # Minimizing player (Umano)
            value = math.inf
            column = random.choice(valid_locations)
            for col in valid_locations:
                temp_engine = copy.deepcopy(engine)
                temp_engine.drop_piece(col, 0)  # Umano index 0
                new_score = self.minimax(temp_engine, depth - 1, alpha, beta, True)[1]
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value

    def get_best_move(self, engine):
        """
        * Ritorna la tupla (colonna_migliore, punteggio_valutazione).
        """
        # Nota: ora ritorniamo entrambi i valori
        col, minimax_score = self.minimax(engine, self.depth, -math.inf, math.inf, True)
        return col, minimax_score

    def get_evaluation(self, engine):
        """
        * Calcola una valutazione statica immediata (senza guardare mosse future).
        * Utile per aggiornare la barra quando tocca all'umano.
        """
        return self.score_position(engine.get_board_matrix(), self.BOT_PIECE)