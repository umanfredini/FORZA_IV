"""
ai/profiler.py
Modulo di Profilazione Comportamentale.
Analizza la discrepanza tra la "Mossa Ottimale" (Teoria dei Giochi)
e la "Mossa Effettuata" (Realtà) per calcolare i Bias cognitivi.
"""
from ai.analysis import get_threat_mask


class OpponentProfiler:
    def __init__(self):
        # HEATMAP DEI BIAS (1.0 = Standard)
        # Se un valore sale, significa che l'avversario è DEBOLE in quell'area.
        self.biases = {
            "missed_win": 1.0,  # Cecità alla propria vittoria (Killer Instinct assente)
            "vertical_weakness": 1.0,  # Ignora minacce verticali
            "horizontal_weakness": 1.0,  # Ignora minacce orizzontali
            "diagonal_weakness": 1.0,  # Ignora minacce diagonali (spesso il bias più alto)
            "threat_underestimation": 1.0  # Tendenza generale a ignorare le nostre minacce
        }

        # Storico per debugging e statistiche
        self.stats = {
            "moves_analyzed": 0,
            "fatal_errors": 0,  # Vittorie mancate o sconfitte non parate
        }

    def update(self, engine, state_before, move_col, opponent_idx):
        """
        Esegue l'autopsia della mossa avversaria.
        Confronta lo stato PRE-mossa con la decisione presa.
        """
        self.stats["moves_analyzed"] += 1

        # 1. RICOSTRUZIONE STATO PRECEDENTE
        p1_map, p2_map, heights = state_before
        full_mask = p1_map | p2_map

        # Determiniamo chi è chi
        # Se opponent_idx ha appena mosso, lui è l'Attuale, noi siamo l'Altro
        opp_pieces = p2_map if opponent_idx == 1 else p1_map  # Lui (Avversario)
        my_pieces = p1_map if opponent_idx == 1 else p2_map  # Noi (IA)

        # Calcoliamo la bitmask della mossa appena fatta
        # (Ci serve per vedere se interseca con le maschere delle minacce)
        # Recuperiamo l'altezza dove è caduta la pedina:
        # Attenzione: heights è lo stato PRIMA della mossa, quindi l'indice è corretto.
        played_bit = 1 << heights[move_col]

        # --- FASE 1: KILLER INSTINCT (Lui poteva vincere?) ---
        # Generiamo la maschera delle SUE vittorie immediate
        winning_spots = get_threat_mask(opp_pieces, full_mask)

        if winning_spots > 0:
            # Esisteva almeno una mossa vincente. Ha giocato lì?
            if (winning_spots & played_bit) == 0:
                # ERRORE GRAVE: Poteva vincere e non l'ha fatto.
                print(f"[PROFILER] L'avversario ha mancato una vittoria LETALE!")
                self.biases["missed_win"] += 0.5
                self.stats["fatal_errors"] += 1
            else:
                # Ha vinto. O comunque ha giocato per vincere. Bravo lui.
                pass

        # --- FASE 2: DIFESA (Noi stavamo per vincere?) ---
        # Generiamo la maschera delle NOSTRE vittorie immediate (minacce per lui)
        my_lethal_threats = get_threat_mask(my_pieces, full_mask)

        if my_lethal_threats > 0:
            # Noi avevamo una vittoria pronta. Lui l'ha bloccata?
            if (my_lethal_threats & played_bit) != 0:
                # Ha parato. Difesa solida.
                # Riduciamo leggermente i bias (sta giocando attento)
                self._decay_biases(0.01)
            else:
                # SUICIDIO: Non ha parato la nostra vittoria.
                # Cerchiamo di capire DI CHE TIPO era la minaccia che ha ignorato.
                print(f"[PROFILER] L'avversario non ha parato una nostra vittoria!")
                self._analyze_missed_threat_type(my_pieces, my_lethal_threats)
                self.biases["threat_underestimation"] += 0.3
                self.stats["fatal_errors"] += 1

        # --- FASE 3: ANALISI TATTICA (Minacce non letali ma pericolose) ---
        # Se non c'erano vittorie immediate, controlliamo se ha ignorato la costruzione
        # di pattern pericolosi (es. non ha chiuso una nostra diagonale aperta).
        # Questo richiede di analizzare i pattern specifici (Verticale/Diagonale).
        # (Implementazione raffinata che chiama l'analisi direzionale)
        if winning_spots == 0 and my_lethal_threats == 0:
            self._check_positional_errors(my_pieces, played_bit, full_mask)

    def _analyze_missed_threat_type(self, my_pieces, threat_mask):
        """
        Identifica geometricamente quale tipo di minaccia è stata ignorata
        per aggiornare il bias specifico (Verticale vs Orizzontale vs Diagonale).
        """
        # Ricalcoliamo le minacce per direzione per vedere quale corrisponde alla threat_mask

        # Verticale
        vert = my_pieces & (my_pieces >> 1) & (my_pieces >> 2)
        if ((vert << 3) & threat_mask) != 0:
            self.biases["vertical_weakness"] += 0.2
            return

        # Orizzontale
        horiz_check = self._get_directional_threat(my_pieces, 7)
        if (horiz_check & threat_mask) != 0:
            self.biases["horizontal_weakness"] += 0.2
            return

        # Diagonali (le accorpiamo o le teniamo separate)
        diag1 = self._get_directional_threat(my_pieces, 6)
        diag2 = self._get_directional_threat(my_pieces, 8)

        if ((diag1 | diag2) & threat_mask) != 0:
            self.biases["diagonal_weakness"] += 0.4  # Diagonali pesano di più!
            print("[PROFILER] Bias Aggiornato: Cecità Diagonale")

    def _get_directional_threat(self, pieces, shift):
        # Helper veloce per isolare minacce in una sola direzione
        # Copia della logica rigorosa di analysis.py ma per singola direzione
        threats = 0
        trios = pieces & (pieces >> shift) & (pieces >> (shift * 2))
        threats |= (trios << (shift * 3)) | (trios >> shift)

        # Buchi interni
        gap1 = pieces & (pieces >> shift) & (pieces >> (shift * 3))
        threats |= (gap1 << (shift * 2))
        gap2 = pieces & (pieces >> (shift * 2)) & (pieces >> (shift * 3))
        threats |= (gap2 << shift)

        return threats

    def _check_positional_errors(self, my_pieces, played_bit, full_mask):
        """
        Se non ci sono minacce letali, controlliamo se l'avversario
        ci ha lasciato espandere liberamente su una diagonale.
        """
        # Esempio: Noi abbiamo un 2-in-fila diagonale. Lui non l'ha chiuso.
        # Shift 6 e 8 (Diagonali)
        for shift in [6, 8]:
            pairs = my_pieces & (my_pieces >> shift)
            # Spazi vitali per la coppia
            expansion_slots = (pairs >> shift) | (pairs << (shift * 2))
            # Rimuoviamo occupati
            expansion_slots &= ~full_mask

            if expansion_slots > 0:
                # Avevamo spazio per espanderci. Ha giocato lì per bloccare?
                if (expansion_slots & played_bit) == 0:
                    # Non ha bloccato l'espansione diagonale. Bias lieve.
                    self.biases["diagonal_weakness"] += 0.05

    def _decay_biases(self, amount):
        """ Rilassamento: se gioca bene, i bias tornano verso 1.0 """
        for k in self.biases:
            if self.biases[k] > 1.0:
                self.biases[k] = max(1.0, self.biases[k] - amount)

    def get_adaptive_weights(self):
        return self.biases