"""
ai/evaluator.py
Modulo di Valutazione Euristica Adattiva.
Calcola il punteggio della scacchiera integrando:
1. Punteggi posizionali (Controllo Centro).
2. Punteggi Pattern Rigorosi (2-in-fila aperti, 3-in-fila).
3. Punteggi "Killer" (Trappole a doppia minaccia / Fork).
4. Pesi psicologici del Profiler (Sfruttamento bias avversario).
"""


class AdaptiveEvaluator:
    def __init__(self, profiler):
        self.profiler = profiler

        # --- COSTANTI EURISTICHE ---
        self.SCORE_CENTER = 4         # Pedina nella colonna centrale

        # Gerarchia delle minacce
        self.SCORE_2_SINGLE = 5       # XX_ (Aperto da un lato)
        self.SCORE_2_SPLIT = 8        # X_X (Insidioso)
        self.SCORE_2_DOUBLE = 15      # _XX_ (Aperto da due lati - Molto forte!)
        self.SCORE_3 = 50             # XXX_ (Minaccia di vittoria)

        # --- NUOVA COSTANTE: DOUBLE THREAT (FORK) ---
        # Vale quasi quanto una vittoria, perché garantisce la vittoria al turno dopo
        self.SCORE_DOUBLE_THREAT = 5000

        self.SCORE_WIN = 10000000     # Vittoria certa

        # Pre-calcolo Maschera Colonna Centrale (Indice 3)
        self.CENTER_MASK = 0
        for r in range(6):
            self.CENTER_MASK |= (1 << (3 * 7 + r))

    def evaluate(self, engine, player_idx):
        """
        Calcola il punteggio netto: (Mio Score Adattivo) - (Score Avversario Standard).
        """
        # 1. CONTROLLO TERMINALE (Vittorie/Sconfitte certe)
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
        my_center = bin(my_pieces & self.CENTER_MASK).count('1')
        opp_center = bin(opp_pieces & self.CENTER_MASK).count('1')

        score += (my_center * self.SCORE_CENTER * biases.get('center_weight', 1.0))
        score -= (opp_center * self.SCORE_CENTER)

        # 4. VALUTAZIONE TATTICA DIREZIONALE
        # --- VERTICALE ---
        v_bias = biases.get('vertical_weakness', 1.0)
        score += self._evaluate_vertical(my_pieces, full_mask) * v_bias
        score -= self._evaluate_vertical(opp_pieces, full_mask)

        # --- ORIZZONTALE ---
        h_bias = biases.get('horizontal_weakness', 1.0)
        score += self._evaluate_general_direction(my_pieces, full_mask, 7) * h_bias
        score -= self._evaluate_general_direction(opp_pieces, full_mask, 7)

        # --- DIAGONALI ---
        d_bias = biases.get('diagonal_weakness', 1.0)
        score += self._evaluate_general_direction(my_pieces, full_mask, 6) * d_bias # \
        score -= self._evaluate_general_direction(opp_pieces, full_mask, 6)
        score += self._evaluate_general_direction(my_pieces, full_mask, 8) * d_bias # /
        score -= self._evaluate_general_direction(opp_pieces, full_mask, 8)

        # 5. CONTROLLO TRAPPOLA A 7 (FORK / DOUBLE THREAT) [NUOVO]
        # Calcoliamo tutte le caselle che, se riempite, darebbero la vittoria immediata
        my_threats_mask = self._get_threat_mask(my_pieces, full_mask)
        num_my_threats = bin(my_threats_mask).count('1')

        # Se ho 2 o più modi diversi di vincere, ho creato una forchetta inarrestabile
        if num_my_threats >= 2:
            score += self.SCORE_DOUBLE_THREAT

        # Facciamo lo stesso controllo per l'avversario (paura pura!)
        opp_threats_mask = self._get_threat_mask(opp_pieces, full_mask)
        num_opp_threats = bin(opp_threats_mask).count('1')

        if num_opp_threats >= 2:
            score -= self.SCORE_DOUBLE_THREAT

        return score

    def _get_threat_mask(self, p, full_mask):
        """
        Ritorna una bitboard dove i bit a 1 rappresentano le celle vuote
        che completano un 4-in-fila per il giocatore 'p'.
        """
        empty = ~full_mask
        threats = 0

        # Controlliamo tutte le direzioni: Verticale(1), Orizzontale(7), Diag1(6), Diag2(8)
        for d in [1, 7, 6, 8]:
            # Pattern: _XXX (Buco all'inizio)
            threats |= (p >> d) & (p >> (2*d)) & (p >> (3*d)) & empty
            # Pattern: X_XX (Buco in seconda posizione)
            threats |= (p << d) & (p >> d) & (p >> (2*d)) & empty
            # Pattern: XX_X (Buco in terza posizione)
            threats |= (p << (2*d)) & (p << d) & (p >> d) & empty
            # Pattern: XXX_ (Buco alla fine)
            threats |= (p << (3*d)) & (p << (2*d)) & (p << d) & empty

        return threats

    def _evaluate_vertical(self, pieces, full_mask):
        """ Logica semplificata per la verticale """
        score = 0
        empty = ~full_mask

        # Tris Verticali (XXX) con spazio sopra
        trios = pieces & (pieces >> 1) & (pieces >> 2)
        valid_trios = trios & (empty >> 3)
        score += bin(valid_trios).count('1') * self.SCORE_3

        # Coppie Verticali (XX) con spazio sopra
        pairs = pieces & (pieces >> 1)
        valid_pairs = pairs & (empty >> 2)
        score += bin(valid_pairs).count('1') * self.SCORE_2_SINGLE

        return score

    def _evaluate_general_direction(self, pieces, full_mask, shift):
        """ Logica pattern per Orizzontale e Diagonali """
        dir_score = 0
        empty = ~full_mask

        # --- 1. TRIS (3 Pezzi) ---
        # A. Consecutivi (XXX_)
        trios = pieces & (pieces >> shift) & (pieces >> (shift * 2))
        t_right = (trios >> shift) & empty
        t_left = (trios << (shift * 3)) & empty

        # B. Tris con Buco (XX_X e X_XX)
        gap1 = pieces & (pieces >> shift) & (pieces >> (shift * 3))
        t_mid_right = (gap1 << (shift * 2)) & empty
        gap2 = pieces & (pieces >> (shift * 2)) & (pieces >> (shift * 3))
        t_mid_left = (gap2 << shift) & empty

        total_threes = t_right | t_left | t_mid_right | t_mid_left
        dir_score += bin(total_threes).count('1') * self.SCORE_3

        # --- 2. COPPIE (2 Pezzi) ---
        pairs = pieces & (pieces >> shift)
        open_left = (empty << shift)
        open_right = (empty >> (shift * 2))

        double_open = pairs & open_left & open_right
        single_right = (pairs & open_right) & (~open_left)
        single_left = (pairs & open_left) & (~open_right)

        dir_score += bin(double_open).count('1') * self.SCORE_2_DOUBLE
        dir_score += bin(single_right | single_left).count('1') * self.SCORE_2_SINGLE

        # Coppie Split (X _ X)
        split = pieces & (pieces >> (shift * 2))
        gap_empty = (empty >> shift)
        s_left = split & gap_empty & (empty << shift)
        s_right = split & gap_empty & (empty >> (shift * 3))

        dir_score += bin(s_left | s_right).count('1') * self.SCORE_2_SPLIT

        return dir_score