from ai.minmax import MinimaxBot


class DiagonalDefensiveFlawBot(MinimaxBot):
    """
    VARIANTE: Difensore Diagonale Disattento

    Caratteristiche:
    - Depth: 4
    - Attacco: 100% Efficace (usa le diagonali per vincere).
    - Difesa: 25% Efficace sulle diagonali.

    Comportamento:
    Se vede una sua vittoria diagonale, la prende.
    Ma se l'avversario ha un '3-in-fila' diagonale, questo bot applica una penalità
    molto bassa (-1 invece di -4 standard).
    Risultato: Spesso preferirà attaccare al centro o costruire il proprio gioco
    piuttosto che bloccare una minaccia diagonale avversaria.
    """

    def __init__(self, depth=1):
        super().__init__(depth)

    def _evaluate_window_biased(self, window, piece, is_diagonal):
        """
        Valutatore personalizzato che riduce la penalità difensiva sulle diagonali.
        """
        score = 0
        opp_piece = self.PLAYER_PIECE if piece == self.BOT_PIECE else self.BOT_PIECE

        # --- LOGICA DI ATTACCO (Invariata) ---
        if window.count(piece) == 4:
            score += 100
        elif window.count(piece) == 3 and window.count(self.EMPTY) == 1:
            score += 5
        elif window.count(piece) == 2 and window.count(self.EMPTY) == 2:
            score += 2

        # --- LOGICA DI DIFESA (Modificata) ---
        if window.count(opp_piece) == 3 and window.count(self.EMPTY) == 1:
            if is_diagonal:
                # Sottostima il pericolo diagonale!
                # Un peso di -1 è basso: se altrove guadagna +2, ignorerà il blocco.
                score -= 1
            else:
                # Difesa standard su righe/colonne (molto reattivo)
                score -= 4

        return score

    def score_position(self, board_matrix, piece):
        """
        Override che distingue tra assi ortogonali e diagonali.
        """
        score = 0

        # 1. Centro (Standard)
        center_array = [int(i) for i in list(board_matrix[:, 3])]
        center_count = center_array.count(piece)
        score += center_count * 3

        # 2. Orizzontale (Difesa Standard -> is_diagonal=False)
        for r in range(6):
            row_array = [int(i) for i in list(board_matrix[r, :])]
            for c in range(7 - 3):
                window = row_array[c:c + self.WINDOW_LENGTH]
                score += self._evaluate_window_biased(window, piece, is_diagonal=False)

        # 3. Verticale (Difesa Standard -> is_diagonal=False)
        for c in range(7):
            col_array = [int(i) for i in list(board_matrix[:, c])]
            for r in range(6 - 3):
                window = col_array[r:r + self.WINDOW_LENGTH]
                score += self._evaluate_window_biased(window, piece, is_diagonal=False)

        # 4. Diagonale Positiva (Difesa Debole -> is_diagonal=True)
        for r in range(6 - 3):
            for c in range(7 - 3):
                window = [board_matrix[r + i][c + i] for i in range(self.WINDOW_LENGTH)]
                score += self._evaluate_window_biased(window, piece, is_diagonal=True)

        # 5. Diagonale Negativa (Difesa Debole -> is_diagonal=True)
        for r in range(6 - 3):
            for c in range(7 - 3):
                window = [board_matrix[r + 3 - i][c + i] for i in range(self.WINDOW_LENGTH)]
                score += self._evaluate_window_biased(window, piece, is_diagonal=True)

        return score