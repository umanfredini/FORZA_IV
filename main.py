import pygame
import sys
from board.engine import GameEngine
from board.interface import GameView
from board.controller import GameController


def main():
    pygame.init()
    screen = pygame.display.set_mode((700, 700))
    pygame.display.set_caption("Connect4 Bitboard Adaptive")

    engine = GameEngine()
    view = GameView(screen)
    controller = GameController(engine, view)

    game_over = False

    # Primo disegno
    view.draw(engine.get_board_matrix(), controller.turn)

    while not game_over:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                col, state, win, player = controller.process_turn(event.pos[0])

                if col is not None:
                    # [PROFILING] Qui in futuro salveremo: state -> col
                    print(f"Stato Bitboard: {state} | Colonna: {col}")

                    view.draw(engine.get_board_matrix(), controller.turn)

                    if win:
                        print(f"Giocatore {player + 1} vince!")
                        game_over = True
                        pygame.time.wait(3000)


if __name__ == "__main__":
    main()