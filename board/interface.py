import pygame

class GameView:
    """
    * Rendering grafico della scacchiera.
    """
    def __init__(self, screen):
        self.screen = screen
        self.sq_size = 100
        self.width = 7 * self.sq_size
        self.height = 7 * self.sq_size
        self.radius = int(self.sq_size / 2 - 5)

    def draw(self, board_matrix, turn):
        """
        * Disegna lo stato attuale.
        """
        self.screen.fill((0, 0, 0))
        for c in range(7):
            for r in range(6):
                pygame.draw.rect(self.screen, (0, 0, 255), (c*self.sq_size, (r+1)*self.sq_size, self.sq_size, self.sq_size))
                color = (0, 0, 0)
                if board_matrix[r][c] == 1: color = (255, 0, 0)
                elif board_matrix[r][c] == 2: color = (255, 255, 0)
                # Invertiamo il disegno per la gravità
                pygame.draw.circle(self.screen, color, (int(c*self.sq_size + self.sq_size/2), self.height - int(r*self.sq_size + self.sq_size/2)), self.radius)
        pygame.display.update()