import sys
import os
import time
import math
import random
import pygame
from typing import List, Tuple, Dict, Optional, Any
from treys import Card
from poker_engine import PokerEngine, CardUtils, Player, PERSONALITY_CONFIG, RoundAnalyzer, HAND_RANKS_PT
from poker_ai import PokerAI
from menu_screen import MenuScreen
from card_design import AntiqueDeck
from game_view import GameView
from poker_highlights import HandHighlight, MatchTracker, HighlightDetector, CuriosityDetector

# ============================================================
# INITIALIZATION & DISPLAY SETUP
# ============================================================
pygame.init()
pygame.font.init()

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
FPS = 60

# ============================================================
# BALATRO / RETRO ARCADE CASINO PALETTE
# ============================================================
# Ambient / Room
COLOR_ROOM_BG = (10, 13, 22)             # Deep Midnight Navy
COLOR_FLOOR_TILE = (16, 20, 34)          # Parquet / Casino Carpet
COLOR_FLOOR_LINE = (24, 30, 48)

# Table Materials
COLOR_WOOD_RIM = (65, 32, 12)            # Dark Mahogany Wood
COLOR_WOOD_RIM_LIGHT = (110, 58, 24)     # Wood Bevel Highlight
COLOR_WOOD_RIM_DARK = (42, 20, 8)        # Wood Bevel Shadow
COLOR_BRASS = (212, 168, 56)             # Polished Brass Trim
COLOR_BRASS_LIGHT = (255, 224, 115)      # Brass Highlight
COLOR_BRASS_DARK = (140, 102, 28)        # Brass Shadow
COLOR_FELT = (10, 72, 48)                # Deep Casino Emerald Felt
COLOR_FELT_LIGHT = (18, 106, 70)         # Illuminated Center Felt
COLOR_FELT_DARK = (6, 48, 32)            # Edge Felt Vignette
COLOR_FELT_LINE = (212, 175, 55, 90)     # Golden Betting Oval Line

# Cards
COLOR_CARD_IVORY = (252, 250, 245)       # Physical Card Face
COLOR_CARD_BORDER = (195, 200, 210)
COLOR_CARD_BACK = (22, 28, 56)           # Deep Indigo Card Back
COLOR_CARD_BACK_INNER = (35, 42, 85)
COLOR_CARD_BACK_GOLD = (212, 168, 56)
COLOR_SUIT_RED = (225, 36, 48)           # Hearts & Diamonds
COLOR_SUIT_BLACK = (24, 28, 38)          # Spades & Clubs

# Chips (3D Denominations)
COLOR_CHIP_RED = (220, 40, 50)           # $5
COLOR_CHIP_GREEN = (34, 168, 86)         # $25
COLOR_CHIP_BLACK = (36, 40, 48)          # $100
COLOR_CHIP_PURPLE = (145, 55, 225)       # $500
COLOR_CHIP_GOLD = (245, 185, 30)         # $1000

# Text & Accents
COLOR_WHITE = (248, 250, 252)
COLOR_MUTED = (130, 142, 168)
COLOR_DARK_TEXT = (18, 22, 32)
COLOR_GOLD = (255, 215, 0)
COLOR_GOLD_BRIGHT = (255, 232, 90)
COLOR_ORANGE = (255, 130, 30)
COLOR_NEON_GREEN = (46, 213, 115)
COLOR_NEON_RED = (255, 65, 85)
COLOR_NEON_PURPLE = (185, 80, 255)
COLOR_NEON_CYAN = (45, 195, 255)

# ============================================================
# PLAYER THEMES (Football Legends / Roguelike Jokers)
# ============================================================
PLAYER_CONFIG = {
    0: {  # Player 0: North
        "key": "cr7",
        "name": "CR7",
        "full_name": "Cristiano Ronaldo",
        "archetype": "CALCULISTA",
        "engine_personality": "equilibrado",
        "theme_color": (45, 125, 255),       # Royal Electric Blue
        "theme_glow": (100, 175, 255),
        "theme_dark": (18, 48, 110),
        "number": "7",
        "emoji": "🧠",
        "quote": "\"A probabilidade não mente. Eu só preciso dos números certos.\"",
        "stats": {"Racional": 98, "Agressão": 55, "Blefe": 15},
        "pos": "north"
    },
    1: {  # Player 1: East
        "key": "vini",
        "name": "Mbappé",
        "full_name": "Kylian Mbappé",
        "archetype": "AGRESSIVO",
        "engine_personality": "agressivo",
        "theme_color": (250, 45, 70),        # Blazing Crimson
        "theme_glow": (255, 105, 125),
        "theme_dark": (115, 16, 28),
        "number": "7",
        "emoji": "🔥",
        "quote": "\"Pressão total o tempo todo! Quem hesita já perdeu na mesa.\"",
        "stats": {"Racional": 45, "Agressão": 95, "Blefe": 40},
        "pos": "east"
    },
    2: {  # Player 2: South (YOU)
        "key": "messi",
        "name": "Messi",
        "full_name": "Lionel Messi",
        "archetype": "DEFENSIVO",
        "engine_personality": "conservador",
        "theme_color": (0, 205, 125),        # Magic Emerald Green
        "theme_glow": (70, 245, 175),
        "theme_dark": (10, 85, 50),
        "number": "10",
        "emoji": "🛡️",
        "quote": "\"Paciência cirúrgica. Só coloco as fichas quando o lance é genial.\"",
        "stats": {"Racional": 85, "Agressão": 30, "Blefe": 20},
        "pos": "south"
    },
    3: {  # Player 3: West
        "key": "neymar",
        "name": "Neymar Jr.",
        "full_name": "Neymar Jr.",
        "archetype": "WILD CARD / BLEFE",
        "engine_personality": "blefador",
        "theme_color": (175, 65, 255),       # Wild Violet / Magenta
        "theme_glow": (215, 125, 255),
        "theme_dark": (75, 20, 115),
        "number": "10",
        "emoji": "🎭",
        "quote": "\"Ninguém na mesa sabe o que eu tenho na mão... nem eu mesmo!\"",
        "stats": {"Racional": 35, "Agressão": 85, "Blefe": 99},
        "pos": "west"
    }
}

# ============================================================
# TYPOGRAPHY
# ============================================================
FONT_HERO = pygame.font.SysFont("impact", 38)
FONT_POT = pygame.font.SysFont("impact", 34)
FONT_STREET = pygame.font.SysFont("impact", 20)
FONT_HEADER = pygame.font.SysFont("segoeui", 20, bold=True)
FONT_PLAYER_NAME = pygame.font.SysFont("segoeui", 17, bold=True)
FONT_PLAYER_STACK = pygame.font.SysFont("impact", 18)
FONT_TAG = pygame.font.SysFont("segoeui", 11, bold=True)
FONT_MAIN = pygame.font.SysFont("segoeui", 13)
FONT_BOLD = pygame.font.SysFont("segoeui", 13, bold=True)
FONT_SMALL = pygame.font.SysFont("segoeui", 11)
FONT_TINY = pygame.font.SysFont("segoeui", 10)
FONT_CARD_RANK = pygame.font.SysFont("impact", 22)
FONT_CARD_SUIT = pygame.font.SysFont("segoeuisymbol", 20, bold=True)
FONT_CARD_CENTER = pygame.font.SysFont("segoeuisymbol", 34, bold=True)
FONT_MODAL_TITLE = pygame.font.SysFont("impact", 28)
FONT_ARCADE_BTN = pygame.font.SysFont("impact", 16)


# ============================================================
# HELPER FUNCTIONS: VISUALS, SHADOWS, GRADIENTS
# ============================================================
def create_drop_shadow(width: int, height: int, radius: int = 12, blur: int = 8, alpha: int = 100) -> pygame.Surface:
    """Creates a high-performance cached drop shadow surface."""
    surf = pygame.Surface((width + blur * 2, height + blur * 2), pygame.SRCALPHA)
    for i in range(blur, 0, -1):
        step_alpha = int(alpha * (1.0 - (i / blur) ** 0.8))
        rect = pygame.Rect(blur - i, blur - i, width + i * 2, height + i * 2)
        pygame.draw.rect(surf, (0, 0, 0, step_alpha), rect, border_radius=radius + i)
    return surf


def draw_glow_rect(surface: pygame.Surface, rect: pygame.Rect, color: Tuple[int, int, int], radius: int = 10, border_radius: int = 12, alpha: int = 120):
    """Draws a multi-layered neon glow around a rectangle."""
    glow_surf = pygame.Surface((rect.width + radius * 2, rect.height + radius * 2), pygame.SRCALPHA)
    for i in range(radius, 0, -2):
        step_a = int(alpha * (1.0 - i / radius) * 0.4)
        g_rect = pygame.Rect(radius - i, radius - i, rect.width + i * 2, rect.height + i * 2)
        pygame.draw.rect(glow_surf, (*color, step_a), g_rect, border_radius=border_radius + i)
    surface.blit(glow_surf, (rect.x - radius, rect.y - radius))


def lerp_color(c1: Tuple[int, int, int], c2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def pulse(speed: float = 4.0, low: float = 0.0, high: float = 1.0) -> float:
    t = (math.sin(time.time() * speed) + 1.0) / 2.0
    return low + t * (high - low)


# ============================================================
# PRE-RENDERED CHIP SPRITES & CHIP STACK RENDERER
# ============================================================
class ChipRenderer:
    _chip_cache: Dict[Tuple[int, int], pygame.Surface] = {}

    @classmethod
    def get_chip(cls, color: Tuple[int, int, int], diameter: int = 24) -> pygame.Surface:
        key = (color, diameter)
        if key in cls._chip_cache:
            return cls._chip_cache[key]

        surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        cx, cy = diameter // 2, diameter // 2
        r = diameter // 2 - 1

        # Drop shadow
        pygame.draw.circle(surf, (0, 0, 0, 90), (cx, cy + 2), r)
        # Main base
        pygame.draw.circle(surf, color, (cx, cy), r)
        # Outer rim highlight
        pygame.draw.circle(surf, (255, 255, 255, 70), (cx, cy), r, width=1)
        # Dashed edge stripes (6 notches like casino chips)
        for angle_deg in range(0, 360, 60):
            rad = math.radians(angle_deg)
            nx = cx + int(math.cos(rad) * (r - 2))
            ny = cy + int(math.sin(rad) * (r - 2))
            pygame.draw.circle(surf, (255, 255, 255, 200), (nx, ny), 2)
        # Inner ring
        inner_r = max(4, r - 5)
        pygame.draw.circle(surf, (255, 255, 255, 120), (cx, cy), inner_r, width=1)
        # Inner core
        pygame.draw.circle(surf, (color[0] // 2, color[1] // 2, color[2] // 2), (cx, cy), inner_r - 2)

        cls._chip_cache[key] = surf
        return surf

    @classmethod
    def draw_chip_stack(cls, surface: pygame.Surface, cx: int, cy: int, amount: int):
        """Draws realistic isometric stacked poker chips representing an amount."""
        if amount <= 0:
            return

        denominations = [
            (1000, COLOR_CHIP_GOLD),
            (500, COLOR_CHIP_PURPLE),
            (100, COLOR_CHIP_BLACK),
            (25, COLOR_CHIP_GREEN),
            (5, COLOR_CHIP_RED)
        ]
        chips_to_draw = []
        rem = amount
        for denom, col in denominations:
            count = rem // denom
            if count > 0:
                draw_count = min(count, 4)
                chips_to_draw.extend([col] * draw_count)
                rem %= denom
            if len(chips_to_draw) >= 8:
                break
        if not chips_to_draw:
            chips_to_draw = [COLOR_CHIP_RED]

        for idx, col in enumerate(chips_to_draw[:10]):
            chip_surf = cls.get_chip(col, diameter=26)
            y_offset = cy - (idx * 4)
            surface.blit(chip_surf, (cx - 13, y_offset - 13))


# ============================================================
# CARD RENDERER (Physical Playing Cards with Shadows & Textures)
# ============================================================
class CardRenderer:
    CARD_WIDTH = 68
    CARD_HEIGHT = 98
    _card_cache: Dict[str, pygame.Surface] = {}
    _shadow_cache: Optional[pygame.Surface] = None

    @classmethod
    def get_shadow(cls) -> pygame.Surface:
        if cls._shadow_cache is None:
            cls._shadow_cache = create_drop_shadow(cls.CARD_WIDTH, cls.CARD_HEIGHT, radius=8, blur=6, alpha=110)
        return cls._shadow_cache

    _design = None

    @classmethod
    def design(cls):
        if cls._design is None:
            cls._design = AntiqueDeck()
        return cls._design

    @classmethod
    def get_card_back(cls) -> pygame.Surface:
        if "BACK" not in cls._card_cache:
            cls._card_cache["BACK"] = pygame.transform.smoothscale(
                cls.design().back, (cls.CARD_WIDTH, cls.CARD_HEIGHT))
        return cls._card_cache["BACK"]

    @classmethod
    def get_card_front(cls, card_int: int) -> pygame.Surface:
        key = f"FRONT_{card_int}"
        if key not in cls._card_cache:
            rank, _, kind = CardUtils.card_rank_suit(card_int)
            cls._card_cache[key] = pygame.transform.smoothscale(
                cls.design().front(rank, kind), (cls.CARD_WIDTH, cls.CARD_HEIGHT))
        return cls._card_cache[key]

    @classmethod
    def draw_card(cls, surface: pygame.Surface, x: int, y: int, card_int: Optional[int],
                  face_down: bool = False, scale: float = 1.0, glow: bool = False,
                  glow_color: Tuple[int, int, int] = COLOR_GOLD, flip_anim: float = 1.0):
        w = int(cls.CARD_WIDTH * scale * abs(flip_anim))
        h = int(cls.CARD_HEIGHT * scale)
        if w <= 1:
            return

        cx = x + (cls.CARD_WIDTH * scale) / 2
        top_left_x = int(cx - w / 2)
        top_left_y = int(y)

        shadow = cls.get_shadow()
        if scale != 1.0 or abs(flip_anim) != 1.0:
            shadow = pygame.transform.smoothscale(shadow, (w + 12, h + 12))
        surface.blit(shadow, (top_left_x - 6, top_left_y - 3))

        show_front = (not face_down) and (card_int is not None) and (flip_anim >= 0)
        card_surf = cls.get_card_front(card_int) if show_front else cls.get_card_back()

        if scale != 1.0 or abs(flip_anim) != 1.0:
            card_surf = pygame.transform.smoothscale(card_surf, (w, h))

        if glow:
            glow_rect = pygame.Rect(top_left_x, top_left_y, w, h)
            draw_glow_rect(surface, glow_rect, glow_color, radius=8, border_radius=7, alpha=150)

        surface.blit(card_surf, (top_left_x, top_left_y))


# ============================================================
# FLYING CHIP ANIMATION SYSTEM
# ============================================================
class FlyingChip:
    def __init__(self, start_x: float, start_y: float, target_x: float, target_y: float, color: Tuple[int, int, int], delay: float = 0.0, speed: int = 1):
        self.start_x = start_x
        self.start_y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.color = color
        self.delay = delay / speed
        self.born = time.time()
        self.duration = 0.40 / speed
        self.active = False
        self.finished = False

    def update(self) -> bool:
        now = time.time()
        elapsed = now - self.born
        if elapsed < self.delay:
            return True
        t = (elapsed - self.delay) / self.duration
        if t >= 1.0:
            self.finished = True
            return False
        return True

    def get_pos(self) -> Tuple[int, int]:
        now = time.time()
        elapsed = now - self.born - self.delay
        t = max(0.0, min(1.0, elapsed / self.duration))
        ease_t = 1.0 - (1.0 - t) ** 3
        arc_offset = math.sin(t * math.pi) * -35.0
        cur_x = self.start_x + (self.target_x - self.start_x) * ease_t
        cur_y = self.start_y + (self.target_y - self.start_y) * ease_t + arc_offset
        return int(cur_x), int(cur_y)


# ============================================================
# FLOATING ACTION BADGE
# ============================================================
class FloatingBadge:
    def __init__(self, text: str, x: int, y: int, color: Tuple[int, int, int], speed: int = 1):
        self.text = text
        self.x = x
        self.y = y
        self.start_y = y
        self.color = color
        self.born = time.time()
        self.lifetime = 1.5 / speed

    def update(self) -> bool:
        return (time.time() - self.born) < self.lifetime

    def draw(self, surface: pygame.Surface):
        elapsed = time.time() - self.born
        progress = elapsed / self.lifetime
        alpha = max(0, int(255 * (1.0 - progress)))
        cur_y = self.start_y - progress * 40

        text_s = FONT_HEADER.render(self.text, True, self.color)
        tw, th = text_s.get_size()
        badge_rect = pygame.Rect(self.x - tw // 2 - 10, cur_y - th // 2 - 4, tw + 20, th + 8)

        b_surf = pygame.Surface((badge_rect.width, badge_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(b_surf, (15, 18, 30, min(230, alpha)), (0, 0, badge_rect.width, badge_rect.height), border_radius=8)
        pygame.draw.rect(b_surf, (*self.color, alpha), (0, 0, badge_rect.width, badge_rect.height), width=2, border_radius=8)
        surface.blit(b_surf, badge_rect.topleft)

        t_surf = pygame.Surface((tw, th), pygame.SRCALPHA)
        t_surf.blit(text_s, (0, 0))
        t_surf.set_alpha(alpha)
        surface.blit(t_surf, (self.x - tw // 2, cur_y - th // 2))


# ============================================================
# MAIN APPLICATION CLASS
# ============================================================
class PokerPygameApp:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("♠ TEXAS HOLD'EM AI — RETRO ARCADE POKER ROYALE ♠")
        self.clock = pygame.time.Clock()

        # Engine & Simulation
        self.engine = PokerEngine(initial_stack=1000, small_blind=10, big_blind=20)
        self.ai = PokerAI(simulations=800)

        # Match Tracker (Recordes e Melhores Momentos)
        self.tracker = MatchTracker()
        self.tracker.start_new_hand(self.engine.hand_count)

        # Application States: "MENU" or "GAME"
        self.state = "MENU"
        self.menu_screen = MenuScreen()
        self.game_view = GameView(CardRenderer)
        self.game_view.sync(self.engine)

        # Presentation & Playback Controls
        self.god_mode = True
        self.auto_play = False
        
        # Centralized Game Speed: 1x, 2x, 3x
        self.game_speed = 1
        self.last_action_time = time.time()

        # Alerts & Feedback
        self.all_in_alert = False
        self.all_in_player_name = ""
        self.screen_shake = 0.0
        self.screen_flash = 0.0
        self.flash_color = (255, 50, 50)

        # Animations
        self.flying_chips: List[FlyingChip] = []
        self.floating_badges: List[FloatingBadge] = []
        self.last_pot_value = 0
        self.pot_bounce = 0.0

        # Highlights & Modals
        self.last_highlight: Optional[HandHighlight] = None
        self.show_modal = False
        self.modal_rect = pygame.Rect(WINDOW_WIDTH // 2 - 430, WINDOW_HEIGHT // 2 - 275, 860, 550)

        # Match History Modal
        self.show_history_modal = False
        self.history_modal_rect = pygame.Rect(WINDOW_WIDTH // 2 - 440, WINDOW_HEIGHT // 2 - 275, 880, 550)

        # Player Station Screen Layout (X, Y anchor for 4 seats)
        # 0: North (CR7), 1: East (Vini), 2: South (Messi), 3: West (Neymar)
        self.seat_anchors = [
            (640, 115),   # North
            (1115, 380),  # East
            (640, 645),   # South
            (165, 380)    # West
        ]

        # Pre-render static table surface for 60 FPS performance
        self.cached_table = self._render_static_table()

        # Pre-load or generate player avatar surfaces
        self.avatar_cache = self._load_or_generate_avatars()

        # Interactive Button Rectangles (Balanced across bottom console)
        self.btn_sp_1x = pygame.Rect(20, 742, 46, 44)
        self.btn_sp_2x = pygame.Rect(72, 742, 46, 44)
        self.btn_sp_3x = pygame.Rect(124, 742, 46, 44)
        self.btn_god = pygame.Rect(180, 742, 135, 44)
        self.btn_next = pygame.Rect(325, 742, 235, 44)
        self.btn_auto = pygame.Rect(570, 742, 180, 44)
        self.btn_history = pygame.Rect(760, 742, 210, 44)
        self.btn_reset = pygame.Rect(980, 742, 130, 44)
        self.btn_menu = pygame.Rect(1120, 742, 135, 44)

        # Menu Start Button
        self.menu_start_btn = pygame.Rect(WINDOW_WIDTH // 2 - 180, 680, 360, 64)

        self.running = True

    # ============================================================
    # CENTRALIZED SPEED HELPER METHODS
    # ============================================================
    def set_game_speed(self, speed: int):
        """Sets the global game speed (1, 2, or 3) and displays immediate feedback."""
        old_speed = self.game_speed
        self.game_speed = max(1, min(3, speed))
        if self.game_speed != old_speed:
            self.floating_badges.append(FloatingBadge(
                f"⚡ VELOCIDADE: {self.game_speed}x",
                WINDOW_WIDTH // 2, 685, COLOR_GOLD_BRIGHT, speed=self.game_speed
            ))

    def get_scaled_delay(self, base_sec: float) -> float:
        """Returns time scaled by current game speed."""
        return base_sec / self.game_speed

    def get_animation_duration(self, base_sec: float) -> float:
        return base_sec / self.game_speed

    # =========================================================================
    # PRE-RENDER STATIC TABLE (Wood, Rail, Studs, Felt & Lighting)
    # =========================================================================
    def _render_static_table(self) -> pygame.Surface:
        table_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        table_surf.fill(COLOR_ROOM_BG)

        # 1. Subtle Retro Parquet / Carpet Tiles
        tile_size = 32
        for ty in range(0, WINDOW_HEIGHT, tile_size):
            for tx in range(0, WINDOW_WIDTH, tile_size):
                if (tx // tile_size + ty // tile_size) % 2 == 0:
                    pygame.draw.rect(table_surf, COLOR_FLOOR_TILE, (tx, ty, tile_size, tile_size))
                pygame.draw.rect(table_surf, COLOR_FLOOR_LINE, (tx, ty, tile_size, tile_size), width=1)

        # Center coordinates
        tcx, tcy = 640, 380

        # 2. Table Drop Shadow
        shadow_w, shadow_h = 1040, 560
        shadow_surf = pygame.Surface((shadow_w + 40, shadow_h + 40), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 130), (20, 20, shadow_w, shadow_h))
        table_surf.blit(shadow_surf, (tcx - shadow_w // 2 - 20, tcy - shadow_h // 2 - 10))

        # 3. Outer Wood Rail (Rich Mahogany)
        rail_w, rail_h = 1010, 530
        rail_rect = pygame.Rect(tcx - rail_w // 2, tcy - rail_h // 2, rail_w, rail_h)
        pygame.draw.ellipse(table_surf, COLOR_WOOD_RIM, rail_rect)
        pygame.draw.ellipse(table_surf, COLOR_WOOD_RIM_LIGHT, rail_rect, width=6)
        pygame.draw.ellipse(table_surf, COLOR_WOOD_RIM_DARK, rail_rect.inflate(-12, -12), width=4)

        # 4. Brass Rivets / Studs along the Wood Rim
        num_studs = 32
        for i in range(num_studs):
            angle = (2.0 * math.pi * i) / num_studs
            sx = tcx + int(math.cos(angle) * (rail_w // 2 - 7))
            sy = tcy + int(math.sin(angle) * (rail_h // 2 - 7))
            pygame.draw.circle(table_surf, COLOR_BRASS_DARK, (sx, sy + 1), 4)
            pygame.draw.circle(table_surf, COLOR_BRASS, (sx, sy), 3)
            pygame.draw.circle(table_surf, COLOR_BRASS_LIGHT, (sx - 1, sy - 1), 1)

        # 5. Inner Brass Bevel
        inner_brass_rect = rail_rect.inflate(-40, -40)
        pygame.draw.ellipse(table_surf, COLOR_BRASS, inner_brass_rect, width=3)

        # 6. Felt Surface (Deep Emerald Green)
        felt_rect = inner_brass_rect.inflate(-6, -6)
        pygame.draw.ellipse(table_surf, COLOR_FELT, felt_rect)

        # 7. Felt Radial Lighting Effect
        center_glow = pygame.Surface((felt_rect.width, felt_rect.height), pygame.SRCALPHA)
        for r_step in range(12, 0, -1):
            alpha = int(14 * (1.0 - r_step / 12.0))
            sub_rect = pygame.Rect(
                felt_rect.width // 2 - (felt_rect.width * r_step // 28),
                felt_rect.height // 2 - (felt_rect.height * r_step // 28),
                (felt_rect.width * r_step // 14),
                (felt_rect.height * r_step // 14)
            )
            pygame.draw.ellipse(center_glow, (*COLOR_FELT_LIGHT, alpha), sub_rect)
        table_surf.blit(center_glow, felt_rect.topleft)

        # 8. Golden Betting Line Oval
        bet_line_rect = felt_rect.inflate(-80, -70)
        pygame.draw.ellipse(table_surf, (212, 175, 55), bet_line_rect, width=2)

        # 9. Center Felt Watermark
        watermark = FONT_HERO.render("POKER ROYALE", True, (12, 85, 58))
        table_surf.blit(watermark, watermark.get_rect(center=(tcx, tcy - 50)))

        return table_surf

    # =========================================================================
    # AVATAR GENERATION / LOADING
    # =========================================================================
    def _load_or_generate_avatars(self) -> Dict[int, pygame.Surface]:
        avatars = {}
        for p_idx, p_data in PLAYER_CONFIG.items():
            key = p_data["key"]
            file_path = os.path.join("assets", "avatars", f"{key}.png")

            if os.path.exists(file_path):
                try:
                    raw = pygame.image.load(file_path).convert_alpha()
                    scaled = pygame.transform.smoothscale(raw, (60, 60))
                    mask = pygame.Surface((60, 60), pygame.SRCALPHA)
                    pygame.draw.circle(mask, (255, 255, 255, 255), (30, 30), 28)
                    scaled.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                    avatars[p_idx] = scaled
                    continue
                except Exception:
                    pass

            # Procedural High-Polish Avatar Fallback
            surf = pygame.Surface((60, 60), pygame.SRCALPHA)
            col = p_data["theme_color"]
            dark = p_data["theme_dark"]

            pygame.draw.circle(surf, dark, (30, 30), 28)
            pygame.draw.circle(surf, col, (30, 30), 25)
            pygame.draw.circle(surf, COLOR_BRASS, (30, 30), 28, width=2)

            num_surf = FONT_HERO.render(p_data["number"], True, COLOR_WHITE)
            surf.blit(num_surf, num_surf.get_rect(center=(30, 28)))

            star = FONT_TINY.render("★", True, COLOR_GOLD)
            surf.blit(star, star.get_rect(center=(30, 48)))

            avatars[p_idx] = surf

        return avatars

    # =========================================================================
    # CHIP SPAWNING (Tactile Juice)
    # =========================================================================
    def spawn_bet_chips(self, player_idx: int, amount: int):
        """Spawns animated chips flying from the player's seat to the pot."""
        px, py = self.seat_anchors[player_idx]
        pot_x, pot_y = 640, 260
        count = min(8, max(3, amount // 20))
        for i in range(count):
            delay = i * 0.04
            chip_col = random.choice([COLOR_CHIP_RED, COLOR_CHIP_GREEN, COLOR_CHIP_BLACK])
            self.flying_chips.append(FlyingChip(px, py, pot_x, pot_y, chip_col, delay=delay, speed=self.game_speed))

    def spawn_win_chips(self, player_idx: int):
        """Spawns animated chips flying from the center pot to the winning player."""
        pot_x, pot_y = 640, 260
        px, py = self.seat_anchors[player_idx]
        for i in range(12):
            delay = i * 0.03
            chip_col = random.choice([COLOR_CHIP_GOLD, COLOR_CHIP_PURPLE, COLOR_CHIP_BLACK])
            self.flying_chips.append(FlyingChip(pot_x, pot_y, px, py, chip_col, delay=delay, speed=self.game_speed))

    # =========================================================================
    # STEP EXECUTION (Advance Game Turn)
    # =========================================================================
    def execute_next_step(self):
        self.game_view.sync(self.engine)
        if self.game_view.busy:
            return
        if self.show_modal:
            self.show_modal = False
            self.engine.start_new_hand(reset_dealer=True)
            self.tracker.start_new_hand(self.engine.hand_count)
            self.last_highlight = None
            return

        if self.show_history_modal:
            self.show_history_modal = False
            return

        self.all_in_alert = False

        if self.engine.hand_ended:
            self.engine.start_new_hand(reset_dealer=True)
            self.tracker.start_new_hand(self.engine.hand_count)
            self.last_highlight = None
            return

        curr_idx = self.engine.current_player_idx
        curr_player = self.engine.players[curr_idx]
        pot_before = self.engine.pot

        active_opps = len([p for p in self.engine.get_active_players() if p.idx != curr_idx])
        cost_to_call = self.engine.get_to_call(curr_player)

        decision = self.ai.decide(
            player=curr_player,
            community_cards=self.engine.community_cards,
            cost_to_call=cost_to_call,
            current_pot=self.engine.pot,
            num_active_opponents=active_opps,
            big_blind=self.engine.big_blind
        )

        action = decision["action"]
        raise_amount = decision["raise_amount"]
        bet_amount = raise_amount if action == "raise" else (cost_to_call if action in ("call", "all-in") else 0)

        # Registra no Tracker
        self.tracker.record_action(
            stage=self.engine.stage,
            player_idx=curr_idx,
            player_name=curr_player.name,
            action=action,
            amount=bet_amount,
            is_bluff=decision.get("is_bluff", False),
            equity=decision.get("equity", 50.0)
        )

        # Apply to engine
        self.engine.player_action(curr_idx, action, raise_amount)
        self.game_view.queue_board(self.engine, curr_idx, self.game_speed)

        # Trigger flying chips & badges
        p_cfg = PLAYER_CONFIG[curr_idx]
        px, py = self.seat_anchors[curr_idx]

        if action == "raise":
            self.spawn_bet_chips(curr_idx, raise_amount)
            self.floating_badges.append(FloatingBadge(f"RAISE +${raise_amount}", px, py - 60, COLOR_ORANGE, speed=self.game_speed))
        elif action == "call":
            self.spawn_bet_chips(curr_idx, cost_to_call)
            self.floating_badges.append(FloatingBadge(f"CALL ${cost_to_call}", px, py - 60, COLOR_NEON_CYAN, speed=self.game_speed))
        elif action == "check":
            self.floating_badges.append(FloatingBadge("CHECK ✓", px, py - 60, COLOR_NEON_GREEN, speed=self.game_speed))
        elif action == "fold":
            self.floating_badges.append(FloatingBadge("FOLD ✕", px, py - 60, (140, 140, 150), speed=self.game_speed))
        elif action == "all-in":
            self.spawn_bet_chips(curr_idx, curr_player.stack)
            self.floating_badges.append(FloatingBadge("⚡ ALL-IN!", px, py - 70, COLOR_GOLD_BRIGHT, speed=self.game_speed))

        # Pot bounce animation
        if self.engine.pot > pot_before:
            self.pot_bounce = time.time()

        # ALL-IN dramatic trigger
        if curr_player.is_all_in or action == "all-in":
            self.all_in_alert = True
            self.all_in_player_name = p_cfg["name"]
            self.screen_shake = time.time()
            self.screen_flash = time.time()
            self.flash_color = (255, 45, 65)

        # Hand conclusion & showdown highlight analysis
        if self.engine.hand_ended:
            if self.engine.winners_info:
                winner_idx = self.engine.winners_info[0]["player"].idx
                self.spawn_win_chips(winner_idx)

            # Analisador Inteligente de Melhores Momentos
            highlight = HighlightDetector.analyze_round(self.engine, self.tracker)
            self.last_highlight = highlight

            # Registra no Histórico da Sessão
            winner_p = self.engine.winners_info[0]["player"]
            winner_score = 99999
            winner_class = self.engine.winners_info[0].get("hand_class", "")
            if len(self.engine.community_cards) >= 3:
                winner_score = self.engine.evaluator.evaluate(self.engine.community_cards, winner_p.hand)

            self.tracker.record_hand_end(
                highlight=highlight,
                pot=self.engine.pot,
                winner_name=winner_p.name,
                rank_score=winner_score,
                hand_class=winner_class,
                winner_cards=winner_p.hand
            )

            # Pausa para exibição do modal caso seja evento marcante
            self.auto_play = False
            if highlight.is_major_event:
                self.game_view.pending_highlight = True

    # =========================================================================
    # MAIN LOOP & EVENT HANDLING
    # =========================================================================
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        if self.state == "GAME":
            mouse_pos = self.game_coordinates(mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.WINDOWRESIZED:
                self.menu_screen.layout(self.screen.get_size())

            elif event.type == pygame.FINGERDOWN:
                width, height = self.screen.get_size()
                position = (event.x * width, event.y * height)
                if self.state == "MENU":
                    self.menu_screen.click(position, self)
                elif not self.show_modal and not self.show_history_modal:
                    self.game_view.click(self.game_coordinates(position))

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if getattr(event, "touch", False):
                    continue  # SDL also emits a synthetic mouse click after a touch.
                mouse_pos = event.pos if self.state == "MENU" else self.game_coordinates(event.pos)
                if self.state == "MENU":
                    self.menu_screen.click(mouse_pos, self)
                elif self.show_history_modal:
                    self.show_history_modal = False
                elif self.show_modal:
                    self.show_modal = False
                    self.engine.start_new_hand(reset_dealer=True)
                    self.tracker.start_new_hand(self.engine.hand_count)
                    self.last_highlight = None
                else:
                    # Interactive Console Buttons Click Handling
                    if self.btn_next.collidepoint(mouse_pos):
                        self.execute_next_step()
                    elif self.btn_auto.collidepoint(mouse_pos):
                        self.toggle_play()
                    elif self.btn_god.collidepoint(mouse_pos):
                        self.god_mode = not self.god_mode
                    elif self.btn_sp_1x.collidepoint(mouse_pos):
                        self.set_game_speed(1)
                    elif self.btn_sp_2x.collidepoint(mouse_pos):
                        self.set_game_speed(2)
                    elif self.btn_sp_3x.collidepoint(mouse_pos):
                        self.set_game_speed(3)
                    elif self.btn_history.collidepoint(mouse_pos):
                        self.show_history_modal = True
                    elif self.btn_reset.collidepoint(mouse_pos):
                        self.reset_match()
                        self.tracker = MatchTracker()
                        self.tracker.start_new_hand(1)
                        self.all_in_alert = False
                        self.show_modal = False
                        self.show_history_modal = False
                    elif self.btn_menu.collidepoint(mouse_pos):
                        self.state = "MENU"
                        self.auto_play = False
                    else:
                        self.game_view.click(mouse_pos)

            elif event.type == pygame.KEYDOWN:
                # Modais Fecham com ESC ou ESPAÇO
                if event.key == pygame.K_ESCAPE:
                    if self.state == "MENU" and (self.menu_screen.settings_open or self.menu_screen.info_open):
                        self.menu_screen.settings_open = False
                        self.menu_screen.info_open = False
                    elif self.show_history_modal:
                        self.show_history_modal = False
                    elif self.show_modal:
                        self.show_modal = False
                    elif self.state == "GAME":
                        self.state = "MENU"
                        self.auto_play = False
                    else:
                        self.running = False

                elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    if self.show_history_modal:
                        self.show_history_modal = False
                    elif self.state == "MENU":
                        if not self.menu_screen.settings_open and not self.menu_screen.info_open:
                            self.start_play()
                    else:
                        self.execute_next_step()

                # Speed Hotkeys: [1], [2], [3], [-], [+]
                elif event.key in (pygame.K_1, pygame.K_KP1):
                    self.set_game_speed(1)
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    self.set_game_speed(2)
                elif event.key in (pygame.K_3, pygame.K_KP3):
                    self.set_game_speed(3)
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    self.set_game_speed(self.game_speed - 1)
                elif event.key in (pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS):
                    self.set_game_speed(self.game_speed + 1)

                # Modal de Histórico de Recordes: [H]
                elif event.key == pygame.K_h:
                    if self.state == "GAME" and not self.show_modal:
                        self.show_history_modal = not self.show_history_modal

                # Modos de Apresentação
                elif event.key == pygame.K_d:
                    self.god_mode = not self.god_mode

                elif event.key == pygame.K_a:
                    if self.state == "GAME" and not self.show_modal:
                        self.toggle_play()

                elif event.key == pygame.K_r:
                    if self.state == "GAME":
                        self.reset_match()
                        self.tracker = MatchTracker()
                        self.tracker.start_new_hand(1)
                        self.all_in_alert = False
                        self.show_modal = False
                        self.show_history_modal = False

    def start_play(self):
        if self.engine.hand_ended:
            self.engine.start_new_hand(reset_dealer=True)
            self.tracker.start_new_hand(self.engine.hand_count)
            self.last_highlight = None
        self.game_view.sync(self.engine)
        self.show_modal = False
        self.show_history_modal = False
        self.state = "GAME"
        self.auto_play = True
        self.last_action_time = time.time()

    def toggle_play(self):
        if self.auto_play:
            self.auto_play = False
        else:
            self.start_play()

    def reset_match(self):
        self.engine = PokerEngine(initial_stack=1000)
        self.game_view.sync(self.engine)
        self.auto_play = False
        self.flying_chips.clear()
        self.floating_badges.clear()

    @staticmethod
    def card_label(card):
        return CardUtils.card_to_str(card)

    def update(self):
        self.game_view.update(self.clock.get_time() / 1000.0, self.engine)
        if self.state == "GAME" and not self.game_view.busy and self.game_view.pending_highlight:
            self.show_modal = True
            self.game_view.pending_highlight = False
        if self.state == "MENU":
            self.menu_screen.layout(self.screen.get_size())
            pointer = pygame.mouse.get_pos() if pygame.mouse.get_focused() else (-1, -1)
            self.menu_screen.update(self.clock.get_time() / 1000.0, pointer)
        # Update flying chips
        self.flying_chips = [c for c in self.flying_chips if c.update()]

        # Update floating badges
        self.floating_badges = [b for b in self.floating_badges if b.update()]

        # Auto-play tick scaled by game speed
        if self.state == "GAME" and self.auto_play and not self.game_view.busy and not self.show_modal and not self.show_history_modal:
            now = time.time()
            scaled_delay = self.get_scaled_delay(1.0)
            if now - self.last_action_time >= scaled_delay:
                if self.engine.hand_ended:
                    self.auto_play = False
                else:
                    self.execute_next_step()
                self.last_action_time = now

    # =========================================================================
    # RENDER ROUTING
    # =========================================================================
    def draw(self):
        shake_x, shake_y = 0, 0
        now = time.time()
        shake_duration = self.get_animation_duration(0.25)
        if now - self.screen_shake < shake_duration:
            intensity = (shake_duration - (now - self.screen_shake)) * 25.0
            shake_x = random.randint(-int(intensity), int(intensity))
            shake_y = random.randint(-int(intensity), int(intensity))

        render_surf = pygame.Surface(self.screen.get_size() if self.state == "MENU" else (WINDOW_WIDTH, WINDOW_HEIGHT))

        if self.state == "MENU":
            self.draw_menu(render_surf)
        else:
            self.draw_game(render_surf)

            # Hold V to peek at the table beneath modal
            keys = pygame.key.get_pressed()
            is_holding_v = keys[pygame.K_v]

            if self.show_modal and self.last_highlight and not is_holding_v:
                self.draw_modal_popup(render_surf)
            elif self.show_history_modal and not is_holding_v:
                self.draw_history_modal(render_surf)
            elif (self.show_modal or self.show_history_modal) and is_holding_v:
                peek_banner = FONT_BOLD.render("[ MODO ESPIAR MESA ATIVO — SOLTE 'V' PARA RETORNAR ]", True, COLOR_GOLD_BRIGHT)
                b_rect = peek_banner.get_rect(center=(WINDOW_WIDTH // 2, 60))
                pygame.draw.rect(render_surf, (15, 20, 35, 230), b_rect.inflate(20, 10), border_radius=8)
                pygame.draw.rect(render_surf, COLOR_GOLD, b_rect.inflate(20, 10), width=1, border_radius=8)
                render_surf.blit(peek_banner, b_rect)

        # Draw Flying Chips
        for c in self.flying_chips:
            cx, cy = c.get_pos()
            chip_surf = ChipRenderer.get_chip(c.color, diameter=22)
            render_surf.blit(chip_surf, (cx - 11, cy - 11))

        # Draw Floating Badges
        for badge in self.floating_badges:
            badge.draw(render_surf)

        # Screen Flash overlay
        flash_duration = self.get_animation_duration(0.30)
        if now - self.screen_flash < flash_duration:
            flash_a = int((1.0 - (now - self.screen_flash) / flash_duration) * 85)
            f_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            f_surf.fill((*self.flash_color, flash_a))
            render_surf.blit(f_surf, (0, 0))

        # Blit with screen shake
        if self.state == "GAME" and self.screen.get_size() != (WINDOW_WIDTH, WINDOW_HEIGHT):
            width, height = self.screen.get_size()
            scale = min(width / WINDOW_WIDTH, height / WINDOW_HEIGHT)
            rendered = pygame.transform.smoothscale(render_surf, (int(WINDOW_WIDTH * scale), int(WINDOW_HEIGHT * scale)))
            self.screen.fill(COLOR_ROOM_BG)
            self.screen.blit(rendered, rendered.get_rect(center=(width // 2, height // 2)))
        else:
            self.screen.blit(render_surf, (shake_x, shake_y))
        pygame.display.flip()

    def game_coordinates(self, position):
        width, height = self.screen.get_size()
        scale = min(width / WINDOW_WIDTH, height / WINDOW_HEIGHT)
        return ((position[0] - (width - WINDOW_WIDTH * scale) / 2) / scale,
                (position[1] - (height - WINDOW_HEIGHT * scale) / 2) / scale)

    # =========================================================================
    # GAME SCREEN: MESA, JOGADORES, POTE & COMMUNITY CARDS
    # =========================================================================
    def draw_game(self, surface: pygame.Surface):
        self.game_view.draw(surface, self)
        self.draw_top_bar(surface)
        self.draw_bottom_console(surface)

    # =========================================================================
    # CENTER BOARD: THE POT & 5 COMMUNITY CARDS
    # =========================================================================
    def draw_center_board(self, surface: pygame.Surface):
        tcx, tcy = 640, 380

        # === 1. THE POT & 3D CHIP PILE ===
        pot_y = 250
        ChipRenderer.draw_chip_stack(surface, tcx - 120, pot_y + 8, self.engine.pot)
        ChipRenderer.draw_chip_stack(surface, tcx + 120, pot_y + 8, self.engine.pot)

        pot_val = f"${self.engine.pot:,}"
        pot_str = f"★ POTE TOTAL: {pot_val} ★"

        now = time.time()
        bounce_duration = self.get_animation_duration(0.35)
        is_bouncing = (now - self.pot_bounce < bounce_duration)
        p_surf = FONT_POT.render(pot_str, True, COLOR_GOLD_BRIGHT if is_bouncing else COLOR_GOLD)
        p_rect = p_surf.get_rect(center=(tcx, pot_y))

        plaque_rect = p_rect.inflate(44, 14)
        pygame.draw.rect(surface, (18, 22, 36), plaque_rect, border_radius=12)
        pygame.draw.rect(surface, COLOR_BRASS, plaque_rect, width=2, border_radius=12)
        if is_bouncing:
            draw_glow_rect(surface, plaque_rect, COLOR_GOLD, radius=8, border_radius=12, alpha=160)
        surface.blit(p_surf, p_rect)

        # === 2. STREET BADGE ===
        street_str = f"• {self.engine.stage} •"
        st_surf = FONT_STREET.render(street_str, True, COLOR_WHITE)
        st_rect = st_surf.get_rect(center=(tcx, pot_y + 36))
        pygame.draw.rect(surface, (12, 16, 28, 200), st_rect.inflate(20, 6), border_radius=6)
        pygame.draw.rect(surface, COLOR_BRASS_DARK, st_rect.inflate(20, 6), width=1, border_radius=6)
        surface.blit(st_surf, st_rect)

        # === 3. COMMUNITY CARDS (5 SLOTS) ===
        cards_y = 330
        card_w = CardRenderer.CARD_WIDTH
        gap = 14
        total_w = 5 * card_w + 4 * gap
        start_x = tcx - total_w // 2

        for i in range(5):
            c_x = start_x + i * (card_w + gap)
            slot_rect = pygame.Rect(c_x, cards_y, card_w, CardRenderer.CARD_HEIGHT)

            pygame.draw.rect(surface, (6, 45, 30), slot_rect, border_radius=7)
            pygame.draw.rect(surface, (18, 90, 60), slot_rect, width=1, border_radius=7)

            if i < len(self.engine.community_cards):
                card_int = self.engine.community_cards[i]
                is_showdown = (self.engine.stage == "SHOWDOWN" or self.engine.hand_ended)
                CardRenderer.draw_card(surface, c_x, cards_y, card_int, face_down=False, glow=is_showdown, glow_color=COLOR_GOLD)
            else:
                empty_mark = FONT_CARD_SUIT.render("♠", True, (15, 60, 42))
                surface.blit(empty_mark, empty_mark.get_rect(center=slot_rect.center))

    # =========================================================================
    # PLAYER STATION HUD (Tactile Arcade Station Seated at the Table)
    # =========================================================================
    def draw_player_station(self, surface: pygame.Surface, player: Player, idx: int):
        p_cfg = PLAYER_CONFIG[idx]
        theme_col = p_cfg["theme_color"]
        cx, cy = self.seat_anchors[idx]

        is_active_turn = (player.idx == self.engine.current_player_idx and not self.engine.hand_ended)
        is_winner = (self.engine.hand_ended and self.engine.winners_info and player.idx == self.engine.winners_info[0]["player"].idx)
        is_dealer = (player.idx == self.engine.dealer_idx)
        has_folded = not player.is_active

        w, h = 260, 92
        station_rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)

        # 1. Active Turn Halo / Glow
        if is_winner:
            draw_glow_rect(surface, station_rect, COLOR_GOLD, radius=12, border_radius=14, alpha=200)
        elif is_active_turn:
            pulse_a = int(pulse(6.0, 100, 220))
            draw_glow_rect(surface, station_rect, theme_col, radius=10, border_radius=14, alpha=pulse_a)

        # 2. Main Station Plate
        plate_bg = (14, 18, 30) if not has_folded else (10, 12, 18)
        pygame.draw.rect(surface, plate_bg, station_rect, border_radius=14)

        border_col = COLOR_GOLD if is_winner else (theme_col if not has_folded else (50, 60, 80))
        border_w = 3 if is_active_turn or is_winner else 2
        pygame.draw.rect(surface, border_col, station_rect, width=border_w, border_radius=14)

        bar_col = theme_col if not has_folded else (60, 70, 85)
        pygame.draw.rect(surface, bar_col, (station_rect.x + 8, station_rect.y + 3, w - 16, 3), border_radius=2)

        # 3. Avatar Portrait
        avatar_img = self.avatar_cache.get(idx)
        if avatar_img:
            surface.blit(avatar_img, (station_rect.x + 10, station_rect.y + 14))

        # 4. Player Details
        name_col = COLOR_WHITE if not has_folded else (120, 130, 145)
        name_s = FONT_PLAYER_NAME.render(p_cfg["name"], True, name_col)
        surface.blit(name_s, (station_rect.x + 78, station_rect.y + 12))

        tag_text = f"[{p_cfg['archetype']}]"
        tag_s = FONT_TAG.render(tag_text, True, theme_col if not has_folded else (100, 110, 125))
        surface.blit(tag_s, (station_rect.x + 78, station_rect.y + 34))

        stack_str = f"${player.stack:,}"
        stack_s = FONT_PLAYER_STACK.render(stack_str, True, COLOR_GOLD_BRIGHT if not has_folded else (110, 120, 135))
        mini_chip = ChipRenderer.get_chip(COLOR_CHIP_GOLD, diameter=16)
        surface.blit(mini_chip, (station_rect.x + 78, station_rect.y + 54))
        surface.blit(stack_s, (station_rect.x + 98, station_rect.y + 51))

        # 5. Position & Dealer Badge
        if is_dealer:
            d_surf = pygame.Surface((22, 22), pygame.SRCALPHA)
            pygame.draw.circle(d_surf, COLOR_BRASS, (11, 11), 10)
            pygame.draw.circle(d_surf, COLOR_BRASS_LIGHT, (11, 11), 8, width=1)
            d_txt = FONT_TAG.render("D", True, COLOR_DARK_TEXT)
            d_surf.blit(d_txt, d_txt.get_rect(center=(11, 11)))
            surface.blit(d_surf, (station_rect.right - 28, station_rect.y + 12))

        # 6. Current Bet Badge
        if player.current_bet > 0 and not self.engine.hand_ended:
            self._draw_bet_pill(surface, idx, player.current_bet)

        # 7. Player Hole Cards
        self._draw_player_cards(surface, player, idx, is_winner)

        # 8. AI Mind Inspector
        self._draw_ai_mind_inspector(surface, player, idx, station_rect, is_active_turn)

    def _draw_bet_pill(self, surface: pygame.Surface, player_idx: int, amount: int):
        px, py = self.seat_anchors[player_idx]
        dir_x = 640 - px
        dir_y = 380 - py
        dist = math.hypot(dir_x, dir_y)
        offset_dist = 75
        bx = int(px + (dir_x / dist) * offset_dist)
        by = int(py + (dir_y / dist) * offset_dist)

        ChipRenderer.draw_chip_stack(surface, bx - 28, by, amount)

        bet_text = f"${amount}"
        b_surf = FONT_TAG.render(bet_text, True, COLOR_WHITE)
        pill_rect = b_surf.get_rect(center=(bx + 12, by))
        pill_bg = pill_rect.inflate(14, 6)
        pygame.draw.rect(surface, (20, 24, 38), pill_bg, border_radius=8)
        pygame.draw.rect(surface, COLOR_BRASS, pill_bg, width=1, border_radius=8)
        surface.blit(b_surf, pill_rect)

    def _draw_player_cards(self, surface: pygame.Surface, player: Player, player_idx: int, is_winner: bool):
        px, py = self.seat_anchors[player_idx]
        show_cards = self.god_mode or self.engine.hand_ended

        if player_idx == 0:    # North
            c1_x, c1_y = px + 140, py - 40
        elif player_idx == 1:  # East
            c1_x, c1_y = px - 55, py + 55
        elif player_idx == 2:  # South (YOU)
            c1_x, c1_y = px + 160, py - 40
        else:                  # West
            c1_x, c1_y = px - 55, py + 55

        c2_x = c1_x + 36
        c2_y = c1_y

        if player.hand and len(player.hand) >= 2 and player.is_active:
            CardRenderer.draw_card(surface, c1_x, c1_y, player.hand[0], face_down=not show_cards, scale=0.88, glow=is_winner)
            CardRenderer.draw_card(surface, c2_x, c2_y, player.hand[1], face_down=not show_cards, scale=0.88, glow=is_winner)
        elif not player.is_active:
            CardRenderer.draw_card(surface, c1_x, c1_y, None, face_down=True, scale=0.80)
            CardRenderer.draw_card(surface, c2_x, c2_y, None, face_down=True, scale=0.80)

    def _draw_ai_mind_inspector(self, surface: pygame.Surface, player: Player, player_idx: int, station_rect: pygame.Rect, is_active_turn: bool):
        if not player.is_active:
            f_rect = pygame.Rect(station_rect.x + 78, station_rect.y + 48, 110, 22)
            pygame.draw.rect(surface, (80, 20, 25), f_rect, border_radius=5)
            f_s = FONT_TAG.render("✕ DESISTIU (FOLD)", True, (255, 120, 130))
            surface.blit(f_s, f_s.get_rect(center=f_rect.center))
            return

        telemetry = player.last_telemetry
        if not telemetry:
            return

        eq = telemetry.get("equity", 50.0)
        is_bluff = telemetry.get("is_bluff", False)
        action = telemetry.get("action", "")

        if is_bluff:
            tag_text = "🎭 INTENÇÃO: BLEFE"
            tag_col = COLOR_NEON_PURPLE
        elif action in ("raise", "all-in") and eq >= 55.0:
            tag_text = "🔥 INTENÇÃO: ATAQUE"
            tag_col = COLOR_NEON_RED
        elif eq < 35.0:
            tag_text = "🛡️ INTENÇÃO: CAUTELA"
            tag_col = COLOR_NEON_GREEN
        else:
            tag_text = "🧠 INTENÇÃO: CÁLCULO"
            tag_col = COLOR_NEON_CYAN

        bar_x = station_rect.x + 78
        bar_y = station_rect.y + 73
        bar_w = 90
        bar_h = 6

        pygame.draw.rect(surface, (25, 30, 48), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        fill_w = int((max(0.0, min(100.0, eq)) / 100.0) * bar_w)
        if fill_w > 0:
            pygame.draw.rect(surface, tag_col, (bar_x, bar_y, fill_w, bar_h), border_radius=3)

        eq_s = FONT_TINY.render(f"{eq:.0f}%", True, COLOR_MUTED)
        surface.blit(eq_s, (bar_x + bar_w + 6, bar_y - 3))

        tag_surf = FONT_TINY.render(tag_text, True, tag_col)
        surface.blit(tag_surf, (bar_x, bar_y - 14))

        if is_active_turn:
            thought = self._format_thought_text(telemetry)
            self._draw_speech_bubble(surface, station_rect, thought, tag_col)

    def _format_thought_text(self, telemetry: Dict[str, Any]) -> str:
        eq = telemetry.get("equity", 50.0)
        action = telemetry.get("action", "")
        is_bluff = telemetry.get("is_bluff", False)

        if is_bluff:
            return f"\"Mão fraca, mas vou blefar pesado para assustar a mesa!\""
        if action == "all-in":
            return f"\"Chance de {eq:.0f}%. Tudo ou nada, ALL-IN!\""
        if action == "raise":
            return f"\"Minha chance é {eq:.0f}%. Aumentando para extrair fichas!\""
        if action == "call":
            return f"\"Preço justo com {eq:.0f}%. Vale a pena ver a carta.\""
        if action == "fold":
            return f"\"{eq:.0f}% é muito arriscado. Protegendo meu stack.\""
        return f"\"Avaliando a mesa com {eq:.0f}% de probabilidade...\""

    def _draw_speech_bubble(self, surface: pygame.Surface, station_rect: pygame.Rect, text: str, border_col: Tuple[int, int, int]):
        t_surf = FONT_SMALL.render(text, True, COLOR_WHITE)
        bw, bh = t_surf.get_width() + 20, t_surf.get_height() + 12

        bx = station_rect.centerx - bw // 2
        by = station_rect.y - bh - 8

        b_rect = pygame.Rect(bx, by, bw, bh)
        pygame.draw.rect(surface, (16, 20, 36), b_rect, border_radius=8)
        pygame.draw.rect(surface, border_col, b_rect, width=1, border_radius=8)
        surface.blit(t_surf, (bx + 10, by + 6))

    # =========================================================================
    # DRAMATIC ALL-IN ALERT BANNER
    # =========================================================================
    def draw_all_in_alert_banner(self, surface: pygame.Surface):
        banner_w, banner_h = 700, 50
        bx = (WINDOW_WIDTH - banner_w) // 2
        by = 185
        rect = pygame.Rect(bx, by, banner_w, banner_h)

        pulse_a = int(pulse(10.0, 160, 255))
        pygame.draw.rect(surface, (120, 15, 25), rect, border_radius=10)
        pygame.draw.rect(surface, (255, 60, 80), rect, width=2, border_radius=10)
        draw_glow_rect(surface, rect, (255, 45, 65), radius=8, border_radius=10, alpha=pulse_a)

        msg = f"⚡ ALL-IN DETECTADO: {self.all_in_player_name.upper()} COLOCOU TUDO EM JOGO! ⚡"
        txt = FONT_HEADER.render(msg, True, COLOR_WHITE)
        surface.blit(txt, txt.get_rect(center=rect.center))

    # =========================================================================
    # TOP HEADER & BOTTOM ARCADE CONSOLE
    # =========================================================================
    def draw_top_bar(self, surface: pygame.Surface):
        bar_rect = pygame.Rect(0, 0, WINDOW_WIDTH, 38)
        pygame.draw.rect(surface, (10, 14, 24), bar_rect)
        pygame.draw.line(surface, (35, 42, 65), (0, 38), (WINDOW_WIDTH, 38), 1)

        title = FONT_HEADER.render("♠ POKER ROYALE — TEXAS HOLD'EM AI", True, COLOR_BRASS)
        surface.blit(title, (24, 7))

        # Mode status indicators on top right
        speed_str = f"VELOCIDADE: {self.game_speed}x"
        god_str = f"MODO DEUS [D]: {'LIGADO' if self.god_mode else 'DESLIGADO'}"
        auto_str = f"AUTO-PLAY [A]: {'ATIVO' if self.auto_play else 'PAUSADO'}"

        sp_col = COLOR_GOLD_BRIGHT
        g_col = COLOR_NEON_GREEN if self.god_mode else COLOR_MUTED
        a_col = COLOR_NEON_CYAN if self.auto_play else COLOR_MUTED

        sp_surf = FONT_BOLD.render(speed_str, True, sp_col)
        g_surf = FONT_BOLD.render(god_str, True, g_col)
        a_surf = FONT_BOLD.render(auto_str, True, a_col)

        surface.blit(sp_surf, (WINDOW_WIDTH - 550, 10))
        surface.blit(g_surf, (WINDOW_WIDTH - 380, 10))
        surface.blit(a_surf, (WINDOW_WIDTH - 180, 10))

    def draw_bottom_console(self, surface: pygame.Surface):
        """Renders tactile arcade buttons for gameplay and speed controls."""
        console_rect = pygame.Rect(0, 730, WINDOW_WIDTH, 70)
        pygame.draw.rect(surface, (12, 16, 28), console_rect)
        pygame.draw.line(surface, COLOR_BRASS_DARK, (0, 730), (WINDOW_WIDTH, 730), 2)

        mouse_pos = self.game_coordinates(pygame.mouse.get_pos())

        def draw_btn(rect: pygame.Rect, text: str, base_col: Tuple[int, int, int], text_col: Tuple[int, int, int] = COLOR_WHITE, highlight: bool = False, active: bool = False):
            is_hover = rect.collidepoint(mouse_pos)
            col = lerp_color(base_col, (255, 255, 255), 0.22) if is_hover else base_col

            pygame.draw.rect(surface, (0, 0, 0, 120), rect.move(0, 3), border_radius=8)
            pygame.draw.rect(surface, col, rect, border_radius=8)

            border_col = COLOR_GOLD_BRIGHT if active else (COLOR_BRASS_LIGHT if highlight else (255, 255, 255, 90))
            border_thick = 2 if (active or highlight) else 1
            pygame.draw.rect(surface, border_col, rect, width=border_thick, border_radius=8)

            if highlight or active:
                glow_col = COLOR_GOLD_BRIGHT if active else base_col
                draw_glow_rect(surface, rect, glow_col, radius=6, border_radius=8, alpha=150)

            t_s = FONT_ARCADE_BTN.render(text, True, text_col)
            surface.blit(t_s, t_s.get_rect(center=rect.center))

        # 1. Speed Controls: [ 1x ] [ 2x ] [ 3x ]
        draw_btn(self.btn_sp_1x, "1x", (36, 42, 60), COLOR_GOLD_BRIGHT if self.game_speed == 1 else COLOR_WHITE, active=(self.game_speed == 1))
        draw_btn(self.btn_sp_2x, "2x", (36, 42, 60), COLOR_GOLD_BRIGHT if self.game_speed == 2 else COLOR_WHITE, active=(self.game_speed == 2))
        draw_btn(self.btn_sp_3x, "3x", (36, 42, 60), COLOR_GOLD_BRIGHT if self.game_speed == 3 else COLOR_WHITE, active=(self.game_speed == 3))

        # 2. God Mode: [ 👁️ DEUS (D) ]
        god_label = "👁️ DEUS: ON" if self.god_mode else "👁️ DEUS: OFF"
        draw_btn(self.btn_god, god_label, (135, 75, 215) if self.god_mode else (36, 42, 60))

        # 3. Main Next Action: [ ▶ PRÓXIMA AÇÃO (ESPAÇO) ]
        draw_btn(self.btn_next, "▶ PRÓXIMA AÇÃO [ESPAÇO]", (34, 168, 86), COLOR_WHITE, highlight=True)

        # 4. Auto-Play: [ ⚡ AUTO-PLAY (A) ]
        auto_label = "⚡ AUTO-PLAY: ON" if self.auto_play else "⚡ AUTO-PLAY: OFF"
        draw_btn(self.btn_auto, auto_label, (45, 125, 220) if self.auto_play else (36, 42, 60))

        # 5. Highlights History: [ ★ RECORDES (H) ]
        draw_btn(self.btn_history, "★ RECORDES [H]", (190, 130, 25), COLOR_WHITE, highlight=self.show_history_modal)

        # 6. Reset & Menu Buttons
        draw_btn(self.btn_reset, "🔄 REINICIAR", (160, 45, 50))
        draw_btn(self.btn_menu, "☰ MENU [ESC]", (45, 55, 75))

    # =========================================================================
    # ADVANCED ROUND HIGHLIGHT MODAL (Melhores Momentos & "E SE?")
    # =========================================================================
    def draw_modal_popup(self, surface: pygame.Surface):
        hl = self.last_highlight
        if not hl:
            return

        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 12, 22, 230))
        surface.blit(overlay, (0, 0))

        m_rect = self.modal_rect
        accent_col = getattr(hl, "color", COLOR_GOLD)
        intensity = getattr(hl, "intensity", 2)

        # Main Modal Box with dynamic glow based on intensity
        pygame.draw.rect(surface, (16, 22, 38), m_rect, border_radius=18)
        border_w = 4 if intensity >= 3 else 2
        pygame.draw.rect(surface, accent_col, m_rect, width=border_w, border_radius=18)
        glow_rad = 14 if intensity >= 3 else 8
        draw_glow_rect(surface, m_rect, accent_col, radius=glow_rad, border_radius=18, alpha=170)

        # 1. Header: Big Impact Title
        title_text = getattr(hl, "title", "★ MELHOR MOMENTO DA RODADA ★")
        title_s = FONT_MODAL_TITLE.render(title_text, True, accent_col)
        surface.blit(title_s, title_s.get_rect(center=(WINDOW_WIDTH // 2, m_rect.y + 32)))

        # Headline
        headline_text = getattr(hl, "headline", "")
        if headline_text:
            head_s = FONT_HEADER.render(headline_text, True, COLOR_WHITE)
            surface.blit(head_s, head_s.get_rect(center=(WINDOW_WIDTH // 2, m_rect.y + 64)))

        pygame.draw.line(surface, (45, 55, 80), (m_rect.x + 30, m_rect.y + 88), (m_rect.right - 30, m_rect.y + 88), 1)

        # 2. Board Cards in Modal
        b_label = FONT_BOLD.render("CARTAS DA MESA:", True, COLOR_BRASS)
        surface.blit(b_label, (m_rect.x + 40, m_rect.y + 102))

        b_start_x = m_rect.x + 220
        b_start_y = m_rect.y + 98
        board_cards = getattr(hl, "board_cards", self.engine.community_cards)
        for i in range(5):
            cx = b_start_x + i * 50
            if i < len(board_cards):
                CardRenderer.draw_card(surface, cx, b_start_y, board_cards[i], face_down=False, scale=0.68)
            else:
                CardRenderer.draw_card(surface, cx, b_start_y, None, face_down=True, scale=0.68)

        # 3. Winner Spotlight Box
        w_box = pygame.Rect(m_rect.x + 35, m_rect.y + 175, 380, 130)
        pygame.draw.rect(surface, (22, 30, 52), w_box, border_radius=12)
        pygame.draw.rect(surface, COLOR_GOLD, w_box, width=2, border_radius=12)

        winner_name = getattr(hl, "player_name", "Vencedor")
        w_lbl = FONT_HEADER.render(f"👑 VENCEDOR: {winner_name}", True, COLOR_GOLD_BRIGHT)
        surface.blit(w_lbl, (w_box.x + 14, w_box.y + 10))

        winner_cards = getattr(hl, "primary_cards", [])
        if winner_cards and len(winner_cards) >= 2:
            CardRenderer.draw_card(surface, w_box.x + 14, w_box.y + 36, winner_cards[0], scale=0.78, glow=True)
            CardRenderer.draw_card(surface, w_box.x + 72, w_box.y + 36, winner_cards[1], scale=0.78, glow=True)
            
            pot_amt = getattr(hl, "pot_amount", self.engine.pot)
            won_s = FONT_HEADER.render(f"Levou: ${pot_amt:,}", True, COLOR_NEON_GREEN)
            surface.blit(won_s, (w_box.x + 140, w_box.y + 44))
            pote_label = FONT_MAIN.render("Pote Conquistado", True, COLOR_MUTED)
            surface.blit(pote_label, (w_box.x + 140, w_box.y + 70))

        # 4. Narrative Story Lines (Right Box)
        n_box = pygame.Rect(m_rect.right - 415, m_rect.y + 175, 380, 130)
        pygame.draw.rect(surface, (20, 26, 45), n_box, border_radius=12)
        pygame.draw.rect(surface, (45, 55, 80), n_box, width=1, border_radius=12)

        story_title = FONT_BOLD.render("O QUE ACONTECEU:", True, accent_col)
        surface.blit(story_title, (n_box.x + 14, n_box.y + 10))

        narrative = getattr(hl, "narrative_lines", [])
        for li, line in enumerate(narrative[:3]):
            l_col = COLOR_WHITE if li == 0 else COLOR_MUTED
            surface.blit(FONT_SMALL.render(f"•  {line}", True, l_col), (n_box.x + 14, n_box.y + 34 + li * 26))

        # 5. Seção "⚠ E SE?" (Curiosidade Contrafactual)
        has_counter = getattr(hl, "has_counterfactual", False)
        if has_counter:
            cf_box = pygame.Rect(m_rect.x + 35, m_rect.y + 320, m_rect.width - 70, 135)
            pygame.draw.rect(surface, (30, 24, 18), cf_box, border_radius=12)
            pygame.draw.rect(surface, COLOR_ORANGE, cf_box, width=2, border_radius=12)
            draw_glow_rect(surface, cf_box, COLOR_ORANGE, radius=6, border_radius=12, alpha=100)

            cf_title = getattr(hl, "counterfactual_title", "⚠ E SE?")
            t_s = FONT_HEADER.render(cf_title, True, COLOR_ORANGE)
            surface.blit(t_s, (cf_box.x + 16, cf_box.y + 10))

            cf_desc = getattr(hl, "counterfactual_desc", "")
            d_s = FONT_BOLD.render(cf_desc, True, COLOR_WHITE)
            surface.blit(d_s, (cf_box.x + 16, cf_box.y + 36))

            cf_cards = getattr(hl, "counterfactual_cards", [])
            if cf_cards and len(cf_cards) >= 2:
                CardRenderer.draw_card(surface, cf_box.x + 16, cf_box.y + 60, cf_cards[0], scale=0.65)
                CardRenderer.draw_card(surface, cf_box.x + 68, cf_box.y + 60, cf_cards[1], scale=0.65)

            disc = getattr(hl, "counterfactual_disclaimer", "RESULTADO SIMULADO — a mão foi encerrada após o fold.")
            disc_s = FONT_SMALL.render(f"[{disc}]", True, (255, 175, 100))
            surface.blit(disc_s, (cf_box.x + 130, cf_box.y + 80))

        # 6. Modal Footer Prompts
        foot_rect = pygame.Rect(WINDOW_WIDTH // 2 - 320, m_rect.bottom - 54, 640, 42)
        pygame.draw.rect(surface, (28, 36, 62), foot_rect, border_radius=20)
        pygame.draw.rect(surface, COLOR_GOLD, foot_rect, width=2, border_radius=20)
        prompt_s = FONT_BOLD.render("[ SEGURE 'V' PARA ESPIAR A MESA ]   •   [ ESPAÇO PARA CONTINUAR ]", True, COLOR_GOLD_BRIGHT)
        surface.blit(prompt_s, prompt_s.get_rect(center=foot_rect.center))

    # =========================================================================
    # MATCH RECORDS & HIGHLIGHTS HISTORY MODAL (Salão da Fama)
    # =========================================================================
    def draw_history_modal(self, surface: pygame.Surface):
        """Renders the comprehensive Match Records and Highlights History modal."""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 12, 22, 235))
        surface.blit(overlay, (0, 0))

        h_rect = self.history_modal_rect
        pygame.draw.rect(surface, (16, 22, 38), h_rect, border_radius=18)
        pygame.draw.rect(surface, COLOR_GOLD, h_rect, width=3, border_radius=18)
        draw_glow_rect(surface, h_rect, COLOR_GOLD, radius=12, border_radius=18, alpha=160)

        # Header Title
        title_s = FONT_MODAL_TITLE.render("★ SALÃO DA FAMA & RECORDES DA PARTIDA ★", True, COLOR_GOLD_BRIGHT)
        surface.blit(title_s, title_s.get_rect(center=(WINDOW_WIDTH // 2, h_rect.y + 32)))

        sub_s = FONT_SMALL.render("Estatísticas acumuladas, momentos marcantes e recordes históricos da sessão", True, COLOR_MUTED)
        surface.blit(sub_s, sub_s.get_rect(center=(WINDOW_WIDTH // 2, h_rect.y + 60)))

        pygame.draw.line(surface, (45, 55, 80), (h_rect.x + 30, h_rect.y + 80), (h_rect.right - 30, h_rect.y + 80), 1)

        # 6 Record Cards Grid (3 columns x 2 rows)
        grid_x = h_rect.x + 30
        grid_y = h_rect.y + 95
        card_w = 260
        card_h = 100
        gap_x = 20
        gap_y = 15

        # 1. Maior Pote
        hp = self.tracker.highest_pot
        r1_rect = pygame.Rect(grid_x, grid_y, card_w, card_h)
        self._draw_record_card(surface, r1_rect, "🏆 MAIOR POTE", f"${hp['amount']:,}", f"Vencedor: {hp['winner']} (Mão #{hp['hand_num']})", COLOR_GOLD_BRIGHT)

        # 2. Maior Aposta
        hb = self.tracker.highest_bet
        r2_rect = pygame.Rect(grid_x + card_w + gap_x, grid_y, card_w, card_h)
        self._draw_record_card(surface, r2_rect, "🔥 MAIOR APOSTA", f"${hb['amount']:,}", f"Jogador: {hb['player']} (Mão #{hb['hand_num']})", COLOR_ORANGE)

        # 3. Melhor Blefe
        bb = self.tracker.best_bluff or {"player": "Nenhum", "pot": 0, "hand_num": 0}
        r3_rect = pygame.Rect(grid_x + 2 * (card_w + gap_x), grid_y, card_w, card_h)
        self._draw_record_card(surface, r3_rect, "🎭 MELHOR BLEFE", f"{bb['player']}", f"Lucrou ${bb['pot']:,} sem showdown (Mão #{bb['hand_num']})", COLOR_NEON_PURPLE)

        # 4. Maior Virada
        bc = self.tracker.best_comeback or {"player": "Nenhum", "pot": 0, "hand_num": 0}
        r4_rect = pygame.Rect(grid_x, grid_y + card_h + gap_y, card_w, card_h)
        self._draw_record_card(surface, r4_rect, "💥 MAIOR VIRADA", f"{bc['player']}", f"Virou no River e levou ${bc['pot']:,} (Mão #{bc['hand_num']})", COLOR_NEON_RED)

        # 5. Mão Mais Forte
        sh = self.tracker.strongest_hand
        r5_rect = pygame.Rect(grid_x + card_w + gap_x, grid_y + card_h + gap_y, card_w, card_h)
        self._draw_record_card(surface, r5_rect, "🃏 MÃO MAIS FORTE", f"{sh['class_name']}", f"Formada por {sh['player']} (Mão #{sh['hand_num']})", COLOR_NEON_GREEN)

        # 6. Fold Curioso Mais Marcante
        nf = self.tracker.notable_folds[-1] if self.tracker.notable_folds else {"player": "Nenhum", "hand_class": "Nenhuma", "pot": 0, "hand_num": 0}
        r6_rect = pygame.Rect(grid_x + 2 * (card_w + gap_x), grid_y + card_h + gap_y, card_w, card_h)
        self._draw_record_card(surface, r6_rect, "⚠ FOLD CURIOSO", f"{nf['player']}", f"Perdeu ${nf['pot']:,} com {nf['hand_class']} (Mão #{nf['hand_num']})", (255, 175, 100))

        # Feed dos Últimos Destaques
        feed_y = grid_y + 2 * (card_h + gap_y) + 15
        f_lbl = FONT_BOLD.render("ÚLTIMOS DESTAQUES REGISTRADOS NA PARTIDA:", True, COLOR_BRASS)
        surface.blit(f_lbl, (grid_x, feed_y))

        for idx, item in enumerate(self.tracker.recent_highlights[:4]):
            hl_y = feed_y + 24 + idx * 30
            pygame.draw.rect(surface, (20, 26, 42), (grid_x, hl_y, h_rect.width - 60, 24), border_radius=6)
            
            # Badge de categoria
            tag_col = getattr(item, "color", COLOR_GOLD)
            tag_s = FONT_TINY.render(f"[{item.event_type}]", True, tag_col)
            surface.blit(tag_s, (grid_x + 10, hl_y + 4))

            # Headline & Pote
            desc_str = f"{item.headline} (Pote: ${item.pot_amount:,})"
            desc_s = FONT_SMALL.render(desc_str, True, COLOR_WHITE)
            surface.blit(desc_s, (grid_x + 140, hl_y + 3))

        # Footer Prompt
        foot_rect = pygame.Rect(WINDOW_WIDTH // 2 - 250, h_rect.bottom - 50, 500, 38)
        pygame.draw.rect(surface, (28, 36, 62), foot_rect, border_radius=19)
        pygame.draw.rect(surface, COLOR_GOLD, foot_rect, width=1, border_radius=19)
        cl_s = FONT_BOLD.render("[ ESC / ESPAÇO / CLIQUE PARA FECHAR ]", True, COLOR_GOLD_BRIGHT)
        surface.blit(cl_s, cl_s.get_rect(center=foot_rect.center))

    def _draw_record_card(self, surface: pygame.Surface, rect: pygame.Rect, title: str, main_val: str, sub_val: str, accent_col: Tuple[int, int, int]):
        pygame.draw.rect(surface, (20, 26, 44), rect, border_radius=10)
        pygame.draw.rect(surface, accent_col, rect, width=1, border_radius=10)

        t_s = FONT_TAG.render(title, True, accent_col)
        surface.blit(t_s, (rect.x + 12, rect.y + 10))

        v_s = FONT_HEADER.render(main_val, True, COLOR_WHITE)
        surface.blit(v_s, (rect.x + 12, rect.y + 32))

        sub_s = FONT_TINY.render(sub_val, True, COLOR_MUTED)
        surface.blit(sub_s, (rect.x + 12, rect.y + 68))

    # =========================================================================
    # MENU SCREEN: 4 JOKER-STYLE LEGENDS SELECTION
    # =========================================================================
    def draw_menu(self, surface: pygame.Surface):
        self.menu_screen.draw(surface, self)


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    app = PokerPygameApp()
    app.run()
