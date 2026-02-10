"""
src/ai/profiler.py
Versione CHECK-MATE:
Corregge il bug delle "Minacce Volanti".
Il bias aumenta SOLO se il bot ignora una minaccia che era FISICAMENTE GIOCABILE (playable_mask).
Questo impedirà al bias orizzontale di salire ingiustamente.
"""
from src.ai.analysis import get_threat_mask

class OpponentProfiler:
    def __init__(self):
        self.biases = {
            "missed_win": 1.0,
            "vertical_weakness": 1.0,
            "horizontal_weakness": 1.0,
            "diagonal_weakness": 1.0,
            "threat_underestimation": 1.0,
            "center_weight": 1.0
        }

        # --- MODIFICA: LEARNING RATES ACCELERATI ---
        # Aumentiamo i delta per reagire entro le prime 5-10 mosse.
        self.RATES = {
            "lethal": 0.8,      # RADDOPPIATO: Se manca una vittoria, l'avversario è cieco.
            "strategic": 0.3,   # TRIPLICATO: Se ignora una coppia, puntiamo subito lì.
            "correction": 0.1   # Se para, riduciamo il bias più velocemente per non diventare arroganti.
        }

        # --- MODIFICA: SOGLIE DI EXPLOIT ---
        # Abbassiamo la soglia di confidenza per iniziare a "predare" prima.
        self.CONFIDENCE_THRESHOLD = 1.1  # Prima era 1.2
        self.ARROGANCE_THRESHOLD = 2.0
        self.LIMIT = 4.0                 # Alzato: Permettiamo all'IA di diventare ossessionata dai difetti.
        self.SMOOTHING = 0.7             # Aumentato: Meno "filtro", più reattività immediata.

        self.stats = {"moves_analyzed": 0, "fatal_errors": 0, "tactical_blunders": 0}


    def _apply_bias(self, key, delta):
        MIN_VAL = 0.8
        if key not in self.biases: return
        # Lo smoothing più alto rende l'apprendimento più "nervoso" e veloce.
        smoothed_delta = delta * self.SMOOTHING
        new_value = self.biases[key] + smoothed_delta
        self.biases[key] = max(MIN_VAL, min(new_value, self.LIMIT))

    def cooling_after_loss(self):
        applied = False
        COOLING_FACTOR = 0.15 # Raffreddamento più rapido in caso di sconfitta imprevista.
        for k in self.biases:
            if self.biases[k] >= self.ARROGANCE_THRESHOLD:
                excess = self.biases[k] - 1.0
                self.biases[k] = 1.0 + (excess * (1 - COOLING_FACTOR))
                applied = True
                print(f"[PROFILER] Bias '{k}' punito (era > {self.ARROGANCE_THRESHOLD})")
        if not applied:
            print(f"[PROFILER] Nessun bias sopra {self.ARROGANCE_THRESHOLD}.")


    def update(self, state_before, move_col, opponent_idx):
        self.stats["moves_analyzed"] += 1
        heights_old = state_before[2]
        played_bit = 1 << heights_old[move_col]

        # Maschera delle mosse legali (solo la prima cella libera per ogni colonna)
        playable_mask = 0
        for c in range(7):
            if heights_old[c] < (c * 7 + 6):
                playable_mask |= (1 << heights_old[c])

        opp_pieces = state_before[opponent_idx] # Bot
        my_pieces = state_before[(opponent_idx + 1) % 2] # IA

        # 1. KILLER INSTINCT (Lethal)
        # Se l'avversario aveva una mossa vincente e non l'ha giocata.
        winning_spots = get_threat_mask(opp_pieces, opp_pieces | my_pieces) & playable_mask
        if winning_spots > 0 and (winning_spots & played_bit) == 0:
            self._apply_bias("missed_win", self.RATES["lethal"])
            # Se manca una vittoria, aumenta drasticamente anche la sottovalutazione generale delle minacce.
            self._apply_bias("threat_underestimation", self.RATES["lethal"] * 0.5)
            self.stats["tactical_blunders"] += 1

        # 2. ANALISI STRATEGICA DIFFERENZIALE
        # Passiamo playable_mask per ignorare le minacce "volanti" (irraggiungibili)
        self._analyze_response(my_pieces, played_bit, playable_mask)

    def _analyze_response(self, my_pieces, played_bit, playable_mask):
        """
        Analizza se la mossa giocata blocca una minaccia o la ignora.
        Considera SOLO le minacce che erano effettivamente giocabili (playable_mask).
        """
        # --- VERTICALE ---
        if (played_bit >> 1) & my_pieces and (played_bit >> 2) & my_pieces:
            self._apply_bias("vertical_weakness", -self.RATES["correction"])

        # --- ORIZZONTALE ---
        h_threats = self._get_potential_threats(my_pieces, 7)
        if h_threats & played_bit:
            self._apply_bias("horizontal_weakness", -self.RATES["correction"])
        elif (h_threats & playable_mask):
            # Aggiornamento aggressivo: l'avversario ha ignorato una minaccia orizzontale.
            self._apply_bias("horizontal_weakness", self.RATES["strategic"])
            self._apply_bias("threat_underestimation", self.RATES["strategic"] * 0.3)

        # --- DIAGONALI ---
        d_threats = self._get_potential_threats(my_pieces, 6) | self._get_potential_threats(my_pieces, 8)
        if d_threats & played_bit:
            self._apply_bias("diagonal_weakness", -self.RATES["correction"])
        elif (d_threats & playable_mask):
            # Se l'avversario ignora le diagonali, dobbiamo punirlo ferocemente.
            self._apply_bias("diagonal_weakness", self.RATES["strategic"] * 1.5)
            self._apply_bias("threat_underestimation", self.RATES["strategic"] * 0.5)

    def _get_potential_threats(self, pieces, shift):
        """
        Genera una maschera bitwise per rilevare coppie o tris che creano minacce immediate.
        """
        # Sposta a destra (controlla sinistra)
        shifted_right = pieces >> shift
        pairs_right = pieces & shifted_right
        threats_left = pairs_right >> shift

        # Sposta a sinistra (controlla destra)
        shifted_left = pieces << shift
        pairs_left = pieces & shifted_left
        threats_right = pairs_left << shift

        # Pattern Gap: X_X
        gap_base = pieces & (pieces >> (shift * 2))
        threats_gap = gap_base << shift

        return threats_left | threats_right | threats_gap

    def _decay_biases(self, amount):
        """ Metodo per ridurre i bias nel tempo (opzionale). """
        pass


    def get_adaptive_weights(self):
        return {k: (v if v >= self.CONFIDENCE_THRESHOLD else 1.0) for k, v in self.biases.items()}