"""
ai/profiler.py
Modulo di Profilazione Comportamentale.
Ottimizzato con .bit_count() e Clamping Strategico.
"""
from src.ai.analysis import get_threat_mask

class OpponentProfiler:
    def __init__(self):
        # Aggiunto center_weight come richiesto
        self.biases = {
            "missed_win": 1.0,
            "vertical_weakness": 1.0,
            "horizontal_weakness": 1.0,
            "diagonal_weakness": 1.0,
            "threat_underestimation": 1.0,
            "center_weight": 1.0
        }

        self.stats = {
            "moves_analyzed": 0,
            "fatal_errors": 0,
        }

    def _apply_bias(self, key, delta):
        """
        Aggiorna un bias applicando IMMEDIATAMENTE il tetto massimo.
        """
        LIMIT = 2.5
        MIN_VAL = 1.0

        if key not in self.biases: return

        new_value = self.biases[key] + delta
        self.biases[key] = max(MIN_VAL, min(new_value, LIMIT))

    def update(self, state_before, move_col, opponent_idx):
        """
        Analizza l'ultima mossa dell'avversario.
        state_before: tuple (p1_bitboard, p2_bitboard, heights)
        """
        self.stats["moves_analyzed"] += 1

        # Ricostruzione stato precedente
        p1_map_old = state_before[0]
        p2_map_old = state_before[1]
        full_mask_old = p1_map_old | p2_map_old

        # Calcolo bit giocato tramite matematica (senza loop)
        # La nuova pedina è in cima alla colonna vecchia
        # Recuperiamo l'altezza dalla lista heights nello state_before (indice 2)
        heights_old = state_before[2]
        played_bit = 1 << heights_old[move_col]

        opp_pieces = state_before[opponent_idx] # Pezzi avversario PRIMA della mossa
        my_pieces = state_before[(opponent_idx + 1) % 2] # Miei pezzi

        # --- FASE 1: KILLER INSTINCT (Missed Win) ---
        # L'avversario poteva vincere ma non l'ha fatto?
        winning_spots = get_threat_mask(opp_pieces, full_mask_old)

        if winning_spots > 0:
            if (winning_spots & played_bit) == 0:
                print(f"[PROFILER] L'avversario ha mancato una vittoria LETALE!")
                self._apply_bias("missed_win", 0.5)
                self.stats["fatal_errors"] += 1

        # --- FASE 2: DIFESA (Missed Threat) ---
        # Noi potevamo vincere al prossimo turno, lui ci ha bloccato?
        my_lethal_threats = get_threat_mask(my_pieces, full_mask_old)

        if my_lethal_threats > 0:
            if (my_lethal_threats & played_bit) != 0:
                # Ha parato! Riduciamo leggermente i bias (gioca bene)
                self._decay_biases(0.01)
            else:
                print(f"[PROFILER] L'avversario non ha parato una nostra vittoria!")
                self._analyze_missed_threat_type(my_pieces, my_lethal_threats)
                self._apply_bias("threat_underestimation", 0.3)
                self.stats["fatal_errors"] += 1

        # --- FASE 3: ANALISI POSIZIONALE ---
        if winning_spots == 0 and my_lethal_threats == 0:
            self._check_positional_errors(my_pieces, played_bit, full_mask_old)

    def _analyze_missed_threat_type(self, my_pieces, threat_mask):
        # Verticale
        vert = my_pieces & (my_pieces >> 1) & (my_pieces >> 2)
        if ((vert << 3) & threat_mask) != 0:
            self._apply_bias("vertical_weakness", 0.2)
            return

        # Orizzontale
        horiz_check = self._get_directional_threat(my_pieces, 7)
        if (horiz_check & threat_mask) != 0:
            self._apply_bias("horizontal_weakness", 0.2)
            return

        # Diagonali
        diag1 = self._get_directional_threat(my_pieces, 6)
        diag2 = self._get_directional_threat(my_pieces, 8)

        if ((diag1 | diag2) & threat_mask) != 0:
            self._apply_bias("diagonal_weakness", 0.4)
            print("[PROFILER] Bias Rilevato: Cecità Diagonale")

    def _get_directional_threat(self, pieces, shift):
        threats = 0
        trios = pieces & (pieces >> shift) & (pieces >> (shift * 2))
        threats |= (trios << (shift * 3)) | (trios >> shift)

        gap1 = pieces & (pieces >> shift) & (pieces >> (shift * 3))
        threats |= (gap1 << (shift * 2))
        gap2 = pieces & (pieces >> (shift * 2)) & (pieces >> (shift * 3))
        threats |= (gap2 << shift)
        return threats

    def _check_positional_errors(self, my_pieces, played_bit, full_mask):
        # Controlliamo solo le diagonali come indicatore chiave
        for shift in [6, 8]:
            pairs = my_pieces & (my_pieces >> shift)
            expansion_slots = (pairs >> shift) | (pairs << (shift * 2))
            expansion_slots &= ~full_mask

            if expansion_slots > 0:
                # Se l'avversario ignora le nostre espansioni diagonali
                if (expansion_slots & played_bit) == 0:
                    self._apply_bias("diagonal_weakness", 0.05)

    def _decay_biases(self, amount):
        for k in self.biases:
            if self.biases[k] > 1.0:
                self._apply_bias(k, -amount)

    def get_adaptive_weights(self):
        return self.biases