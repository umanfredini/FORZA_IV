import pygame

# Definiamo gli stati qui per poterli importare nel main
STATE_MAIN_MENU = 0
STATE_GAME = 1
STATE_BOT_SELECT = 2


class MenuManager:
    """
    * Gestisce tutte le schermate del menu (Principale e Selezione Bot).
    """

    def __init__(self, screen):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()

        # Font Inizializzati qui per pulizia
        self.font_title = pygame.font.SysFont("Arial", 40, bold=True)
        self.font_option = pygame.font.SysFont("Arial", 28)
        self.font_desc = pygame.font.SysFont("Arial", 18, italic=True)

        # Colori
        self.COLOR_BG = (30, 30, 40)
        self.COLOR_TITLE = (255, 255, 255)
        self.COLOR_TEXT = (200, 200, 200)
        self.COLOR_ACCENT = (255, 255, 0)  # Giallo per highlight
        self.COLOR_BIAS = (255, 100, 100)  # Rosso per il bot cattivo

    def draw_main_menu(self):
        """
        * Disegna la schermata iniziale.
        """
        self.screen.fill(self.COLOR_BG)

        title = self.font_title.render("FORZA 4 - AI CHALLENGE", True, self.COLOR_TITLE)
        opt1 = self.font_option.render("1. Giocatore vs Giocatore (PvP)", True, self.COLOR_TEXT)
        opt2 = self.font_option.render("2. Giocatore vs Bot (PvE)", True, self.COLOR_TEXT)

        # Centratura
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 100))
        self.screen.blit(opt1, (self.width // 2 - opt1.get_width() // 2, 300))
        self.screen.blit(opt2, (self.width // 2 - opt2.get_width() // 2, 400))

        # Footer
        footer = self.font_desc.render("Premi 1 o 2 per selezionare", True, (100, 100, 100))
        self.screen.blit(footer, (self.width // 2 - footer.get_width() // 2, 650))

        pygame.display.update()

    def draw_bot_selection(self):
        """
        * Disegna la schermata di scelta dell'avversario AI.
        """
        self.screen.fill((40, 40, 50))  # Sfondo leggermente più chiaro

        title = self.font_title.render("SCEGLI IL TUO AVVERSARIO", True, self.COLOR_ACCENT)

        # Opzione 1
        opt1 = self.font_option.render("1. Bot Standard", True, self.COLOR_TITLE)
        desc1 = self.font_desc.render("(Equilibrato, gioca per vincere)", True, self.COLOR_TEXT)

        # Opzione 2
        opt2 = self.font_option.render("2. Il Cieco Diagonale", True, self.COLOR_BIAS)
        desc2 = self.font_desc.render("(Forte in attacco, ma ignora le minacce diagonali)", True, self.COLOR_TEXT)

        center_x = self.width // 2

        self.screen.blit(title, (center_x - title.get_width() // 2, 80))

        # Blocco 1
        self.screen.blit(opt1, (center_x - opt1.get_width() // 2, 250))
        self.screen.blit(desc1, (center_x - desc1.get_width() // 2, 285))

        # Blocco 2
        self.screen.blit(opt2, (center_x - opt2.get_width() // 2, 400))
        self.screen.blit(desc2, (center_x - desc2.get_width() // 2, 435))

        pygame.display.update()