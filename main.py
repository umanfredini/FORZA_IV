import pygame
import sys

# --- MODULI CORE (MVC) ---
from board.engine import GameEngine
from board.interface import GameView
from board.controller import GameController
from board.menu import MenuManager, STATE_MAIN_MENU, STATE_GAME, STATE_BOT_SELECT

# --- MODULI INTELLIGENZA ARTIFICIALE (Nuova Architettura) ---
from ai.minmax import MinimaxAgent
from ai.evaluator import AdaptiveEvaluator
from ai.bots.training_evaluators import CasualEvaluator, DiagonalBlinderEvaluator, EdgeRunnerEvaluator


def main():
    pygame.init()
    # Setup finestra
    WIDTH, HEIGHT = 700, 700
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Forza 4 - AI Adattiva (Bitboard Engine)")

    # Inizializzazione MVC
    # Nota: Il Controller ora contiene il Profiler che persiste tra le partite!
    engine = GameEngine()
    view = GameView(screen)
    controller = GameController(engine, view)
    menu = MenuManager(screen)

    # Variabili di Stato
    bot = None
    app_state = STATE_MAIN_MENU
    game_mode = "PVP"  # "PVP" o "PVE"

    clock = pygame.time.Clock()

    while True:
        # Limitiamo gli FPS per non fondere la CPU
        clock.tick(60)

        # -----------------------------------------------------------------
        # 1. MENU PRINCIPALE
        # -----------------------------------------------------------------
        if app_state == STATE_MAIN_MENU:
            menu.draw_main_menu()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit();
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:  # PvP
                        game_mode = "PVP"
                        controller.reset_for_new_round()
                        app_state = STATE_GAME

                    elif event.key == pygame.K_2:  # PvE
                        game_mode = "PVE"
                        app_state = STATE_BOT_SELECT

        # -----------------------------------------------------------------
        # 2. SELEZIONE BOT (Configurazione Avversario)
        # -----------------------------------------------------------------
        elif app_state == STATE_BOT_SELECT:
            menu.draw_bot_selection()

            # Setup del bot in base alla scelta
            selected_bot = None

            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()

                if event.type == pygame.KEYDOWN:

                    # TASTO 1: NOVIZIO (Depth 2, Standard)
                    if event.key == pygame.K_1:
                        print("[SYSTEM] Bot Scelto: Novizio (Casual)")
                        selected_bot = MinimaxAgent(engine, CasualEvaluator(), depth=2)

                    # TASTO 2: CIECO DIAGONALE (Depth 4, Bias Diagonale)
                    elif event.key == pygame.K_2:
                        print("[SYSTEM] Bot Scelto: Cieco Diagonale (Training)")
                        selected_bot = MinimaxAgent(engine, DiagonalBlinderEvaluator(), depth=4)

                    # TASTO 3: BORDISTA (Depth 3, Odia il Centro)
                    elif event.key == pygame.K_3:
                        print("[SYSTEM] Bot Scelto: Bordista (Training)")
                        selected_bot = MinimaxAgent(engine, EdgeRunnerEvaluator(), depth=3)

                    # TASTO 4 (Opzionale): IA ADATTIVA REALE (Usa il Profiler!)
                    elif event.key == pygame.K_4:
                        print("[SYSTEM] Bot Scelto: IA ADATTIVA (Profiler Attivo)")
                        # Colleghiamo il Profiler del Controller all'Evaluator del Bot
                        adaptive_eval = AdaptiveEvaluator(controller.profiler)
                        selected_bot = MinimaxAgent(engine, adaptive_eval, depth=4)


                    elif event.key == pygame.K_ESCAPE:
                        app_state = STATE_MAIN_MENU

            # Se è stato scelto un bot, avviamo il gioco
            if selected_bot:
                bot = selected_bot
                controller.reset_for_new_round()
                app_state = STATE_GAME

        # -----------------------------------------------------------------
        # 3. GIOCO (Game Loop)
        # -----------------------------------------------------------------
        elif app_state == STATE_GAME:

            # Disegniamo la scacchiera (Engine -> View)
            # Passiamo controller.stats per visualizzare debug/punteggi se implementato
            view.draw(engine.get_board_matrix(), controller.stats)

            # --- TURNO DEL BOT ---
            # Il Bot gioca se è PvE, è il turno del Giallo (1) e il gioco non è finito
            if game_mode == "PVE" and controller.turn == 1 and not controller.game_over:
                pygame.display.update()  # Forza aggiornamento schermo prima che il bot pensi
                pygame.time.wait(500)  # Piccola pausa per realismo

                # 1. Il Bot pensa (Minimax)
                col = bot.choose_move(1)  # 1 = Player Index del Bot

                # 2. Calcoliamo lo score solo per le statistiche (opzionale)
                eval_score = bot.evaluator.evaluate(engine, 1)
                controller.stats["ai_eval"] = eval_score
                print(f"[BOT] Scelgo colonna {col + 1} (Valutazione: {eval_score})")

                # 3. Eseguiamo la mossa convertendo colonna -> pixel
                if col is not None:
                    # Simuliamo un click al centro della colonna scelta
                    simulated_x = int(col * view.sq_size + (view.sq_size / 2))
                    win, player = controller.process_turn(simulated_x)

                    if win:
                        print(f"--- IL BOT HA VINTO! ---")
                        view.draw(engine.get_board_matrix(), controller.stats)
                        pygame.display.update()
                        pygame.time.wait(3000)
                        app_state = STATE_MAIN_MENU

            # --- INPUT UMANO ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit();
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        app_state = STATE_MAIN_MENU

                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Blocchiamo l'input umano se tocca al bot
                    if game_mode == "PVE" and controller.turn == 1:
                        continue

                    if event.button == 1:  # Click Sinistro
                        # Il controller gestisce logica, engine, profiler e cambio turno
                        win, player = controller.process_turn(event.pos[0])

                        # Aggiorniamo le statistiche "in diretta"
                        if game_mode == "PVE" and bot:
                            # Mostriamo come il bot valuta la situazione attuale
                            current_eval = bot.evaluator.evaluate(engine, 1)
                            controller.stats["ai_eval"] = current_eval

                        if win:
                            winner = "Giocatore 1" if player == 0 else "Giocatore 2/Bot"
                            print(f"--- {winner} HA VINTO! ---")
                            # Disegna ultimo frame
                            view.draw(engine.get_board_matrix(), controller.stats)
                            pygame.display.update()
                            pygame.time.wait(3000)
                            app_state = STATE_MAIN_MENU

            pygame.display.update()


if __name__ == "__main__":
    main()