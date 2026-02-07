import sys
import os
import time

# Aggiunge la root del progetto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.script.training_monitor import run_training_session


def run_full_benchmark(games_per_opponent=100):
    start_time = time.time()

    print("=" * 60)
    print(f"🚀 INIZIO BENCHMARK COMPLETO ({games_per_opponent} partite per avversario)")
    print("=" * 60)

    # 1. Contro il Novizio (Depth 2) - Test di Dominio
    # Ci aspettiamo 95-100% Win Rate. Bias bassi o misti.
    print("\n--- FASE 1: CASUAL NOVICE ---")
    run_training_session(opponent_type="casual", iterations=games_per_opponent)

    # 2. Contro Edge Runner (Depth 4) - Test Posizionale
    # Ci aspettiamo > 80% Win Rate. Bias 'center_weight' dovrebbe salire.
    print("\n--- FASE 2: EDGE RUNNER ---")
    run_training_session(opponent_type="edge", iterations=games_per_opponent)

    # 3. Contro Diagonal Blinder (Depth 4) - Test Tattico/Adattivo
    # Ci aspettiamo > 55% Win Rate. Bias 'diagonal' deve esplodere, 'hori' basso.
    print("\n--- FASE 3: DIAGONAL BLINDER ---")
    run_training_session(opponent_type="diagonal", iterations=games_per_opponent)

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"✅ BENCHMARK COMPLETATO in {elapsed / 60:.2f} minuti.")
    print("Controlla il file 'src/db/connect4_factory.db' per i dati storici.")
    print("=" * 60)


if __name__ == "__main__":
    # Puoi cambiare il numero qui se vuoi fare test più brevi o più lunghi
    run_full_benchmark(games_per_opponent=100)