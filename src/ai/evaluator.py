"""
ai/evaluator.py
Versione GOLD: Asimmetria Pura.
- Difesa: Assoluta e Paranoica (x20) contro i Tris reali.
- Attacco: Guidato dai Bias, senza calcoli di parità fantasma.
"""

class AdaptiveEvaluator:
    def __init__(self, profiler):
        self.profiler = profiler

        # Punteggi Base
        self.SCORE_CENTER = 7        # Aumentato leggermente per controllo posizionale
        self.SCORE_2 = 10            # Coppie
        self.SCORE_3 = 100           # Tris Base

        # Punteggi Speciali
        self.SCORE_DOUBLE_THREAT = 900  # Forchetta
        self.SCORE_WIN = 10000000

        # FATTORI DI MOLTIPLICAZIONE
        # Se l'avversario ha un tris, la penalità è 100 * 20 = 2000.
        # È sufficiente a bloccare qualsiasi velleità offensiva (max ~1000).
        self.THREAT_MULTIPLIER = 20.0

        self.CENTER_MASK = 0
        for r in range(6):
            self.CENTER_MASK |= (1 << (3 * 7 + r))

    def evaluate(self, engine, player_idx):
        if engine.check_victory(player_idx): return self.SCORE_WIN
        opponent_idx = (player_idx + 1) % 2
        if engine.check_victory(opponent_idx): return -self.SCORE_WIN

        biases = self.profiler.get_adaptive_weights()
        my_pieces = engine.bitboards[player_idx]
        opp_pieces = engine.bitboards[opponent_idx]
        full_mask = my_pieces | opp_pieces

        score = 0

        # --- 1. ATTACCO PREDATORIO (Guidato dai Bias) ---
        # Se l'avversario è debole in una direzione, il valore di quell'attacco
        # viene amplificato per forzare situazioni che il suo depth ridotto non vede.

        # Centro: Fondamentale per le diagonali
        score += (my_pieces & self.CENTER_MASK).bit_count() * self.SCORE_CENTER * biases.get('center_weight', 1.0)

        # Direzioni con moltiplicatore di aggressività
        # Se bias > 1.0, l'attacco in quella direzione diventa prioritario
        score += self._score_position(my_pieces, full_mask, 1) * (biases.get('vertical_weakness', 1.0) ** 2)
        score += self._score_position(my_pieces, full_mask, 7) * (biases.get('horizontal_weakness', 1.0) ** 2)

        # Diagonali: Il punto debole tipico dei bot a basso depth.
        # Usiamo un esponente per rendere l'IA "ossessionata" se il bias è alto.
        diag_score = self._score_position(my_pieces, full_mask, 6) + \
                     self._score_position(my_pieces, full_mask, 8)
        score += diag_score * (biases.get('diagonal_weakness', 1.0) ** 2)

        # --- 2. DIFESA ADATTIVA (Sconto Confidenza) ---
        # Se sappiamo che l'avversario è scarso (bias alto), possiamo permetterci
        # di essere meno "paranoici" in difesa per dare priorità all'attacco vincente.

        # Calcolo minacce nemiche
        opp_threats = 0
        opp_threats += self._score_defense(opp_pieces, full_mask, 1)
        opp_threats += self._score_defense(opp_pieces, full_mask, 7)
        opp_threats += self._score_defense(opp_pieces, full_mask, 6) + \
                       self._score_defense(opp_pieces, full_mask, 8)

        # --- MIGLIORIA: Se l'avversario sottovaluta le minacce, riduciamo il peso
        # della nostra difesa (Risk Management) per essere più aggressivi.
        defense_relaxation = 1.0 / biases.get('threat_underestimation', 1.0)
        score -= (opp_threats * defense_relaxation)

        # Penalità centro avversario
        score -= (opp_pieces & self.CENTER_MASK).bit_count() * self.SCORE_CENTER

        # --- 3. FORCHETTE E TATTICA (Anti-Novizio) ---
        # Un bot a depth 2 non può prevedere una forchetta. Se rileviamo un alto
        # bias di sottovalutazione minacce, puntiamo tutto sulla creazione di double threats.

        my_threat_mask = self._get_threat_mask(my_pieces, full_mask)
        if my_threat_mask.bit_count() >= 2:
            # Moltiplichiamo il bonus forchetta per il bias dell'avversario
            score += self.SCORE_DOUBLE_THREAT * biases.get('threat_underestimation', 1.0)

        # Se l'avversario ha una forchetta, è grave, ma se è un bot debole
        # potrebbe non completarla, quindi non esageriamo con la penalità se abbiamo un attacco forte.
        if self._get_threat_mask(opp_pieces, full_mask).bit_count() >= 2:
            score -= (self.SCORE_DOUBLE_THREAT * 1.5) * defense_relaxation

        return score

    def _score_position(self, pieces, full_mask, shift):
        """ Calcola il punteggio OFFENSIVO """
        score = 0
        empty = ~full_mask

        # TRIS (XXX_)
        trios = pieces & (pieces >> shift) & (pieces >> (shift * 2))
        open_ends = ((trios >> shift) & empty) | ((trios << (shift * 3)) & empty)

        # TRIS CON BUCO (XX_X)
        gap1 = (pieces & (pieces >> shift) & (pieces >> (shift * 3))) << (shift * 2) & empty
        gap2 = (pieces & (pieces >> (shift * 2)) & (pieces >> (shift * 3))) << shift & empty

        # Totale Tris Potenziali
        score += (open_ends | gap1 | gap2).bit_count() * self.SCORE_3

        # COPPIE (XX) - Importanti per costruire
        pairs = pieces & (pieces >> shift)
        open_both = (pairs & (empty << shift) & (empty >> (shift * 2)))
        score += open_both.bit_count() * self.SCORE_2

        return score

    def _score_defense(self, pieces, full_mask, shift):
        """ Calcola il punteggio DIFENSIVO (Solo minacce reali) """
        score = 0
        empty = ~full_mask

        # TRIS AVVERSARIO (Minaccia Letale)
        trios = pieces & (pieces >> shift) & (pieces >> (shift * 2))
        threats = ((trios >> shift) & empty) | ((trios << (shift * 3)) & empty)

        gap1 = (pieces & (pieces >> shift) & (pieces >> (shift * 3))) << (shift * 2) & empty
        gap2 = (pieces & (pieces >> (shift * 2)) & (pieces >> (shift * 3))) << shift & empty

        total_threats = (threats | gap1 | gap2).bit_count()

        # APPLICAZIONE MOLTIPLICATORE PAURA
        # Solo i tris attivano la super difesa. Le coppie avversarie le ignoriamo (score 0)
        # per non distrarci dal nostro attacco.
        score += total_threats * (self.SCORE_3 * self.THREAT_MULTIPLIER)

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