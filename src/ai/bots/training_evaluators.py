"""
src/ai/bots/training_evaluators.py

Evaluator specializzati per l'allenamento.
Replicano i bias e i difetti dei vecchi bot usando la nuova tecnologia Bitboard.
Include un fattore di 'Rumore' (Noise) per simulare l'errore umano.
"""
import random

class TrainingBaseEvaluator:
    """
    Classe base che contiene la logica comune di conteggio pattern.
    I bot specifici erediteranno da qui e cambieranno solo i PESI nel __init__.
    """

    def __init__(self):
        # Valori base (simili al vecchio MinimaxBotNovice)
        self.SCORE_WIN = 10000000
        self.SCORE_3 = 5       # 3 pezzi + 1 vuoto (Minaccia/Opportunità)
        self.SCORE_2 = 2       # 2 pezzi + 2 vuoti (Costruzione)
        self.SCORE_CENTER = 3  # Pezzo nella colonna centrale

        # Pesi Difensivi Base
        # -4.0 significa che temo un tris avversario 4 volte più di quanto desidero un mio tris.
        self.DEFENSE_WEIGHT_3 = 4.0

        # Configurazione Pesi Direzionali (Default: 1.0 = Standard)
        # Modificando questi, creiamo le "personalità" dei bot.
        self.weights = {
            'vertical_attack': 1.0,   'vertical_defense': 1.0,
            'horizontal_attack': 1.0, 'horizontal_defense': 1.0,
            'diagonal_attack': 1.0,   'diagonal_defense': 1.0,
            'center_bias': 1.0        # Moltiplicatore per il controllo centro
        }
        self.center_col_idx = 3 # Colonna centrale per board 7x6

    def evaluate(self, engine, player_idx):
        # 1. Controllo Vittoria/Sconfitta (Immediata - NO RUMORE)
        # Se c'è una mossa vincente o perdente certa, la valutazione deve essere assoluta.
        if engine.check_victory(player_idx): return self.SCORE_WIN
        opponent_idx = (player_idx + 1) % 2
        if engine.check_victory(opponent_idx): return -self.SCORE_WIN

        # Recupero Bitboard
        my_pieces = engine.bitboards[player_idx]
        opp_pieces = engine.bitboards[opponent_idx]
        full_mask = my_pieces | opp_pieces
        empty_mask = ~full_mask

        score = 0

        # 2. Controllo Centro (Replica logica Novice)
        # Creiamo la maschera per la colonna centrale (bit 21..26)
        center_mask = 0
        for r in range(6):
            center_mask |= (1 << (self.center_col_idx * 7 + r))

        my_center_count = (my_pieces & center_mask).bit_count()
        score += (my_center_count * self.SCORE_CENTER * self.weights['center_bias'])

        # 3. Analisi Pattern per Direzione
        # Passiamo i pesi specifici per ogni direzione

        # Verticale (Shift 1)
        score += self._score_direction(my_pieces, opp_pieces, empty_mask, 1,
                                       self.weights['vertical_attack'], self.weights['vertical_defense'])
        # Orizzontale (Shift 7)
        score += self._score_direction(my_pieces, opp_pieces, empty_mask, 7,
                                       self.weights['horizontal_attack'], self.weights['horizontal_defense'])
        # Diagonale 1 / (Shift 6)
        score += self._score_direction(my_pieces, opp_pieces, empty_mask, 6,
                                       self.weights['diagonal_attack'], self.weights['diagonal_defense'])
        # Diagonale 2 \ (Shift 8)
        score += self._score_direction(my_pieces, opp_pieces, empty_mask, 8,
                                       self.weights['diagonal_attack'], self.weights['diagonal_defense'])

        # 4. APPLICAZIONE RUMORE (Noise)
        # Variamo il punteggio del +/- 20% per simulare "errore umano" o disattenzione.
        # Questo impedisce all'IA di "memorizzare" partite identiche contro un bot deterministico.
        noise_factor = random.uniform(0.8, 1.2)
        score *= noise_factor

        return score

    def _score_direction(self, my_p, opp_p, empty, shift, w_attack, w_defense):
        """
        Calcola punteggio netto per una direzione applicando i pesi specifici.
        Usa operazioni bitwise per trovare pattern XXX_ o _XXX.
        """
        net_score = 0

        # --- MIEI PUNTI (Attacco) ---
        # Trova 3 pezzi consecutivi
        my_3 = my_p & (my_p >> shift) & (my_p >> (shift * 2))
        # Controlla se c'è spazio PRIMA (_XXX) o DOPO (XXX_)
        valid_my_3 = ((my_3 >> shift) & empty) | ((my_3 << (shift * 3)) & empty)

        # Trova 2 pezzi consecutivi
        my_2 = my_p & (my_p >> shift)
        # Controlla spazio prima
        valid_my_2 = (my_2 >> shift) & empty
        # Nota: per semplicità questo training evaluator controlla solo _XX, non XX_ o X_X
        # È voluto per simulare un avversario non perfetto.

        net_score += valid_my_3.bit_count() * self.SCORE_3 * w_attack
        net_score += valid_my_2.bit_count() * self.SCORE_2 * w_attack

        # --- PUNTI AVVERSARIO (Difesa) ---
        opp_3 = opp_p & (opp_p >> shift) & (opp_p >> (shift * 2))
        valid_opp_3 = ((opp_3 >> shift) & empty) | ((opp_3 << (shift * 3)) & empty)

        # Sottraiamo punti se l'avversario ha minacce
        # Moltiplichiamo per w_defense: se è basso (es. 0.25), ignoriamo la minaccia!
        net_score -= valid_opp_3.bit_count() * self.DEFENSE_WEIGHT_3 * w_defense

        return net_score


# ==============================================================================
# 1. IL NOVIZIO (Casual Human)
# ==============================================================================
class CasualEvaluator(TrainingBaseEvaluator):
    """ Gioca in modo bilanciato ma non profondo. Parametri standard. """
    def __init__(self):
        super().__init__()
        # Tutto a 1.0, rumore attivo.


# ==============================================================================
# 2. IL CIECO DIAGONALE (Diagonal Defensive Flaw)
# ==============================================================================
class DiagonalBlinderEvaluator(TrainingBaseEvaluator):
    """
    Simula un giocatore che non vede bene le minacce diagonali.
    Ottimo per insegnare all'IA a sfruttare le diagonali.
    """
    def __init__(self):
        super().__init__()
        # Attacco standard
        self.weights['diagonal_attack'] = 1.0

        # DIFESA DIAGONALE ROTTA:
        # Pesa le minacce diagonali avversarie 1/4 del normale.
        # Il bot penserà: "Vabbè, ha 3 in diagonale, ma non è grave".
        self.weights['diagonal_defense'] = 0.25


# ==============================================================================
# 3. IL BORDISTA (Edge Runner)
# ==============================================================================
class EdgeRunnerEvaluator(TrainingBaseEvaluator):
    """
    Odia il centro. Gioca sui lati.
    Serve a insegnare all'IA a dominare il centro.
    """
    def __init__(self):
        super().__init__()
        # Penalità massiccia per il centro
        self.weights['center_bias'] = -20.0