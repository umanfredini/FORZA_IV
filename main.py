import pygame
import sys

# --- MODULI CORE (MVC) ---
from board.engine import GameEngine
from board.interface import GameView
from board.controller import GameController
from board.menu import MenuManager, STATE_MAIN_MENU, STATE_GAME, STATE_BOT_SELECT, STATE_GAME_OVER

# --- MODULI INTELLIGENZA ARTIFICIALE ---
from ai.minmax import MinimaxAgent
from ai.evaluator import AdaptiveEvaluator
from ai.bots.training_evaluators import CasualEvaluator, DiagonalBlinderEvaluator, EdgeRunnerEvaluator
from db.persistence import GamePersistence  # Import per caricare memoria


def main():
    pygame.init()
    # WIDTH AUMENTATA A 1000 PER SIDEBAR
    WIDTH, HEIGHT = 1000, 700
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Forza 4 - AI Adattiva")

    engine = GameEngine()
    view = GameView(screen)
    controller = GameController(engine, view)
    menu = MenuManager(screen)
    persistence = GamePersistence()

    bot = None
    app_state = STATE_MAIN_MENU
    game_mode = "PVP"

    winner_text = ""
    btn_retry_rect = None
    btn_menu_rect = None

    clock = pygame.time.Clock()

    while True:
        clock.tick(60)

        # -----------------------------------------------------------------
        # 1. MENU PRINCIPALE
        # -----------------------------------------------------------------
        if app_state == STATE_MAIN_MENU:
            menu.draw_main_menu()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        game_mode = "PVP"
                        controller.reset_for_new_round()
                        app_state = STATE_GAME
                    elif event.key == pygame.K_2:
                        game_mode = "PVE"
                        app_state = STATE_BOT_SELECT

        # -----------------------------------------------------------------
        # 2. SELEZIONE BOT
        # -----------------------------------------------------------------
        elif app_state == STATE_BOT_SELECT:
            menu.draw_bot_selection()
            selected_bot = None
            bot_db_name = None  # Nome per caricare bias dal DB

            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        selected_bot = MinimaxAgent(engine, CasualEvaluator(), depth=2)
                        bot_db_name = "casual_novice"
                    elif event.key == pygame.K_2:
                        selected_bot = MinimaxAgent(engine, DiagonalBlinderEvaluator(), depth=4)
                        bot_db_name = "diagonal_blinder"
                    elif event.key == pygame.K_3:
                        selected_bot = MinimaxAgent(engine, EdgeRunnerEvaluator(), depth=3)
                        bot_db_name = "edge_runner"
                    elif event.key == pygame.K_4:
                        # IA ADATTIVA: Qui il profiler impara LIVE dall'umano
                        adaptive_eval = AdaptiveEvaluator(controller.profiler)
                        selected_bot = MinimaxAgent(engine, adaptive_eval, depth=4)
                        bot_db_name = "human_player"
                    elif event.key == pygame.K_ESCAPE:
                        app_state = STATE_MAIN_MENU

            if selected_bot:
                bot = selected_bot

                # CARICAMENTO MEMORIA PERSISTENTE
                # Se giochiamo contro un bot di training, carichiamo i suoi bias nel Profiler
                # così la sidebar mostrerà le sue debolezze note.
                if bot_db_name:
                    latest_biases = persistence.get_latest_biases(bot_db_name)
                    if latest_biases:
                        print(f"[SYSTEM] Caricati bias per {bot_db_name}: {latest_biases}")
                        controller.profiler.biases = latest_biases
                    else:
                        # Reset profiler se non ci sono dati
                        controller.profiler.__init__()

                controller.reset_for_new_round()
                app_state = STATE_GAME

        # -----------------------------------------------------------------
        # 3. GIOCO (Game Loop)
        # -----------------------------------------------------------------
        elif app_state == STATE_GAME:
            # PASSIAMO IL PROFILER ALLA VIEW PER DISEGNARE LA SIDEBAR
            view.draw(engine.get_board_matrix(), controller.stats, profiler=controller.profiler)

            # --- TURNO BOT ---
            if game_mode == "PVE" and controller.turn == 1 and not controller.game_over:
                pygame.display.update()
                pygame.time.wait(500)

                col = bot.choose_move(1)
                controller.stats["ai_eval"] = bot.evaluator.evaluate(engine, 1)

                if col is not None:
                    simulated_x = int(col * view.sq_size + (view.sq_size / 2))
                    win, player = controller.process_turn(simulated_x)

                    if win:
                        print(f"--- IL BOT HA VINTO! ---")
                        winner_text = "IL BOT VINCE!"
                        app_state = STATE_GAME_OVER

            # --- INPUT UMANO ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    app_state = STATE_MAIN_MENU

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if game_mode == "PVE" and controller.turn == 1: continue
                    if event.button == 1:
                        # Verifica click solo nella zona scacchiera
                        if event.pos[0] < view.board_width:
                            win, player = controller.process_turn(event.pos[0])

                            if game_mode == "PVE" and bot:
                                controller.stats["ai_eval"] = bot.evaluator.evaluate(engine, 1)

                            if win:
                                w_name = "GIOCATORE 1" if player == 0 else "GIOCATORE 2"
                                print(f"--- {w_name} HA VINTO! ---")
                                winner_text = f"{w_name} VINCE!"
                                app_state = STATE_GAME_OVER

            pygame.display.update()

        # -----------------------------------------------------------------
        # 4. GAME OVER (Modal)
        # -----------------------------------------------------------------
        elif app_state == STATE_GAME_OVER:
            view.draw(engine.get_board_matrix(), controller.stats, profiler=controller.profiler)
            btn_retry_rect, btn_menu_rect = view.draw_game_over_modal(winner_text)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = event.pos
                    if btn_retry_rect.collidepoint(mouse_pos):
                        controller.reset_for_new_round()
                        app_state = STATE_GAME
                    elif btn_menu_rect.collidepoint(mouse_pos):
                        app_state = STATE_MAIN_MENU


if __name__ == "__main__":
    main()