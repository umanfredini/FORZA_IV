import pygame
import sys

# --- MODULI CORE (MVC) ---
from board.engine import GameEngine
from board.interface import GameView
from board.controller import GameController
# AGGIUNTO STATE_GAME_OVER all'import
from board.menu import MenuManager, STATE_MAIN_MENU, STATE_GAME, STATE_BOT_SELECT, STATE_GAME_OVER

# --- MODULI INTELLIGENZA ARTIFICIALE ---
from ai.minmax import MinimaxAgent
from ai.evaluator import AdaptiveEvaluator
from ai.bots.training_evaluators import CasualEvaluator, DiagonalBlinderEvaluator, EdgeRunnerEvaluator


def main():
    pygame.init()
    WIDTH, HEIGHT = 700, 700
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Forza 4 - AI Adattiva")

    engine = GameEngine()
    view = GameView(screen)
    controller = GameController(engine, view)
    menu = MenuManager(screen)

    bot = None
    app_state = STATE_MAIN_MENU
    game_mode = "PVP"

    # Variabili per gestire il Game Over
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
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        selected_bot = MinimaxAgent(engine, CasualEvaluator(), depth=2)
                    elif event.key == pygame.K_2:
                        selected_bot = MinimaxAgent(engine, DiagonalBlinderEvaluator(), depth=4)
                    elif event.key == pygame.K_3:
                        selected_bot = MinimaxAgent(engine, EdgeRunnerEvaluator(), depth=3)
                    elif event.key == pygame.K_4:
                        adaptive_eval = AdaptiveEvaluator(controller.profiler)
                        selected_bot = MinimaxAgent(engine, adaptive_eval, depth=4)
                    elif event.key == pygame.K_ESCAPE:
                        app_state = STATE_MAIN_MENU

            if selected_bot:
                bot = selected_bot
                controller.reset_for_new_round()
                app_state = STATE_GAME

        # -----------------------------------------------------------------
        # 3. GIOCO (Game Loop)
        # -----------------------------------------------------------------
        elif app_state == STATE_GAME:
            view.draw(engine.get_board_matrix(), controller.stats)

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
                        # NON RESETTIAMO PIÙ SUBITO, CAMBIAMO STATO
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
                        win, player = controller.process_turn(event.pos[0])

                        if game_mode == "PVE" and bot:
                            controller.stats["ai_eval"] = bot.evaluator.evaluate(engine, 1)

                        if win:
                            w_name = "GIOCATORE 1" if player == 0 else "GIOCATORE 2"
                            print(f"--- {w_name} HA VINTO! ---")
                            # NON RESETTIAMO PIÙ SUBITO, CAMBIAMO STATO
                            winner_text = f"{w_name} VINCE!"
                            app_state = STATE_GAME_OVER

            pygame.display.update()

        # -----------------------------------------------------------------
        # 4. GAME OVER (Modal)
        # -----------------------------------------------------------------
        elif app_state == STATE_GAME_OVER:
            # 1. Disegna la scacchiera sotto (così si vede la mossa finale)
            # Nota: non serve ridisegnarla ogni frame se non cambia, ma per semplicità lo facciamo
            view.draw(engine.get_board_matrix(), controller.stats)

            # 2. Disegna il Modal sopra e ottieni i rect dei bottoni
            btn_retry_rect, btn_menu_rect = view.draw_game_over_modal(winner_text)

            # 3. Gestione Click sui Bottoni
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = event.pos

                    # Tasto RIGIOCA
                    if btn_retry_rect.collidepoint(mouse_pos):
                        controller.reset_for_new_round()
                        app_state = STATE_GAME  # Torna a giocare

                    # Tasto MENU
                    elif btn_menu_rect.collidepoint(mouse_pos):
                        app_state = STATE_MAIN_MENU  # Torna al menu principale


if __name__ == "__main__":
    main()