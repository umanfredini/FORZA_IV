import sys
import os
import time

# Aggiunge la root del progetto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.script.training_monitor import run_training_session
from src.db.persistence import GamePersistence # Usiamo la tua classe


def print_table(results, title="📊 RISULTATI"):
    """ Stampa una tabella formattata. """
    W_NAME, W_STAT, W_PERC = 20, 10, 10
    total_width = W_NAME + (W_STAT * 3) + W_PERC + 13

    print(f"\n{title}")
    print("=" * total_width)
    print(
        f"{'AVVERSARIO':<{W_NAME}} | {'VITTORIE':<{W_STAT}} | {'SCONFITTE':<{W_STAT}} | {'PAREGGI':<{W_STAT}} | {'% WIN':<{W_PERC}}")
    print("-" * total_width)

    t_games, t_w, t_l, t_d = 0, 0, 0, 0
    for name, w, l, d in results:
        games = w + l + d
        win_rate = (w / games * 100) if games > 0 else 0.0
        print(f"{name:<{W_NAME}} | {w:<{W_STAT}} | {l:<{W_STAT}} | {d:<{W_STAT}} | {win_rate:<{W_PERC - 1}.1f}%")
        t_games, t_w, t_l, t_d = t_games + games, t_w + w, t_l + l, t_d + d

    print("-" * total_width)
    global_rate = (t_w / t_games * 100) if t_games > 0 else 0.0
    print(
        f"{'TOTALE COMPLESSIVO':<{W_NAME}} | {t_w:<{W_STAT}} | {t_l:<{W_STAT}} | {t_d:<{W_STAT}} | {global_rate:<{W_PERC - 1}.1f}%")
    print("=" * total_width + "\n")


def run_full_benchmark(games_per_opponent=500):
    db = GamePersistence()
    start_time = time.time()
    session_results = []

    # Mappa tag -> nome visualizzato
    bots = [("casual", "Casual Novice"), ("edge", "Edge Runner"), ("diagonal", "Diagonal Blinder")]

    print("=" * 60)
    print(f"🚀 INIZIO BENCHMARK COMPLETO ({games_per_opponent} match/bot)")
    print("=" * 60)

    for tag, name in bots:
        print(f"\n--- TEST ATTUALE CONTRO {name.upper()} ---")
        # run_training_session deve restituire (win, loss, draw)
        w, l, d = run_training_session(tag, iterations=games_per_opponent, silent=True)
        session_results.append((name, w, l, d))

    # --- CALCOLO STORICO ---
    total_lifetime = []
    for tag, name in bots:
        # Recupera dati dal DB (escludendo la sessione appena fatta se non ancora salvata,
        # o includendola se run_training_session salva internamente)
        hw, hl, hd = db.get_total_stats_by_bot(tag)

        # Se run_training_session SALVA GIÀ nel db, hw, hl, hd contengono già i risultati attuali.
        # Altrimenti, decommenta le righe sotto per sommarli manualmente:
        # sw, sl, sd = next(item[1:] for item in session_results if item[0] == name)
        # total_lifetime.append((name, hw + sw, hl + sl, hd + sd))

        total_lifetime.append((name, hw, hl, hd))

    elapsed = time.time() - start_time
    print(f"\n✅ BENCHMARK COMPLETATO IN {elapsed / 60:.2f} MINUTI.")

    # Visualizzazione sdoppiata
    print_table(session_results, title="📈 PERFORMANCE SESSIONE ATTUALE")
    print_table(total_lifetime, title="🏛️ STATISTICHE TOTALI (LIFETIME)")


if __name__ == "__main__":
    run_full_benchmark(games_per_opponent=1000)