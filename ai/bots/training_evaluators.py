"""
ai/bots/training_evaluators.py
Evaluator specializzati per l'allenamento.
Replicano i bias e i difetti dei vecchi bot usando la nuova tecnologia Bitboard.
"""


class TrainingBaseEvaluator:
    """
    Classe base che contiene la logica comune di conteggio pattern.
    I bot specifici erediteranno da qui e cambieranno solo i PESI.
    """

    def __init__(self):
        # Valori base del vecchio MinimaxBotNovice
        self.SCORE_WIN = 10000000
        self.SCORE_3 = 5  # 3 pezzi + 1 vuoto
        self.SCORE_2 = 2  # 2 pezzi + 2 vuoti
        self.SCORE_CENTER = 3  # Pezzo al centro

        # Pesi Difensivi Base (Quanto mi preoccupo delle minacce avversarie?)
        # Standard: -4 punti per un 3-in-fila avversario
        self.DEFENSE_WEIGHT_3 = 4.0

        # Configurazione Pesi Direzionali (Default: 1.0 = Standard)
        self.weights = {
            'vertical_attack': 1.0, 'vertical_defense': 1.0,
            'horizontal_attack': 1.0, 'horizontal_defense': 1.0,
            'diagonal_attack': 1.0, 'diagonal_defense': 1.0,
            'center_bias': 1.0  # Moltiplicatore per il controllo centro
        }
        self.center_col_idx = 3

    def evaluate(self, engine, player_idx):
        # 1. Controllo Vittoria/Sconfitta (Immediata)
        if engine.check_victory(player_idx): return self.SCORE_WIN
        opponent_idx = (player_idx + 1) % 2
        if engine.check_victory(opponent_idx): return -self.SCORE_WIN

        my_pieces = engine.bitboards[player_idx]
        opp_pieces = engine.bitboards[opponent_idx]
        full_mask = my_pieces | opp_pieces
        empty_mask = ~full_mask

        score = 0

        # 2. Controllo Centro (Replica logica Novice)
        center_mask = 0
        for r in range(6):
            center_mask |= (1 << (self.center_col_idx * 7 + r))

        my_center_count = bin(my_pieces & center_mask).count('1')
        score += (my_center_count * self.SCORE_CENTER * self.weights['center_bias'])

        # 3. Analisi Pattern per Direzione
        # Verticale
        score += self._score_direction(my_pieces, opp_pieces, empty_mask, 1,
                                       self.weights['vertical_attack'], self.weights['vertical_defense'])
        # Orizzontale (Shift 7)
        score += self._score_direction(my_pieces, opp_pieces, empty_mask, 7,
                                       self.weights['horizontal_attack'], self.weights['horizontal_defense'])
        # Diagonale 1 (Shift 6)
        score += self._score_direction(my_pieces, opp_pieces, empty_mask, 6,
                                       self.weights['diagonal_attack'], self.weights['diagonal_defense'])
        # Diagonale 2 (Shift 8)
        score += self._score_direction(my_pieces, opp_pieces, empty_mask, 8,
                                       self.weights['diagonal_attack'], self.weights['diagonal_defense'])

        return score

    def _score_direction(self, my_p, opp_p, empty, shift, w_attack, w_defense):
        """ Calcola punteggio netto per una direzione applicando i pesi specifici """
        net_score = 0

        # --- MIEI PUNTI (Attacco) ---
        # 3 in fila (con spazio)
        # Cerchiamo pattern XXX_ o _XXX ecc.
        # Semplificazione veloce bitwise: (bits & (bits>>s) & (bits>>2s))
        my_3 = my_p & (my_p >> shift) & (my_p >> (shift * 2))
        # Validiamo con spazio vuoto
        valid_my_3 = (my_3 >> shift) & empty | (my_3 << (shift * 3)) & empty

        # 2 in fila (con spazio)
        my_2 = my_p & (my_p >> shift)
        valid_my_2 = (my_2 >> shift) & empty

        net_score += bin(valid_my_3).count('1') * self.SCORE_3 * w_attack
        net_score += bin(valid_my_2).count('1') * self.SCORE_2 * w_attack

        # --- PUNTI AVVERSARIO (Difesa) ---
        # 3 in fila avversari (Minaccia!)
        opp_3 = opp_p & (opp_p >> shift) & (opp_p >> (shift * 2))
        valid_opp_3 = (opp_3 >> shift) & empty | (opp_3 << (shift * 3)) & empty

        # Sottraiamo punti in base al peso difensivo
        # Se w_defense è basso (es. 0.25), sottraiamo poco -> il bot ignora la minaccia
        net_score -= bin(valid_opp_3).count('1') * self.DEFENSE_WEIGHT_3 * w_defense

        return net_score


# ==============================================================================
# 1. IL NOVIZIO (Casual Human) - Depth consigliata: 2
# ==============================================================================
class CasualEvaluator(TrainingBaseEvaluator):
    def __init__(self):
        super().__init__()
        # Pesi standard (1.0).
        # Replica esattamente il punteggio del tuo "MinimaxBotNovice"
        # (+100 win, +5 trio, +2 pair, -4 threat, +3 center)
        pass

    # ==============================================================================


# 2. IL CIECO DIAGONALE (Diagonal Defensive Flaw) - Depth consigliata: 4
# ==============================================================================
class DiagonalBlinderEvaluator(TrainingBaseEvaluator):
    def __init__(self):
        super().__init__()
        # Attacco: 100% efficacia su tutto (come il tuo codice originale)
        self.weights['diagonal_attack'] = 1.0

        # Difesa: DEBOLE sulle diagonali
        # Nel tuo codice: "-1 invece di -4".
        # Quindi il peso è 1/4 = 0.25
        self.weights['diagonal_defense'] = 0.25

        # Difesa Verticale/Orizzontale rimane Standard (1.0) -> -4 punti


# ==============================================================================
# 3. IL BORDISTA (Edge Runner) - Depth consigliata: 3
# ==============================================================================
class EdgeRunnerEvaluator(TrainingBaseEvaluator):
    def __init__(self):
        super().__init__()
        # Strategia: Odia il centro.
        # Invertiamo il peso del centro per renderlo negativo
        self.weights['center_bias'] = -20.0

        # Opzionale: potremmo dare bonus alle colonne laterali,
        # ma un malus forte al centro basta per spingerlo ai bordi.