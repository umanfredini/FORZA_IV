"""
ai/evaluator.py
Modulo di Valutazione Euristica Adattiva.
Include:
1. Ottimizzazione hardware (.bit_count())
2. Anti-Blunder Check (Riconoscimento colonne velenose/Zugzwang)
"""

class AdaptiveEvaluator:
    def __init__(self, profiler):
        self.profiler = profiler

        # --- COSTANTI EURISTICHE ---
        self.SCORE_CENTER = 4
        self.SCORE_2_SINGLE = 5
        self.SCORE_2_SPLIT = 8
        self.SCORE_2_DOUBLE = 15
        self.SCORE_3 = 50
        self.SCORE_DOUBLE_THREAT = 5000
        self.SCORE_WIN = 10000000

        # Penalità per mossa suicida (giocare sotto una vittoria avversaria)
        self.SCORE_BLUNDER = 100000.0

        # Pre-calcolo Maschera Colonna Centrale (Indice 3)
        self.CENTER_MASK = 0
        for r in range(6):
            self.CENTER_MASK |= (1 << (3 * 7 + r))

    def evaluate(self, engine, player_idx):
        # 1. CONTROLLO TERMINALE
        if engine.check_victory(player_idx):
            return self.SCORE_WIN

        opponent_idx = (player_idx + 1) % 2
        if engine.check_victory(opponent_idx):
            return -self.SCORE_WIN

        # 2. RECUPERO DATI
        biases = self.profiler.get_adaptive_weights()
        my_pieces = engine.bitboards[player_idx]
        opp_pieces = engine.bitboards[opponent_idx]
        full_mask = my_pieces | opp_pieces

        score = 0

        # 3. VALUTAZIONE STRATEGICA (Centro)
        my_center = (my_pieces & self.CENTER_MASK).bit_count()
        opp_center = (opp_pieces & self.CENTER_MASK).bit_count()

        score += (my_center * self.SCORE_CENTER * biases.get('center_weight', 1.0))
        score -= (opp_center * self.SCORE_CENTER)

        # 4. VALUTAZIONE TATTICA DIREZIONALE
        # Verticale
        v_bias = biases.get('vertical_weakness', 1.0)
        score += self._evaluate_vertical(my_pieces, full_mask) * v_bias
        score -= self._evaluate_vertical(opp_pieces, full_mask)

        # Orizzontale
        h_bias = biases.get('horizontal_weakness', 1.0)
        score += self._evaluate_general_direction(my_pieces, full_mask, 7) * h_bias
        score -= self._evaluate_general_direction(opp_pieces, full_mask, 7)

        # Diagonali
        d_bias = biases.get('diagonal_weakness', 1.0)
        score += self._evaluate_general_direction(my_pieces, full_mask, 6) * d_bias
        score -= self._evaluate_general_direction(opp_pieces, full_mask, 6)
        score += self._evaluate_general_direction(my_pieces, full_mask, 8) * d_bias
        score -= self._evaluate_general_direction(opp_pieces, full_mask, 8)

        # 5. CONTROLLO TRAPPOLA A 7 (FORK)
        my_threats_mask = self._get_threat_mask(my_pieces, full_mask)
        if my_threats_mask.bit_count() >= 2:
            score += self.SCORE_DOUBLE_THREAT

        opp_threats_mask = self._get_threat_mask(opp_pieces, full_mask)
        if opp_threats_mask.bit_count() >= 2:
            score -= self.SCORE_DOUBLE_THREAT


        # 6. ANTI-BLUNDER CHECK (ZUGZWANG)
        # Scorriamo le colonne per vedere se muovere lì è un suicidio.
        # "Se gioco in colonna X, l'avversario vince subito sopra?"

        # Recuperiamo la maschera delle minacce avversarie (dove LUI vince se gioca)
        # L'abbiamo già calcolata: opp_threats_mask

        for col in range(7):
            # L'altezza attuale è dove cadrebbe la nostra pedina
            current_h = engine.heights[col]

            # Controllo validità: la colonna non deve essere piena (altezza < 6)
            # E per esserci un pericolo sopra, deve esserci spazio sopra (altezza < 5)
            # Quindi controlliamo se current_h < 5
            if current_h < 5:
                # La cella "sopra" è current_h + 1
                cell_above_bit = 1 << ((col * 7) + (current_h + 1))

                # Se quella cella è una vittoria per l'avversario...
                if cell_above_bit & opp_threats_mask:
                    # ...allora la cella attuale (current_h) è VELENOSA.
                    # Non dobbiamo giocarci.
                    score -= self.SCORE_BLUNDER

        return score

    def _get_threat_mask(self, p, full_mask):
        empty = ~full_mask
        threats = 0
        for d in [1, 7, 6, 8]:
            threats |= (p >> d) & (p >> (2*d)) & (p >> (3*d)) & empty
            threats |= (p << d) & (p >> d) & (p >> (2*d)) & empty
            threats |= (p << (2*d)) & (p << d) & (p >> d) & empty
            threats |= (p << (3*d)) & (p << (2*d)) & (p << d) & empty
        return threats

    def _evaluate_vertical(self, pieces, full_mask):
        score = 0
        empty = ~full_mask

        trios = pieces & (pieces >> 1) & (pieces >> 2)
        valid_trios = trios & (empty >> 3)
        score += valid_trios.bit_count() * self.SCORE_3

        pairs = pieces & (pieces >> 1)
        valid_pairs = pairs & (empty >> 2)
        score += valid_pairs.bit_count() * self.SCORE_2_SINGLE

        return score

    def _evaluate_general_direction(self, pieces, full_mask, shift):
        dir_score = 0
        empty = ~full_mask

        # TRIS
        trios = pieces & (pieces >> shift) & (pieces >> (shift * 2))
        t_right = (trios >> shift) & empty
        t_left = (trios << (shift * 3)) & empty

        gap1 = pieces & (pieces >> shift) & (pieces >> (shift * 3))
        t_mid_right = (gap1 << (shift * 2)) & empty
        gap2 = pieces & (pieces >> (shift * 2)) & (pieces >> (shift * 3))
        t_mid_left = (gap2 << shift) & empty

        total_threes = t_right | t_left | t_mid_right | t_mid_left
        dir_score += total_threes.bit_count() * self.SCORE_3

        # COPPIE
        pairs = pieces & (pieces >> shift)
        open_left = (empty << shift)
        open_right = (empty >> (shift * 2))

        double_open = pairs & open_left & open_right
        single_right = (pairs & open_right) & (~open_left)
        single_left = (pairs & open_left) & (~open_right)

        dir_score += double_open.bit_count() * self.SCORE_2_DOUBLE
        dir_score += (single_right | single_left).bit_count() * self.SCORE_2_SINGLE

        split = pieces & (pieces >> (shift * 2))
        gap_empty = (empty >> shift)
        s_left = split & gap_empty & (empty << shift)
        s_right = split & gap_empty & (empty >> (shift * 3))

        dir_score += (s_left | s_right).bit_count() * self.SCORE_2_SPLIT

        return dir_score