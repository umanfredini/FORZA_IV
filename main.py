import pygame
import sys
from board.engine import GameEngine
from board.interface import GameView
from board.controller import GameController
# Importiamo il nuovo gestore menu e le costanti
from board.menu import MenuManager, STATE_MAIN_MENU, STATE_GAME, STATE_BOT_SELECT

# --- IMPORTS AI ---
from ai.minmax import MinimaxBot
from ai.diagonal_blind import DiagonalDefensiveFlawBot


def main():
    pygame.init()
    screen = pygame.display.set_mode((700, 700))
    pygame.display.set_caption("Forza 4 - AI & PvP")

    # Inizializzazione Componenti MVC
    engine = GameEngine()
    view = GameView(screen)
    controller = GameController(engine, view)

    # Inizializzazione Gestore Menu
    menu = MenuManager(screen)

    # Stato Iniziale
    bot = None
    app_state = STATE_MAIN_MENU
    game_mode = "PVP"

    while True:
        # -----------------------------------------------------------------
        # 1. MENU PRINCIPALE
        # -----------------------------------------------------------------
        if app_state == STATE_MAIN_MENU:
            menu.draw_main_menu()  # Chiamata pulita alla classe Menu

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        # PvP
                        game_mode = "PVP"
                        controller.reset_for_new_round()
                        app_state = STATE_GAME

                    elif event.key == pygame.K_2:
                        # PvE -> Vai a selezione bot
                        game_mode = "PVE"
                        app_state = STATE_BOT_SELECT

        # -----------------------------------------------------------------
        # 2. SELEZIONE BOT
        # -----------------------------------------------------------------
        elif app_state == STATE_BOT_SELECT:
            menu.draw_bot_selection()  # Chiamata pulita alla classe Menu

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit();
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        print("Scelto: Bot Standard")
                        bot = MinimaxBot(depth=4)
                        controller.reset_for_new_round()
                        app_state = STATE_GAME

                    elif event.key == pygame.K_2:
                        print("Scelto: Bot Cieco Diagonale")
                        bot = DiagonalDefensiveFlawBot(depth=4)
                        controller.reset_for_new_round()
                        app_state = STATE_GAME

                    elif event.key == pygame.K_ESCAPE:
                        app_state = STATE_MAIN_MENU

        # -----------------------------------------------------------------
        # 3. GIOCO
        # -----------------------------------------------------------------
        elif app_state == STATE_GAME:

            # --- TURNO BOT ---
            if game_mode == "PVE" and controller.turn == 1 and not controller.game_over:
                pygame.time.wait(500)

                col, score = bot.get_best_move(engine)
                controller.stats["ai_eval"] = score

                if col is not None:
                    simulated_x = col * view.sq_size + 10
                    win, player = controller.process_turn(simulated_x)
                    view.draw(engine.get_board_matrix(), controller.stats)
                    if win:
                        print(f"Il Bot ha vinto!")
                        pygame.time.wait(2000)
                        app_state = STATE_MAIN_MENU

            # --- INPUT UMANO ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        app_state = STATE_MAIN_MENU

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if game_mode == "PVE" and controller.turn == 1:
                            continue

                        win, player = controller.process_turn(event.pos[0])

                        if game_mode == "PVE" and not win and bot:
                            controller.stats["ai_eval"] = bot.get_evaluation(engine)

                        view.draw(engine.get_board_matrix(), controller.stats)

                        if win:
                            winner_name = "Giocatore 1" if player == 0 else (
                                "Giocatore 2" if game_mode == "PVP" else "Bot")
                            print(f"{winner_name} ha vinto!")
                            pygame.time.wait(3000)
                            app_state = STATE_MAIN_MENU

            view.draw(engine.get_board_matrix(), controller.stats)
            pygame.display.update()


if __name__ == "__main__":
    main()