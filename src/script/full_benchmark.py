import sys
import os
import time

# Aggiunge la root del progetto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.script.training_monitor import run_training_session
from src.db.persistence import GamePersistence


def print_table(results, title="📊 RISULTATI"):
    """ Stampa una tabella formattata con l'aggiunta delle mosse medie. """
    W_NAME, W_STAT, W_PERC, W_AVG = 20, 10, 10, 12
    total_width = W_NAME + (W_STAT * 3) + W_PERC + W_AVG + 16

    print(f"\n{title}")
    print("=" * total_width)
    print(
        f"{'AVVERSARIO':<{W_NAME}} | {'VITTORIE':<{W_STAT}} | {'SCONFITTE':<{W_STAT}} | {'PAREGGI':<{W_STAT}} | {'% WIN':<{W_PERC}} | {'AVG MOVES':<{W_AVG}}"
    )
    print("-" * total_width)

    t_games, t_w, t_l, t_d = 0, 0, 0, 0
    t_moves_weighted_sum = 0.0

    for name, w, l, d, avg_m in results:
        games = w + l + d
        win_rate = (w / games * 100) if games > 0 else 0.0

        print(
            f"{name:<{W_NAME}} | {w:<{W_STAT}} | {l:<{W_STAT}} | {d:<{W_STAT}} | {win_rate:<{W_PERC - 1}.1f}% | {avg_m:<{W_AVG}.1f}")

        t_games += games
        t_w += w
        t_l += l
        t_d += d
        t_moves_weighted_sum += (avg_m * games)

    print("-" * total_width)

    global_rate = (t_w / t_games * 100) if t_games > 0 else 0.0
    global_avg_moves = (t_moves_weighted_sum / t_games) if t_games > 0 else 0.0

    print(
        f"{'TOTALE COMPLESSIVO':<{W_NAME}} | {t_w:<{W_STAT}} | {t_l:<{W_STAT}} | {t_d:<{W_STAT}} | {global_rate:<{W_PERC - 1}.1f}% | {global_avg_moves:<{W_AVG}.1f}"
    )
    print("=" * total_width + "\n")


def run_full_benchmark(games_per_opponent=500):
    db = GamePersistence()
    start_time = time.time()
    session_results = []

    bots = [("casual", "Casual Novice"), ("edge", "Edge Runner"), ("diagonal", "Diagonal Blinder")]

    print("=" * 60)
    print(f"🚀 INIZIO BENCHMARK COMPLETO ({games_per_opponent} match/bot)")
    print("=" * 60)

    for tag, name in bots:
        print(f"\n--- TEST ATTUALE CONTRO {name.upper()} ---")

        # 1. Eseguiamo la sessione (ritorna 3 valori)
        w, l, d = run_training_session(tag, iterations=games_per_opponent, silent=True)

        # 2. Recuperiamo la media mosse aggiornata dal DB tramite il metodo esistente
        stats = db.get_stats_for_docs(tag)
        avg_m = stats["avg_moves"] if stats else 0.0

        session_results.append((name, w, l, d, avg_m))

    # --- CALCOLO STORICO (LIFETIME) ---
    total_lifetime = []
    for tag, name in bots:
        hw, hl, hd = db.get_total_stats_by_bot(tag)
        stats = db.get_stats_for_docs(tag)
        havg = stats["avg_moves"] if stats else 0.0

        total_lifetime.append((name, hw, hl, hd, havg))

    elapsed = time.time() - start_time
    print(f"\n✅ BENCHMARK COMPLETATO IN {elapsed / 60:.2f} MINUTI.")

    print_table(session_results, title="📈 PERFORMANCE SESSIONE ATTUALE")
    print_table(total_lifetime, title="🏛️ STATISTICHE TOTALI (LIFETIME)")


if __name__ == "__main__":
    run_full_benchmark(games_per_opponent=2000)