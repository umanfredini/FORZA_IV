"""
ai/evaluator.py
Modulo di Valutazione Euristica Adattiva.
Versione Bilanciata: Applica i bias alla differenza di punteggio (Simmetria).
"""

class AdaptiveEvaluator:
    def __init__(self, profiler):
        self.profiler = profiler

        # --- COSTANTI EURISTICHE BASE ---
        self.SCORE_CENTER = 4
        self.SCORE_2_SINGLE = 5
        self.SCORE_2_SPLIT = 8
        self.SCORE_2_DOUBLE = 15
        self.SCORE_3 = 50

        # Punteggi Speciali (Non influenzati dai bias normali)
        self.SCORE_DOUBLE_THREAT = 5000
        self.SCORE_BLUNDER = 100000.0 # Deve essere > (SCORE_3 * MaxBias)
        self.SCORE_WIN = 10000000     # Infinito pratico

        # Pre-calcolo Maschera Colonna Centrale (Indice 3)
        self.CENTER_MASK = 0
        for r in range(6):
            self.CENTER_MASK |= (1 << (3 * 7 + r))

    def evaluate(self, engine, player_idx):
        """
        Valuta lo stato della board.
        Priorità:
        1. Vittoria/Sconfitta (Assoluta)
        2. Euristica Ponderata (Bias applicati alla differenza)
        3. Anti-Blunder (Penalità suicidio)
        """

        # 1. CONTROLLO TERMINALE (Assoluto - Mai toccato dai bias)
        if engine.check_victory(player_idx):
            return self.SCORE_WIN

        opponent_idx = (player_idx + 1) % 2
        if engine.check_victory(opponent_idx):
            return -self.SCORE_WIN

        # 2. RECUPERO DATI E BIAS
        biases = self.profiler.get_adaptive_weights()
        my_pieces = engine.bitboards[player_idx]
        opp_pieces = engine.bitboards[opponent_idx]
        full_mask = my_pieces | opp_pieces

        score = 0

        # 3. VALUTAZIONE STRATEGICA (Centro)
        # Bias del centro (se presente nel profiler)
        c_bias = biases.get('center_weight', 1.0)

        my_center = (my_pieces & self.CENTER_MASK).bit_count() * self.SCORE_CENTER
        opp_center = (opp_pieces & self.CENTER_MASK).bit_count() * self.SCORE_CENTER

        # Applichiamo il bias alla differenza
        score += (my_center - opp_center) * c_bias

        # 4. VALUTAZIONE TATTICA DIREZIONALE (Simmetrica)

        # Verticale
        v_bias = biases.get('vertical_weakness', 1.0)
        v_score_my = self._evaluate_vertical(my_pieces, full_mask)
        v_score_opp = self._evaluate_vertical(opp_pieces, full_mask)
        score += (v_score_my - v_score_opp) * v_bias

        # Orizzontale
        h_bias = biases.get('horizontal_weakness', 1.0)
        h_score_my = self._evaluate_general_direction(my_pieces, full_mask, 7)
        h_score_opp = self._evaluate_general_direction(opp_pieces, full_mask, 7)
        score += (h_score_my - h_score_opp) * h_bias

        # Diagonali (Sommiamo / e \ prima di applicare il bias)
        d_bias = biases.get('diagonal_weakness', 1.0)

        d_score_my = self._evaluate_general_direction(my_pieces, full_mask, 6) + \
                     self._evaluate_general_direction(my_pieces, full_mask, 8)

        d_score_opp = self._evaluate_general_direction(opp_pieces, full_mask, 6) + \
                      self._evaluate_general_direction(opp_pieces, full_mask, 8)

        score += (d_score_my - d_score_opp) * d_bias

        # 5. BONUS TRAPPOLA A 7 (FORK) - Non biasato, troppo importante
        my_threats_mask = self._get_threat_mask(my_pieces, full_mask)
        if my_threats_mask.bit_count() >= 2:
            score += self.SCORE_DOUBLE_THREAT

        opp_threats_mask = self._get_threat_mask(opp_pieces, full_mask)
        if opp_threats_mask.bit_count() >= 2:
            score -= self.SCORE_DOUBLE_THREAT

        # 6. ANTI-BLUNDER CHECK (ZUGZWANG)
        # Penalità massiccia se la mossa offre una vittoria facile all'avversario

        # Controlliamo solo per noi (dove muoviamo noi), perché l'evaluator
        # valuta lo stato statico, ma il Minimax simulerà la mossa.
        # Questa logica serve a dire: "Questa configurazione è brutta perché ho celle avvelenate".

        # Recuperiamo dove l'avversario vincerebbe
        # (opp_threats_mask è già calcolata sopra)

        for col in range(7):
            current_h = engine.heights[col]
            if current_h < 5:
                # La cella sopra la prossima mossa
                cell_above_bit = 1 << ((col * 7) + (current_h + 1))

                # Se quella cella permette all'avversario di vincere...
                if cell_above_bit & opp_threats_mask:
                    # ...e se noi siamo costretti a giocare lì sotto?
                    # Questo controllo è euristico: penalizziamo lo stato se ci sono
                    # molte colonne "avvelenate" che riducono le nostre opzioni.
                     score -= self.SCORE_BLUNDER / 10 # Penalità posizionale

        return score

    # --- METODI DI SUPPORTO (Invariati nella logica bitwise) ---

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
        # Tris Verticali
        trios = pieces & (pieces >> 1) & (pieces >> 2)
        valid_trios = trios & (empty >> 3)
        score += valid_trios.bit_count() * self.SCORE_3
        # Coppie Verticali
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