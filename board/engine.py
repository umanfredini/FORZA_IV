import numpy as np


class GameEngine:
    def __init__(self):
        self.bitboards = [0, 0]
        # Altezze iniziali: 0, 7, 14, 21, 28, 35, 42
        self.heights = [col * 7 for col in range(7)]
        self.counter = 0

    def is_valid_location(self, col):
        # Maschera per la riga superiore (la riga 5 di ogni colonna)
        # Il bit di guardia è il 6°, 13°, ecc.
        # Una mossa è valida se il bit di guardia NON è quello puntato da heights
        TOP_ROW_MASK = 0b1000000100000010000001000000100000010000001000000
        return ((1 << self.heights[col]) & TOP_ROW_MASK) == 0

    def drop_piece(self, col, player_idx):
        move = 1 << self.heights[col]
        self.bitboards[player_idx] ^= move
        self.heights[col] += 1
        self.counter += 1

    def is_winning_move(self, col, player_idx):
        """
        Simula la mossa e controlla la vittoria senza sporcare la bitboard reale.
        Usalo nel Profiler per vedere se l'avversario ha "mancato" una vittoria.
        """
        temp_bitboard = self.bitboards[player_idx] | (1 << self.heights[col])
        return self._check_bitboard_victory(temp_bitboard)

    def check_victory(self, player_idx):
        return self._check_bitboard_victory(self.bitboards[player_idx])

    def _check_bitboard_victory(self, b):
        # Orizzontale
        m = b & (b >> 7)
        if m & (m >> 14): return True
        # Diagonale \
        m = b & (b >> 6)
        if m & (m >> 12): return True
        # Diagonale /
        m = b & (b >> 8)
        if m & (m >> 16): return True
        # Verticale
        m = b & (b >> 1)
        if m & (m >> 2): return True
        return False

    def get_board_matrix(self):
        """
        Converte le bitboard in matrice per la View.
        Usa np.flipud per orientare correttamente la gravità (0 in basso -> 5 in basso visuale).
        """
        # Creiamo la matrice "logica": riga 0 è il fondo, riga 5 è la cima
        matrix = np.zeros((6, 7), dtype=int)

        for col in range(7):
            for row in range(6):
                # Calcoliamo il bit esatto usando la struttura 7-bit (6 + 1 guardia)
                bit_index = col * 7 + row
                bit_mask = 1 << bit_index

                if self.bitboards[0] & bit_mask:
                    matrix[row][col] = 1
                elif self.bitboards[1] & bit_mask:
                    matrix[row][col] = 2

        # ORA invertiamo l'asse Y della matrice.
        # Ciò che era logico (riga 0) diventa visivo (riga 5/fondo)
        return np.flipud(matrix)

    def get_state(self):
        """ Ritorna una copia del sistema binario per il Profiler """
        return self.bitboards[0], self.bitboards[1], list(self.heights)