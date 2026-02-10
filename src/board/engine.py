import numpy as np


class GameEngine:
    # Maschera globale per la riga dei "guardiani" (il 7° bit di ogni colonna)
    # Serve a capire istantaneamente se una colonna è piena.
    # Corrisponde a: 1000000 1000000 1000000 1000000 1000000 1000000 1000000
    TOP_MASK = 0b1000000100000010000001000000100000010000001000000

    def __init__(self):
        self.bitboards = [0, 0]  # [Player 0 (Giallo), Player 1 (Rosso)]
        # Altezze iniziali: puntano alla riga 0 di ogni colonna (0, 7, 14, 21...)
        self.heights = [col * 7 for col in range(7)]
        self.counter = 0

    def is_valid_location(self, col):
        """
        Controlla se la colonna non è piena.
        Verifica se il bit puntato da heights[col] colliderebbe con la TOP_MASK.
        """
        return ((1 << self.heights[col]) & self.TOP_MASK) == 0

    def drop_piece(self, col, player_idx):
        """
        Inserisce la pedina nella colonna e aggiorna l'altezza.
        """
        move = 1 << self.heights[col]
        self.bitboards[player_idx] ^= move  # XOR per attivare il bit
        self.heights[col] += 1
        self.counter += 1

    def is_winning_move(self, col, player_idx):
        """
        Simula la mossa e controlla la vittoria senza modificare lo stato reale.
        Fondamentale per il Minimax (Killer Instinct) e il Profiler.
        """
        # Creiamo una bitboard temporanea con la mossa aggiunta
        temp_bitboard = self.bitboards[player_idx] | (1 << self.heights[col])
        return self._check_bitboard_victory(temp_bitboard)

    def check_victory(self, player_idx):
        """ Controlla se il giocatore specificato ha vinto. """
        return self._check_bitboard_victory(self.bitboards[player_idx])

    def _check_bitboard_victory(self, b):
        """
        Algoritmo ultra-veloce per controllo vittoria (bitwise operations).
        """
        # Orizzontale (-)
        m = b & (b >> 7)
        if m & (m >> 14): return True

        # Diagonale Backslash (\)
        m = b & (b >> 6)
        if m & (m >> 12): return True

        # Diagonale Slash (/)
        m = b & (b >> 8)
        if m & (m >> 16): return True

        # Verticale (|)
        m = b & (b >> 1)
        if m & (m >> 2): return True

        return False

    def get_board_matrix(self):
        """
        Converte le bitboard in matrice NumPy per l'interfaccia grafica.
        """
        # Matrice logica: riga 0 = fondo
        matrix = np.zeros((6, 7), dtype=int)

        for col in range(7):
            for row in range(6):
                bit_index = col * 7 + row
                bit_mask = 1 << bit_index

                if self.bitboards[0] & bit_mask:
                    matrix[row][col] = 1
                elif self.bitboards[1] & bit_mask:
                    matrix[row][col] = 2

        # Invertiamo l'asse Y per la visualizzazione (riga 0 diventa alto nello schermo)
        return np.flipud(matrix)

    # --- METODI PER IL MINIMAX (Salvataggio Stato) ---

    def get_state(self):
        """
        Restituisce lo stato corrente completo.
        IMPORTANTE: Deve includere le Bitboard E le Altezze (heights).
        Il Profiler si aspetta: [bitboard_P1, bitboard_P2, heights_list]
        """
        # Restituiamo una copia delle bitboard e una COPIA delle altezze (heights[:])
        return [self.bitboards[0], self.bitboards[1], self.heights[:], self.counter]

    def set_state(self, state):
        """
        Ripristina lo stato della scacchiera.
        """
        self.bitboards[0] = state[0]
        self.bitboards[1] = state[1]

        # Ripristiniamo anche le altezze.
        # Se il tuo vecchio codice non passava le heights, questo crashava.
        self.heights = state[2][:]
        self.counter = state[3]


    def reset(self):
        """ Ripristina tutto allo stato iniziale. """
        self.bitboards = [0, 0]
        self.heights = [col * 7 for col in range(7)]
        self.counter = 0