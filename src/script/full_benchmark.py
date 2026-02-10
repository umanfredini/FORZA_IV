import sys
import os
import time

# Aggiunge la root del progetto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.script.training_monitor import run_training_session


def print_table(results):
    """
    Stampa una tabella formattata con le percentuali individuali.
    """
    # Larghezza totale della tabella aumentata per ospitare la colonna %
    W_NAME = 20
    W_STAT = 10
    W_PERC = 10
    total_width = W_NAME + (W_STAT * 3) + W_PERC + 13  # 13 per i separatori

    print("\n" + "=" * total_width)
    # Header con la nuova colonna % WIN
    print(
        f"{'AVVERSARIO':<{W_NAME}} | {'VITTORIE':<{W_STAT}} | {'SCONFITTE':<{W_STAT}} | {'PAREGGI':<{W_STAT}} | {'% WIN':<{W_PERC}}")
    print("-" * total_width)

    total_games = 0
    total_wins = 0
    total_losses = 0
    total_draws = 0

    for bot_name, w, l, d in results:
        games = w + l + d
        # Calcolo percentuale individuale
        win_rate = (w / games * 100) if games > 0 else 0.0

        # Stampa riga
        print(f"{bot_name:<{W_NAME}} | {w:<{W_STAT}} | {l:<{W_STAT}} | {d:<{W_STAT}} | {win_rate:<{W_PERC - 1}.1f}%")

        # Aggiornamento totali
        total_games += games
        total_wins += w
        total_losses += l
        total_draws += d

    print("-" * total_width)

    # Calcolo percentuale globale
    global_rate = (total_wins / total_games * 100) if total_games > 0 else 0.0

    print(
        f"{'TOTALE COMPLESSIVO':<{W_NAME}} | {total_wins:<{W_STAT}} | {total_losses:<{W_STAT}} | {total_draws:<{W_STAT}} | {global_rate:<{W_PERC - 1}.1f}%")
    print("=" * total_width + "\n")


def run_full_benchmark(games_per_opponent=100):
    start_time = time.time()
    results = []  # Lista per salvare le tuple (nome, win, loss, draw)

    print("=" * 60)
    print(f"🚀 INIZIO BENCHMARK COMPLETO ({games_per_opponent} partite per avversario)")
    print("=" * 60)

    # 1. Contro il Novizio
    print("\n--- FASE 1: CASUAL NOVICE (Depth 2) ---")
    # Nota: Assicurati che run_training_session in training_monitor.py restituisca (w, l, d)
    w, l, d = run_training_session("casual", iterations=games_per_opponent, silent=True)
    results.append(("Casual Novice", w, l, d))

    # 2. Contro Edge Runner
    print("\n--- FASE 2: EDGE RUNNER (Depth 4) ---")
    w, l, d = run_training_session("edge", iterations=games_per_opponent, silent=True)
    results.append(("Edge Runner", w, l, d))

    # 3. Contro Diagonal Blinder
    print("\n--- FASE 3: DIAGONAL BLINDER (Depth 4) ---")
    w, l, d = run_training_session("diagonal", iterations=games_per_opponent, silent=True)
    results.append(("Diagonal Blinder", w, l, d))

    elapsed = time.time() - start_time

    # Stampa tabella finale
    print("\n✅ BENCHMARK COMPLETATO!")
    print(f"Tempo trascorso: {elapsed / 60:.2f} minuti.")

    print_table(results)


if __name__ == "__main__":
    # Eseguiamo 100 partite per bot (aumenta a 1000 per dati più precisi)
    run_full_benchmark(games_per_opponent=50)