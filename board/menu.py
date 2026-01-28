import pygame

# Definiamo gli stati qui per poterli importare nel main
STATE_MAIN_MENU = 0
STATE_GAME = 1
STATE_BOT_SELECT = 2
STATE_GAME_OVER = 3


class MenuManager:
    """
    * Gestisce tutte le schermate del menu (Principale e Selezione Bot).
    * Aggiornata per supportare 4 varianti di AI.
    """

    def __init__(self, screen):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()

        # --- Font ---
        self.font_title = pygame.font.SysFont("Arial", 40, bold=True)
        self.font_option = pygame.font.SysFont("Arial", 26)  # Ridotto leggermente per farci stare tutto
        self.font_desc = pygame.font.SysFont("Arial", 16, italic=True)

        # --- Colori Modern Dark ---
        self.COLOR_BG = (30, 30, 40)
        self.COLOR_TITLE = (255, 255, 255)
        self.COLOR_TEXT = (200, 200, 200)
        self.COLOR_ACCENT = (255, 255, 0)  # Giallo standard

        # Colori specifici per i Bot
        self.COLOR_NOVICE = (100, 255, 100)  # Verde (Facile)
        self.COLOR_BIAS = (255, 100, 100)  # Rosso (Bias/Difettoso)
        self.COLOR_EDGE = (255, 165, 0)  # Arancione (Strategia strana)
        self.COLOR_ADAPTIVE = (0, 255, 255)  # Ciano (High Tech/Adaptive)

    def draw_main_menu(self):
        """
        * Disegna la schermata iniziale (PvP vs PvE).
        """
        self.screen.fill(self.COLOR_BG)

        title = self.font_title.render("FORZA 4 - AI ADATTIVA", True, self.COLOR_TITLE)
        opt1 = self.font_option.render("1. Giocatore vs Giocatore (PvP)", True, self.COLOR_TEXT)
        opt2 = self.font_option.render("2. Giocatore vs Bot (PvE)", True, self.COLOR_TEXT)

        # Centratura
        center_x = self.width // 2
        self.screen.blit(title, (center_x - title.get_width() // 2, 100))
        self.screen.blit(opt1, (center_x - opt1.get_width() // 2, 300))
        self.screen.blit(opt2, (center_x - opt2.get_width() // 2, 400))

        # Footer
        footer = self.font_desc.render("Premi 1 o 2 per selezionare", True, (100, 100, 100))
        self.screen.blit(footer, (center_x - footer.get_width() // 2, 650))

        pygame.display.update()

    def draw_bot_selection(self):
        """
        * Disegna la schermata di scelta dell'avversario AI.
        * Supporta 4 opzioni come da Main.py.
        """
        self.screen.fill((40, 40, 50))

        title = self.font_title.render("CONFIGURAZIONE AVVERSARIO", True, self.COLOR_ACCENT)
        center_x = self.width // 2

        # Titolo
        self.screen.blit(title, (center_x - title.get_width() // 2, 40))

        # --- PARAMETRI DI LAYOUT ---
        start_y = 120
        gap_y = 100  # Distanza tra le opzioni

        # ---------------------------------------------------------
        # OPZIONE 1: NOVIZIO (Casual)
        # ---------------------------------------------------------
        opt1 = self.font_option.render("1. Il Novizio (Casual)", True, self.COLOR_NOVICE)
        desc1 = self.font_desc.render("(Simula errori umani, Depth 2)", True, self.COLOR_TEXT)

        self.screen.blit(opt1, (center_x - opt1.get_width() // 2, start_y))
        self.screen.blit(desc1, (center_x - desc1.get_width() // 2, start_y + 30))

        # ---------------------------------------------------------
        # OPZIONE 2: CIECO DIAGONALE (Training)
        # ---------------------------------------------------------
        opt2 = self.font_option.render("2. Il Cieco Diagonale (Bias)", True, self.COLOR_BIAS)
        desc2 = self.font_desc.render("(Forte in attacco, ignora le diagonali, Depth 4)", True, self.COLOR_TEXT)

        self.screen.blit(opt2, (center_x - opt2.get_width() // 2, start_y + gap_y))
        self.screen.blit(desc2, (center_x - desc2.get_width() // 2, start_y + gap_y + 30))

        # ---------------------------------------------------------
        # OPZIONE 3: BORDISTA (Training)
        # ---------------------------------------------------------
        opt3 = self.font_option.render("3. Il Bordista (Edge Runner)", True, self.COLOR_EDGE)
        desc3 = self.font_desc.render("(Evita il centro, gioca sui lati, Depth 3)", True, self.COLOR_TEXT)

        self.screen.blit(opt3, (center_x - opt3.get_width() // 2, start_y + gap_y * 2))
        self.screen.blit(desc3, (center_x - desc3.get_width() // 2, start_y + gap_y * 2 + 30))

        # ---------------------------------------------------------
        # OPZIONE 4: IA ADATTIVA (Real AI)
        # ---------------------------------------------------------
        opt4 = self.font_option.render("4. IA ADATTIVA (Profiler)", True, self.COLOR_ADAPTIVE)
        desc4 = self.font_desc.render("(Analizza il tuo stile e si adatta! Depth 4)", True, self.COLOR_TEXT)

        self.screen.blit(opt4, (center_x - opt4.get_width() // 2, start_y + gap_y * 3))
        self.screen.blit(desc4, (center_x - desc4.get_width() // 2, start_y + gap_y * 3 + 30))

        # ---------------------------------------------------------
        # FOOTER
        # ---------------------------------------------------------
        footer = self.font_desc.render("Premi 1, 2, 3 o 4 (ESC per tornare)", True, (150, 150, 150))
        self.screen.blit(footer, (center_x - footer.get_width() // 2, 650))

        pygame.display.update()