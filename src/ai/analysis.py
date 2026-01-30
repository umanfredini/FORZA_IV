"""
ai/analysis.py
Versione Ingegneristica Definitiva.
Ottimizzato con .bit_count() per Python 3.10+
"""


def get_threat_mask(my_pieces, full_mask):
    """
    Identifica TUTTI i bit dove una mossa completerebbe un 4-in-fila.
    Controlla: XXX_, _XXX, XX_X, X_XX.
    """
    threats = 0
    # Orizzontale, Diagonale \, Diagonale /
    for shift in [7, 6, 8]:
        # Pattern consecutivi (XXX_ e _XXX)
        # Tre pezzi di fila
        trios_1 = my_pieces & (my_pieces >> shift) & (my_pieces >> (shift * 2))
        # Spazio a destra: XXX_
        threats |= (trios_1 << (shift * 3))
        # Spazio a sinistra: _XXX
        threats |= (trios_1 >> shift)

        # Pattern con buco (XX_X e X_XX)
        # XX_X: pezzi in 0, 1, 3. Buco in 2.
        threats |= (my_pieces & (my_pieces >> shift) & (my_pieces >> (shift * 3))) << (shift * 2)
        # X_XX: pezzi in 0, 2, 3. Buco in 1.
        threats |= (my_pieces & (my_pieces >> (shift * 2)) & (my_pieces >> (shift * 3))) << shift

    # Verticale: solo XXX_ (il vuoto può essere solo sopra)
    vert_trios = my_pieces & (my_pieces >> 1) & (my_pieces >> 2)
    threats |= (vert_trios << 3)

    # Fondamentale: una minaccia è reale solo se lo spazio è VUOTO
    return threats & ~full_mask


def count_all_patterns(my_pieces, full_mask):
    """
    Censisce ogni struttura (2 o 3 pezzi) che ha lo spazio vitale
    per diventare un 4-in-fila in futuro.
    Ottimizzato usando .bit_count() invece di bin().count().
    """
    stats = {'threes': 0, 'twos': 0}
    empty = ~full_mask

    # --- ANALISI TRIS ---
    # Usiamo direttamente get_threat_mask per coerenza.
    threat_map = get_threat_mask(my_pieces, full_mask)
    # OTTIMIZZAZIONE QUI:
    stats['threes'] = threat_map.bit_count()

    # --- ANALISI COPPIE (Rigorosa) ---
    for shift in [7, 6, 8, 1]:
        # 1. Coppie consecutive (XX)
        pairs = my_pieces & (my_pieces >> shift)

        # Rileviamo gli spazi liberi intorno alla coppia
        e1_left = (empty << shift)
        e2_left = (empty << (shift * 2))
        e1_right = (empty >> (shift * 2))
        e2_right = (empty >> (shift * 3))

        # Una coppia è 'viva' se ha almeno due spazi liberi coerenti:
        # Caso XX_ _
        v1 = pairs & e1_right & e2_right
        # Caso _ _ XX
        v2 = pairs & e1_left & e2_left
        # Caso _ XX _
        v3 = pairs & e1_left & e1_right

        # 2. Coppie con buco (X _ X)
        # Deve avere un buco in mezzo e almeno uno spazio ai lati: _ X _ X o X _ X _
        split_pairs = my_pieces & (my_pieces >> (shift * 2))
        gap_empty = (empty >> shift)

        # Caso _ X _ X
        v4 = split_pairs & gap_empty & (empty << shift)
        # Caso X _ X _
        v5 = split_pairs & gap_empty & (empty >> (shift * 3))

        # Sommiamo tutti i bit validi trovati
        combined_twos = v1 | v2 | v3 | v4 | v5
        # OTTIMIZZAZIONE QUI:
        stats['twos'] += combined_twos.bit_count()

    return stats