import pygame


class GameView:
    """
    * Gestisce il rendering grafico avanzato e l'interfaccia utente (UI).
    * Si occupa di disegnare la griglia, le pedine e le statistiche di gioco.
    """

    def __init__(self, screen):
        """
        * Inizializza la vista, calcolando le dimensioni dinamiche e definendo la palette colori.
        *
        * @param screen La superficie Pygame principale su cui disegnare.
        """
        self.screen = screen
        self.width = screen.get_width()

        # Riserviamo i primi 100px in alto per le statistiche
        self.ui_height = 100

        # Calcolo dinamico della dimensione delle celle
        self.sq_size = int(self.width / 7)
        self.radius = int(self.sq_size / 2 - 8)

        # --- Palette Colori Modern ---
        self.COLOR_BG = (30, 30, 30)  # Sfondo UI
        self.COLOR_BOARD = (25, 60, 150)  # Blu scacchiera
        self.COLOR_EMPTY = (15, 15, 15)  # Colore "vuoto" (nero)
        self.COLOR_P1 = (220, 50, 50)  # Rosso (Giocatore 1)
        self.COLOR_P2 = (240, 200, 40)  # Giallo (Giocatore 2 / Bot)
        self.COLOR_TEXT = (255, 255, 255)  # Testo bianco

        # --- Font ---
        self.font_main = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.font_score = pygame.font.SysFont("monospace", 20)
        # Ho aggiunto questo font che mancava nella tua definizione ma veniva usato in draw
        self.font_moves = pygame.font.SysFont("monospace", 18)

    def draw(self, board_matrix, stats):
        """
        * Disegna l'intero stato di gioco: interfaccia utente in alto e scacchiera in basso.
        *
        * @param board_matrix La matrice NumPy (o lista di liste) che rappresenta la griglia 6x7.
        * @param stats Dizionario contenente le statistiche (es. {'wins_p1': 0, 'moves_p1': 0, ...}).
        """
        self.screen.fill(self.COLOR_BG)

        # --- DISEGNO UI (Stats) ---

        # Sezione Giocatore 1 (Sinistra)
        p1_title = self.font_score.render(f"P1 RED", True, self.COLOR_P1)
        p1_stats = self.font_moves.render(f"Wins: {stats['wins_p1']} | Moves: {stats['moves_p1']}", True,
                                          self.COLOR_TEXT)
        self.screen.blit(p1_title, (20, 20))
        self.screen.blit(p1_stats, (20, 50))

        # Sezione Giocatore 2 (Destra)
        p2_title = self.font_score.render(f"P2 YELLOW", True, self.COLOR_P2)
        p2_stats = self.font_moves.render(f"Wins: {stats['wins_p2']} | Moves: {stats['moves_p2']}", True,
                                          self.COLOR_TEXT)

        # Calcolo allineamento a destra
        self.screen.blit(p2_title, (self.screen.get_width() - p2_title.get_width() - 20, 20))
        self.screen.blit(p2_stats, (self.screen.get_width() - p2_stats.get_width() - 20, 50))

        # --- DISEGNO SCACCHIERA ---
        for c in range(7):
            for r in range(6):
                # Calcolo posizione rettangolo (cella)
                rect_x, rect_y = c * self.sq_size, r * self.sq_size + self.ui_height

                # Disegna il quadrato blu
                pygame.draw.rect(self.screen, self.COLOR_BOARD, (rect_x, rect_y, self.sq_size, self.sq_size))

                # Determina il colore della pedina
                cell = board_matrix[r][c]
                color = self.COLOR_EMPTY  # Default vuoto
                if cell == 1:
                    color = self.COLOR_P1
                elif cell == 2:
                    color = self.COLOR_P2

                # Disegna il cerchio (pedina o foro vuoto)
                pygame.draw.circle(self.screen, color, (rect_x + self.sq_size // 2, rect_y + self.sq_size // 2),
                                   self.radius)

        pygame.display.update()