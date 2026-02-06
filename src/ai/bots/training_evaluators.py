"""
ai/bots/training_evaluators.py
Evaluator specializzati per l'allenamento.
Replicano i bias e i difetti dei vecchi bot usando la nuova tecnologia Bitboard.
Include un fattore di 'Rumore' (Noise) per simulare l'errore umano.
"""
import random

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
        # 1. Controllo Vittoria/Sconfitta (Immediata - NO RUMORE QUI)
        # Se c'è una vittoria certa, il bot non deve avere dubbi.
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

        # Ottimizzazione: .bit_count() invece di bin().count()
        my_center_count = (my_pieces & center_mask).bit_count()
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

        # 4. APPLICAZIONE RUMORE (Noise)
        # Variamo il punteggio del +/- 20% per simulare indecisione o errore di giudizio.
        # Moltiplichiamo per un fattore casuale tra 0.8 (80%) e 1.2 (120%).
        noise_factor = random.uniform(0.8, 1.2)
        score *= noise_factor

        return score

    def _score_direction(self, my_p, opp_p, empty, shift, w_attack, w_defense):
        """ Calcola punteggio netto per una direzione applicando i pesi specifici """
        net_score = 0

        # --- MIEI PUNTI (Attacco) ---
        # 3 in fila
        my_3 = my_p & (my_p >> shift) & (my_p >> (shift * 2))
        valid_my_3 = (my_3 >> shift) & empty | (my_3 << (shift * 3)) & empty

        # 2 in fila
        my_2 = my_p & (my_p >> shift)
        valid_my_2 = (my_2 >> shift) & empty

        # Ottimizzazione .bit_count()
        net_score += valid_my_3.bit_count() * self.SCORE_3 * w_attack
        net_score += valid_my_2.bit_count() * self.SCORE_2 * w_attack

        # --- PUNTI AVVERSARIO (Difesa) ---
        opp_3 = opp_p & (opp_p >> shift) & (opp_p >> (shift * 2))
        valid_opp_3 = (opp_3 >> shift) & empty | (opp_3 << (shift * 3)) & empty

        net_score -= valid_opp_3.bit_count() * self.DEFENSE_WEIGHT_3 * w_defense

        return net_score


# ==============================================================================
# 1. IL NOVIZIO (Casual Human)
# ==============================================================================
class CasualEvaluator(TrainingBaseEvaluator):
    def __init__(self):
        super().__init__()
        pass


# ==============================================================================
# 2. IL CIECO DIAGONALE (Diagonal Defensive Flaw)
# ==============================================================================
class DiagonalBlinderEvaluator(TrainingBaseEvaluator):
    def __init__(self):
        super().__init__()
        # Attacco: 100%
        self.weights['diagonal_attack'] = 1.0
        # Difesa: DEBOLE sulle diagonali (0.25)
        self.weights['diagonal_defense'] = 0.25


# ==============================================================================
# 3. IL BORDISTA (Edge Runner)
# ==============================================================================
class EdgeRunnerEvaluator(TrainingBaseEvaluator):
    def __init__(self):
        super().__init__()
        # Odia il centro
        self.weights['center_bias'] = -20.0