import pygame


class GameView:
    def __init__(self, screen):
        self.screen = screen
        self.WIDTH, self.HEIGHT = screen.get_size()

        # --- PALETTE CYBERPUNK ---
        self.C_BG = (10, 12, 18)  # Background scuro
        self.C_BOARD = (20, 30, 200)  # Blu Elettrico
        self.C_BORDER = (50, 150, 255)  # Bordo tech

        # Pedine (con effetto glow)
        self.C_P1 = (255, 40, 40)  # Rosso
        self.C_P1_GLOW = (150, 0, 0)
        self.C_P2 = (255, 200, 0)  # Giallo
        self.C_P2_GLOW = (100, 80, 0)

        # UI & Profiler
        self.C_TEXT_MAIN = (200, 220, 255)
        self.C_TEXT_DIM = (100, 120, 140)  # Grigio per etichette

        # Barre Profiler
        self.C_DIAG = (0, 255, 255)
        self.C_VERT = (0, 255, 128)
        self.C_HORIZ = (255, 165, 0)
        self.C_THREAT = (255, 0, 128)

        # --- SETUP GEOMETRIA ---
        self.margin = 30

        # 1. Scacchiera (Sinistra)
        self.board_rows = 6
        self.board_cols = 7

        avail_h = self.HEIGHT - (self.margin * 2) - 80
        self.sq_size = int(avail_h / self.board_rows)

        self.board_w = self.board_cols * self.sq_size
        self.board_h = self.board_rows * self.sq_size

        self.board_x = self.margin
        self.board_y = self.HEIGHT - self.board_h - self.margin

        self.board_rect = pygame.Rect(self.board_x, self.board_y, self.board_w, self.board_h)

        # Parametri per main.py
        self.slot_start_x = self.board_x
        self.cell_size = self.sq_size

        # 2. Generazione Texture "Bucata"
        self.board_surface = self._generate_board_texture()

        # 3. Profiler (Destra)
        prof_x = self.board_x + self.board_w + self.margin
        prof_w = self.WIDTH - prof_x - self.margin
        self.prof_rect = pygame.Rect(prof_x, self.board_y, prof_w, self.board_h - 80)

        # 4. Header (Scoreboard) - In alto
        self.head_rect = pygame.Rect(self.margin, 20, self.WIDTH - (self.margin * 2), 70)

        # 5. Tasto Reset (Basso a destra)
        btn_w, btn_h = 160, 50
        self.reset_rect = pygame.Rect(
            self.WIDTH - self.margin - btn_w,
            self.HEIGHT - self.margin - btn_h,
            btn_w,
            btn_h
        )

        # Font
        self.f_sml = pygame.font.SysFont("consolas", 14)
        self.f_med = pygame.font.SysFont("consolas", 20, bold=True)
        self.f_big = pygame.font.SysFont("consolas", 32, bold=True)

    def _generate_board_texture(self):
        s = pygame.Surface((self.board_w, self.board_h), pygame.SRCALPHA)
        s.fill(self.C_BOARD)
        radius = int(self.sq_size * 0.42)
        for c in range(self.board_cols):
            for r in range(self.board_rows):
                cx = c * self.sq_size + self.sq_size // 2
                cy = r * self.sq_size + self.sq_size // 2
                pygame.draw.circle(s, (0, 0, 0, 0), (cx, cy), radius)
        return s

    def draw(self, board_matrix, stats, profiler=None):
        self.screen.fill(self.C_BG)

        # --- 1. DISEGNO PEDINE (Dietro la scacchiera) ---
        for r in range(6):
            for c in range(7):
                piece = board_matrix[r][c]
                if piece != 0:
                    cx = self.board_x + c * self.sq_size + self.sq_size // 2
                    cy = self.board_y + r * self.sq_size + self.sq_size // 2

                    radius = int(self.sq_size * 0.40)

                    color = self.C_P1 if piece == 1 else self.C_P2
                    glow = self.C_P1_GLOW if piece == 1 else self.C_P2_GLOW

                    # Glow esterno
                    pygame.draw.circle(self.screen, glow, (cx, cy), radius + 4)
                    # Corpo solido
                    pygame.draw.circle(self.screen, color, (cx, cy), radius)
                    # (RIMOSSO RIFLESSO BIANCO)

        # --- 2. DISEGNO SCACCHIERA ---
        self.screen.blit(self.board_surface, (self.board_x, self.board_y))
        pygame.draw.rect(self.screen, self.C_BORDER, self.board_rect, 3, border_radius=10)

        # --- 3. HEADER / SCOREBOARD (REFURBISHED) ---
        self._draw_panel(self.head_rect)

        center_x = self.head_rect.centerx

        # --- PLAYER 1 (Sinistra) ---
        # Definiamo un punto centrale per l'area P1
        p1_center = self.head_rect.left + 100
        # Nome P1
        self._draw_text_aligned("PLAYER 1", (p1_center, self.head_rect.centery - 12), self.C_P1, self.f_med, "center")
        # Wins
        self._draw_text_aligned(f"WINS: {stats['wins_p1']}", (p1_center, self.head_rect.centery + 12), self.C_TEXT_DIM,
                                self.f_sml, "center")

        # --- PLAYER 2 / BOT (Destra) ---
        # Definiamo un punto centrale per l'area P2
        p2_center = self.head_rect.right - 100
        # Nome P2
        self._draw_text_aligned("OPPONENT", (p2_center, self.head_rect.centery - 12), self.C_P2, self.f_med, "center")
        # Wins
        self._draw_text_aligned(f"WINS: {stats['wins_p2']}", (p2_center, self.head_rect.centery + 12), self.C_TEXT_DIM,
                                self.f_sml, "center")

        # --- BARRA EVAL (TUG OF WAR) ---

        self._draw_eval_bar(center_x, self.head_rect.top + 40, stats.get('ai_eval', 0))

        # --- 4. TASTO RESET ---
        pygame.draw.rect(self.screen, (30, 45, 60), self.reset_rect, border_radius=8)
        pygame.draw.rect(self.screen, self.C_DIAG, self.reset_rect, 2, border_radius=8)

        rst_txt = self.f_med.render("RESET GAME", True, self.C_DIAG)
        self.screen.blit(rst_txt, (self.reset_rect.centerx - rst_txt.get_width() // 2,
                                   self.reset_rect.centery - rst_txt.get_height() // 2))

        # --- 5. PROFILER ---
        self._draw_panel(self.prof_rect)

        title = self.f_med.render("NEURAL PROFILER", True, self.C_DIAG)
        self.screen.blit(title, (self.prof_rect.centerx - title.get_width() // 2, self.prof_rect.top + 20))

        if profiler:
            biases = profiler.get_adaptive_weights()
            start_y = self.prof_rect.top + 80
            gap = 60

            self._draw_prof_bar("DIAGONAL", start_y, biases.get('diagonal_weakness', 1.0), self.C_DIAG)
            self._draw_prof_bar("VERTICAL", start_y + gap, biases.get('vertical_weakness', 1.0), self.C_VERT)
            self._draw_prof_bar("HORIZONTAL", start_y + gap * 2, biases.get('horizontal_weakness', 1.0), self.C_HORIZ)
            self._draw_prof_bar("BLINDNESS", start_y + gap * 3, biases.get('threat_underestimation', 1.0),
                                self.C_THREAT)

            err_box_y = self.prof_rect.bottom - 80
            self._draw_text_aligned("FATAL ERRORS", (self.prof_rect.left + 20, err_box_y), self.C_THREAT, self.f_sml,
                                    "topleft")
            err_val = self.f_big.render(str(profiler.stats.get("fatal_errors", 0)), True, self.C_P1)
            self.screen.blit(err_val, (self.prof_rect.left + 20, err_box_y + 20))

    def _draw_panel(self, rect):
        s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        s.fill((30, 35, 45, 200))
        self.screen.blit(s, (rect.x, rect.y))
        pygame.draw.rect(self.screen, self.C_BORDER, rect, 2, border_radius=10)

    def _draw_text_aligned(self, text, pos, color, font, align="topleft"):
        s = font.render(text, True, color)
        rect = s.get_rect()

        if align == "center":
            rect.center = pos
        elif align == "midleft":
            rect.midleft = pos
        elif align == "midright":
            rect.midright = pos
        elif align == "topleft":
            rect.topleft = pos

        self.screen.blit(s, rect)

    def _draw_eval_bar(self, cx, cy, val):
        # Disegna una barra "Tiro alla fune"
        total_w = 300
        h = 10
        start_x = cx - total_w // 2

        # Limita i valori tra -2000 e 2000
        clamped_val = max(-2000.0, min(2000.0, float(val)))

        # Calcola la percentuale di Rosso (P1).
        # A 0 (equilibrio) è 0.5. A +2000 è 1.0. A -2000 è 0.0.
        red_ratio = (clamped_val + 2000) / 4000.0

        red_w = int(total_w * red_ratio)
        yel_w = total_w - red_w

        # Disegna parte Rossa (Sinistra)
        pygame.draw.rect(self.screen, self.C_P1, (start_x, cy, red_w, h), border_top_left_radius=5,
                         border_bottom_left_radius=5)
        # Disegna parte Gialla (Destra)
        pygame.draw.rect(self.screen, self.C_P2, (start_x + red_w, cy, yel_w, h), border_top_right_radius=5,
                         border_bottom_right_radius=5)

        # Linea centrale (Equilibrio)
        pygame.draw.line(self.screen, (0, 0, 0), (cx, cy), (cx, cy + h), 2)

        # Valore numerico (Intero)
        val_int = int(val)
        self._draw_text_aligned(f"{val_int:+d}", (cx, cy - 15), (200, 200, 200), self.f_sml, "center")

    def _draw_prof_bar(self, label, y, val, color):
        self._draw_text_aligned(label, (self.prof_rect.left + 20, y), (200, 200, 200), self.f_sml, "topleft")
        self._draw_text_aligned(f"{val:.2f}", (self.prof_rect.right - 50, y), color, self.f_sml, "topleft")

        bar_rect = pygame.Rect(self.prof_rect.left + 20, y + 20, self.prof_rect.width - 40, 6)
        pygame.draw.rect(self.screen, (40, 40, 50), bar_rect, border_radius=3)

        pct = (min(4.0, max(1.0, val)) - 1.0) / 3.0
        fill_w = int(bar_rect.width * pct)
        if fill_w > 0:
            pygame.draw.rect(self.screen, color, (bar_rect.x, bar_rect.y, fill_w, 6), border_radius=3)

    def draw_game_over_modal(self, winner_text):
        s = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 200))
        self.screen.blit(s, (0, 0))

        center_x, center_y = self.WIDTH // 2, self.HEIGHT // 2
        box_w, box_h = 400, 250
        box_rect = pygame.Rect(center_x - box_w // 2, center_y - box_h // 2, box_w, box_h)
        self._draw_panel(box_rect)

        t = self.f_big.render(winner_text, True, self.C_P1)
        self.screen.blit(t, (center_x - t.get_width() // 2, box_rect.top + 50))

        btn_retry = pygame.Rect(center_x - 100, box_rect.bottom - 110, 200, 40)
        btn_menu = pygame.Rect(center_x - 100, box_rect.bottom - 60, 200, 40)

        pygame.draw.rect(self.screen, self.C_DIAG, btn_retry, border_radius=5)
        pygame.draw.rect(self.screen, (80, 80, 90), btn_menu, border_radius=5)

        t1 = self.f_med.render("RIVINCITA", True, (0, 0, 0))
        self.screen.blit(t1, (btn_retry.centerx - t1.get_width() // 2, btn_retry.centery - t1.get_height() // 2))

        t2 = self.f_med.render("MENU", True, (255, 255, 255))
        self.screen.blit(t2, (btn_menu.centerx - t2.get_width() // 2, btn_menu.centery - t2.get_height() // 2))

        return btn_retry, btn_menu