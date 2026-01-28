"""
ai/evaluator.py
Modulo di Valutazione Euristica Adattiva.
Calcola il punteggio della scacchiera integrando:
1. Punteggi posizionali (Controllo Centro).
2. Punteggi Pattern Rigorosi (2-in-fila aperti, 3-in-fila).
3. Pesi psicologici del Profiler (Sfruttamento bias avversario).
"""


class AdaptiveEvaluator:
    def __init__(self, profiler):
        self.profiler = profiler

        # --- COSTANTI EURISTICHE ---
        self.SCORE_CENTER = 4  # Pedina nella colonna centrale

        # Gerarchia delle minacce
        self.SCORE_2_SINGLE = 5  # XX_ (Aperto da un lato)
        self.SCORE_2_DOUBLE = 15  # _XX_ (Aperto da due lati - Molto forte!)
        self.SCORE_2_SPLIT = 8  # X_X (Insidioso)
        self.SCORE_3 = 50  # XXX_ (Minaccia di vittoria)
        self.SCORE_WIN = 10000000  # Vittoria certa

        # Pre-calcolo Maschera Colonna Centrale (Indice 3)
        # Bit: 3, 10, 17, 24, 31, 38 (su board 7x6+1)
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
        # Se 'center_weight' > 1.0, l'IA lotterà più duramente per il centro
        my_center = bin(my_pieces & self.CENTER_MASK).count('1')
        opp_center = bin(opp_pieces & self.CENTER_MASK).count('1')

        score += (my_center * self.SCORE_CENTER * biases.get('center_weight', 1.0))
        score -= (opp_center * self.SCORE_CENTER)

        # 4. VALUTAZIONE TATTICA DIREZIONALE
        # Analizziamo ogni direzione separatamente per applicare i bias specifici.

        # --- VERTICALE (Shift 1) ---
        # Verticale è speciale: non ha "buchi" sotto, solo sopra.
        v_bias = biases.get('vertical_weakness', 1.0)
        score += self._evaluate_vertical(my_pieces, full_mask) * v_bias
        score -= self._evaluate_vertical(opp_pieces, full_mask)  # Difesa standard

        # --- ORIZZONTALE (Shift 7) ---
        h_bias = biases.get('horizontal_weakness', 1.0)
        score += self._evaluate_general_direction(my_pieces, full_mask, 7) * h_bias
        score -= self._evaluate_general_direction(opp_pieces, full_mask, 7)

        # --- DIAGONALI (Shift 6 e 8) ---
        d_bias = biases.get('diagonal_weakness', 1.0)
        # Diagonale \
        score += self._evaluate_general_direction(my_pieces, full_mask, 6) * d_bias
        score -= self._evaluate_general_direction(opp_pieces, full_mask, 6)
        # Diagonale /
        score += self._evaluate_general_direction(my_pieces, full_mask, 8) * d_bias
        score -= self._evaluate_general_direction(opp_pieces, full_mask, 8)

        return score

    def _evaluate_vertical(self, pieces, full_mask):
        """ Logica semplificata per la verticale (gravità permette solo crescita in alto) """
        score = 0
        empty = ~full_mask

        # Pattern 3 Verticali (XXX) con spazio sopra
        # Shift 1 = esposta in alto
        trios = pieces & (pieces >> 1) & (pieces >> 2)
        valid_trios = trios & (empty >> 3)  # Cella sopra vuota
        score += bin(valid_trios).count('1') * self.SCORE_3

        # Pattern 2 Verticali (XX) con spazio sopra
        pairs = pieces & (pieces >> 1)
        valid_pairs = pairs & (empty >> 2)
        score += bin(valid_pairs).count('1') * self.SCORE_2_SINGLE  # Verticale ha sempre un solo lato

        return score

    def _evaluate_general_direction(self, pieces, full_mask, shift):
        """
        Logica RIGOROSA per Orizzontale e Diagonali.
        Distingue tra minacce aperte, chiuse e doppie.
        """
        dir_score = 0
        empty = ~full_mask

        # --- 1. TRIS (3 Pezzi) ---
        # A. Consecutivi (XXX_)
        trios = pieces & (pieces >> shift) & (pieces >> (shift * 2))

        # Controlliamo spazio a Destra e Sinistra (per i tris consecutivi)
        t_right = (trios >> shift) & empty  # XXX_
        t_left = (trios << (shift * 3)) & empty  # _XXX

        # B. Tris con Buco (XX_X e X_XX)
        gap1 = pieces & (pieces >> shift) & (pieces >> (shift * 3))
        t_mid_right = (gap1 << (shift * 2)) & empty  # XX_X

        gap2 = pieces & (pieces >> (shift * 2)) & (pieces >> (shift * 3))
        t_mid_left = (gap2 << shift) & empty  # X_XX

        # Uniamo tutto (OR logico) per contare quante minacce di vittoria uniche ci sono
        total_threes = t_right | t_left | t_mid_right | t_mid_left
        dir_score += bin(total_threes).count('1') * self.SCORE_3

        # --- 2. COPPIE (2 Pezzi) ---
        # A. Consecutivi (XX)
        pairs = pieces & (pieces >> shift)

        # Analisi Pattern Aperti (Rigorosa)
        # _ X X _ (Doppia Apertura - Fortissimo!)
        open_left = (empty << shift)
        open_right = (empty >> (shift * 2))

        double_open = pairs & open_left & open_right

        # X X _ (Singola apertura destra) - Escludendo quelli che sono già double
        single_right = (pairs & open_right) & (~open_left)
        # _ X X (Singola apertura sinistra)
        single_left = (pairs & open_left) & (~open_right)

        # Assegnazione Punteggi Coppie
        dir_score += bin(double_open).count('1') * self.SCORE_2_DOUBLE
        dir_score += bin(single_right | single_left).count('1') * self.SCORE_2_SINGLE

        # B. Coppie Split (X _ X)
        # Richiede buco centrale vuoto E almeno un lato libero (_ X _ X oppure X _ X _)
        split = pieces & (pieces >> (shift * 2))
        gap_empty = (empty >> shift)  # Il buco in mezzo

        # Controlliamo se c'è spazio ai lati del panino X_X
        # _ X _ X
        s_left = split & gap_empty & (empty << shift)
        # X _ X _
        s_right = split & gap_empty & (empty >> (shift * 3))

        dir_score += bin(s_left | s_right).count('1') * self.SCORE_2_SPLIT

        return dir_score