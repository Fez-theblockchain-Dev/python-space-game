"""
Game settings persistence and the in-game settings screen.

Settings are stored in localStorage (browser) or game_settings.json (desktop)
and applied when a new run starts from the main menu.
"""
import asyncio
import json
import os
import sys

import pygame

from button import Button
from config import SCREEN_WIDTH, SCREEN_HEIGHT, resource_path

SETTINGS_STORAGE_KEY = "space_cowboys_settings"
SETTINGS_FILE_NAME = "game_settings.json"

DIFFICULTY_OPTIONS = ("Easy", "Normal", "Hard")
DIFFICULTY_ALIEN_MULTIPLIER = {
    "Easy": 0.85,
    "Normal": 1.0,
    "Hard": 1.25,
}

SHIP_SPEED_OPTIONS = ("Slow", "Standard", "Fast")
SHIP_SPEED_VALUES = {
    "Slow": 4,
    "Standard": 5,
    "Fast": 7,
}

DEFAULTS = {
    "muted": False,
    "sfx_volume": 0.7,
    "music_volume": 0.5,
    "theme_index": 0,
    "difficulty": "Normal",
    "ship_speed": "Standard",
}


def running_in_browser() -> bool:
    return sys.platform == "emscripten"


def settings_file_path() -> str:
    game_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(game_dir, SETTINGS_FILE_NAME)


def get_font(size: int) -> pygame.font.Font:
    font_path = resource_path("assets", "Fonts", "hyperspace", "Hyperspace Bold Italic.otf")
    try:
        return pygame.font.Font(font_path, size)
    except Exception:
        return pygame.font.Font(None, size)


class GameSettings:
    """Mutable settings snapshot with load/save helpers."""

    def __init__(self):
        self.muted = DEFAULTS["muted"]
        self.sfx_volume = DEFAULTS["sfx_volume"]
        self.music_volume = DEFAULTS["music_volume"]
        self.theme_index = DEFAULTS["theme_index"]
        self.difficulty = DEFAULTS["difficulty"]
        self.ship_speed = DEFAULTS["ship_speed"]

    def to_dict(self) -> dict:
        return {
            "muted": self.muted,
            "sfx_volume": round(self.sfx_volume, 2),
            "music_volume": round(self.music_volume, 2),
            "theme_index": self.theme_index,
            "difficulty": self.difficulty,
            "ship_speed": self.ship_speed,
        }

    def apply_dict(self, data: dict) -> None:
        if not isinstance(data, dict):
            return
        self.muted = bool(data.get("muted", self.muted))
        self.sfx_volume = clamp01(float(data.get("sfx_volume", self.sfx_volume)))
        self.music_volume = clamp01(float(data.get("music_volume", self.music_volume)))
        self.theme_index = max(0, int(data.get("theme_index", self.theme_index)))
        difficulty = data.get("difficulty", self.difficulty)
        if difficulty in DIFFICULTY_OPTIONS:
            self.difficulty = difficulty
        ship_speed = data.get("ship_speed", self.ship_speed)
        if ship_speed in SHIP_SPEED_OPTIONS:
            self.ship_speed = ship_speed

    def load(self) -> "GameSettings":
        raw = read_settings_blob()
        if raw:
            self.apply_dict(raw)
        return self

    def save(self) -> None:
        write_settings_blob(self.to_dict())

    def alien_speed_multiplier(self) -> float:
        return DIFFICULTY_ALIEN_MULTIPLIER.get(self.difficulty, 1.0)

    def player_speed(self) -> int:
        return SHIP_SPEED_VALUES.get(self.ship_speed, 5)

    def effective_sfx_volume(self) -> float:
        return 0.0 if self.muted else self.sfx_volume

    def effective_music_volume(self) -> float:
        return 0.0 if self.muted else self.music_volume


game_settings = GameSettings().load()


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def value_from_x(x: int, track: pygame.Rect) -> float:
    if track.width <= 0:
        return 0.0
    relative = (x - track.x) / track.width
    return clamp01(relative)


def read_settings_blob():
    if running_in_browser():
        try:
            from platform import window  # type: ignore[import-not-found]

            stored = window.localStorage.getItem(SETTINGS_STORAGE_KEY)
            if stored and stored != "null":
                return json.loads(stored)
        except Exception as exc:
            print(f"[settings] localStorage read failed: {exc}")
        return None

    path = settings_file_path()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def write_settings_blob(data: dict) -> None:
    if running_in_browser():
        try:
            from platform import window  # type: ignore[import-not-found]

            window.localStorage.setItem(SETTINGS_STORAGE_KEY, json.dumps(data))
        except Exception as exc:
            print(f"[settings] localStorage write failed: {exc}")
        return

    path = settings_file_path()
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
    except OSError as exc:
        print(f"[settings] file write failed: {exc}")


def sync_theme_manager(theme_manager) -> None:
    """Apply saved theme index to the menu theme manager."""
    theme_manager.ensure_themes_loaded()
    if theme_manager.themes:
        game_settings.theme_index %= len(theme_manager.themes)
        theme_manager.current_theme_index = game_settings.theme_index


def apply_theme_manager_to_settings(theme_manager) -> None:
    theme_manager.ensure_themes_loaded()
    if theme_manager.themes:
        game_settings.theme_index = theme_manager.current_theme_index


class Slider:
    """Simple horizontal slider for volume controls."""

    def __init__(self, rect: pygame.Rect, value: float, accent: tuple[int, int, int]):
        self.rect = rect
        self.value = clamp01(value)
        self.accent = accent
        self.dragging = False
        self.knob_radius = 10

    def set_value(self, value: float) -> None:
        self.value = clamp01(value)

    def handle_event(self, event, mouse_pos) -> bool:
        changed = False
        track = self.track_rect()
        knob_x, knob_y = self.knob_center()
        knob_rect = pygame.Rect(0, 0, self.knob_radius * 2, self.knob_radius * 2)
        knob_rect.center = (knob_x, knob_y)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if track.collidepoint(mouse_pos) or knob_rect.collidepoint(mouse_pos):
                self.dragging = True
                self.value = value_from_x(mouse_pos[0], track)
                changed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                changed = True
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.value = value_from_x(mouse_pos[0], track)
            changed = True
        return changed

    def track_rect(self) -> pygame.Rect:
        return pygame.Rect(self.rect.x, self.rect.centery - 4, self.rect.width, 8)

    def knob_center(self) -> tuple[int, int]:
        track = self.track_rect()
        x = track.x + int(self.value * track.width)
        return x, track.centery

    def draw(self, screen: pygame.Surface) -> None:
        track = self.track_rect()
        pygame.draw.rect(screen, (55, 55, 70), track, border_radius=4)
        fill_width = int(self.value * track.width)
        if fill_width > 0:
            fill_rect = pygame.Rect(track.x, track.y, fill_width, track.height)
            pygame.draw.rect(screen, self.accent, fill_rect, border_radius=4)
        knob_x, knob_y = self.knob_center()
        pygame.draw.circle(screen, (240, 240, 240), (knob_x, knob_y), self.knob_radius)
        pygame.draw.circle(screen, self.accent, (knob_x, knob_y), self.knob_radius - 3)


class CycleControl:
    """Previous / next control for discrete options."""

    def __init__(self, rect: pygame.Rect, options: tuple[str, ...], index: int):
        self.rect = rect
        self.options = options
        self.index = index % len(options) if options else 0
        self.prev_rect = pygame.Rect(rect.x, rect.y, 36, rect.height)
        self.next_rect = pygame.Rect(rect.right - 36, rect.y, 36, rect.height)

    @property
    def value(self) -> str:
        return self.options[self.index]

    def set_value(self, value: str) -> None:
        if value in self.options:
            self.index = self.options.index(value)

    def handle_event(self, event, mouse_pos) -> bool:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False
        if self.prev_rect.collidepoint(mouse_pos):
            self.index = (self.index - 1) % len(self.options)
            return True
        if self.next_rect.collidepoint(mouse_pos):
            self.index = (self.index + 1) % len(self.options)
            return True
        return False

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        pygame.draw.rect(screen, (20, 20, 30), self.rect, border_radius=8)
        pygame.draw.rect(screen, (182, 143, 64), self.rect, width=2, border_radius=8)

        prev_label = font.render("<", True, (215, 252, 212))
        next_label = font.render(">", True, (215, 252, 212))
        value_label = font.render(self.value, True, (255, 255, 255))

        screen.blit(prev_label, prev_label.get_rect(center=self.prev_rect.center))
        screen.blit(next_label, next_label.get_rect(center=self.next_rect.center))
        value_rect = value_label.get_rect(center=self.rect.center)
        screen.blit(value_label, value_rect)


def draw_panel(screen: pygame.Surface) -> pygame.Rect:
    panel = pygame.Rect(
        SCREEN_WIDTH // 2 - 420,
        70,
        840,
        SCREEN_HEIGHT - 140,
    )
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    pygame.draw.rect(screen, (18, 18, 28), panel, border_radius=16)
    pygame.draw.rect(screen, (182, 143, 64), panel, width=3, border_radius=16)
    return panel


def draw_section_header(screen: pygame.Surface, font: pygame.font.Font, text: str, y: int) -> None:
    label = font.render(text, True, (182, 143, 64))
    screen.blit(label, (SCREEN_WIDTH // 2 - 380, y))


def draw_row_label(screen: pygame.Surface, font: pygame.font.Font, text: str, y: int) -> None:
    label = font.render(text, True, (215, 252, 212))
    screen.blit(label, (SCREEN_WIDTH // 2 - 380, y))


def draw_percent(screen: pygame.Surface, font: pygame.font.Font, value: float, x: int, y: int) -> None:
    label = font.render(f"{int(value * 100)}%", True, (200, 200, 200))
    screen.blit(label, (x, y))


async def settings_screen(theme_manager, get_screen) -> None:
    """
    Settings overlay loop. Mutates ``game_settings`` and syncs theme on exit.
    """
    from mainMenu import get_screen as menu_get_screen

    if get_screen is None:
        get_screen = menu_get_screen

    title_font = get_font(64)
    section_font = get_font(28)
    row_font = get_font(24)
    hint_font = get_font(20)
    accent = (182, 143, 64)

    sync_theme_manager(theme_manager)
    theme_manager.ensure_themes_loaded()
    theme_names = tuple(name for name, _ in theme_manager.themes) or ("Default",)

    working = GameSettings()
    working.apply_dict(game_settings.to_dict())
    working.theme_index %= max(1, len(theme_names))

    sfx_slider = Slider(pygame.Rect(SCREEN_WIDTH // 2 - 40, 0, 280, 24), working.sfx_volume, accent)
    music_slider = Slider(pygame.Rect(SCREEN_WIDTH // 2 - 40, 0, 280, 24), working.music_volume, accent)
    theme_control = CycleControl(
        pygame.Rect(SCREEN_WIDTH // 2 + 40, 0, 300, 36),
        theme_names,
        working.theme_index,
    )
    difficulty_control = CycleControl(
        pygame.Rect(SCREEN_WIDTH // 2 + 40, 0, 300, 36),
        DIFFICULTY_OPTIONS,
        DIFFICULTY_OPTIONS.index(working.difficulty),
    )
    speed_control = CycleControl(
        pygame.Rect(SCREEN_WIDTH // 2 + 40, 0, 300, 36),
        SHIP_SPEED_OPTIONS,
        SHIP_SPEED_OPTIONS.index(working.ship_speed),
    )

    mute_button = Button(
        image=None,
        pos=(SCREEN_WIDTH // 2 + 360, 0),
        text_input="MUTE: OFF",
        font=get_font(22),
        base_color="#d7fcd4",
        hovering_color="White",
    )

    back_button = Button(
        image=None,
        pos=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 95),
        text_input="BACK",
        font=get_font(56),
        base_color="#d7fcd4",
        hovering_color="White",
    )

    clock = pygame.time.Clock()

    while True:
        screen = get_screen()
        mouse_pos = pygame.mouse.get_pos()

        current_bg = theme_manager.get_current_background()
        screen.blit(current_bg, (0, 0))
        draw_panel(screen)

        title = title_font.render("GAME SETTINGS", True, accent)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 115)))

        draw_section_header(screen, section_font, "AUDIO", 165)
        draw_row_label(screen, row_font, "Sound Effects", 205)
        sfx_slider.rect.y = 205
        sfx_slider.draw(screen)
        draw_percent(screen, row_font, sfx_slider.value, SCREEN_WIDTH // 2 + 260, 205)

        draw_row_label(screen, row_font, "Music", 255)
        music_slider.rect.y = 255
        music_slider.draw(screen)
        draw_percent(screen, row_font, music_slider.value, SCREEN_WIDTH // 2 + 260, 255)

        mute_button.x_pos = SCREEN_WIDTH // 2 + 360
        mute_button.y_pos = 230
        mute_button.text_input = "MUTE: ON" if working.muted else "MUTE: OFF"
        mute_button.text = mute_button.font.render(
            mute_button.text_input,
            True,
            mute_button.base_color,
        )
        mute_button.rect = mute_button.text.get_rect(center=(mute_button.x_pos, mute_button.y_pos))
        mute_button.text_rect = mute_button.text.get_rect(center=(mute_button.x_pos, mute_button.y_pos))
        mute_button.change_color(mouse_pos)
        mute_button.update(screen)

        draw_section_header(screen, section_font, "VISUALS", 315)
        draw_row_label(screen, row_font, "Background", 355)
        theme_control.rect.y = 350
        theme_control.draw(screen, row_font)

        draw_section_header(screen, section_font, "GAMEPLAY", 425)
        draw_row_label(screen, row_font, "Difficulty", 465)
        difficulty_control.rect.y = 460
        difficulty_control.draw(screen, row_font)

        draw_row_label(screen, row_font, "Ship Speed", 515)
        speed_control.rect.y = 510
        speed_control.draw(screen, row_font)

        draw_section_header(screen, section_font, "CONTROLS", 575)
        controls = [
            "Move: Arrow Keys   |   Shoot: Spacebar",
            "Pause: P   |   Resume: Esc   |   Quit to Menu: Q (while paused)",
        ]
        for idx, line in enumerate(controls):
            hint = hint_font.render(line, True, (180, 180, 190))
            screen.blit(hint, (SCREEN_WIDTH // 2 - 380, 610 + idx * 28))

        back_button.change_color(mouse_pos)
        back_button.update(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if sfx_slider.handle_event(event, mouse_pos):
                working.sfx_volume = sfx_slider.value
                if working.sfx_volume > 0:
                    working.muted = False
            if music_slider.handle_event(event, mouse_pos):
                working.music_volume = music_slider.value
                if working.music_volume > 0:
                    working.muted = False

            theme_control.handle_event(event, mouse_pos)
            difficulty_control.handle_event(event, mouse_pos)
            speed_control.handle_event(event, mouse_pos)

            if theme_manager.themes:
                theme_manager.current_theme_index = theme_control.index % len(theme_manager.themes)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if mute_button.check_input(mouse_pos):
                    working.muted = not working.muted
                if back_button.check_input(mouse_pos):
                    game_settings.apply_dict(working.to_dict())
                    game_settings.sfx_volume = sfx_slider.value
                    game_settings.music_volume = music_slider.value
                    game_settings.difficulty = difficulty_control.value
                    game_settings.ship_speed = speed_control.value
                    game_settings.theme_index = theme_control.index
                    game_settings.muted = working.muted
                    game_settings.save()

                    theme_manager.current_theme_index = theme_control.index
                    theme_manager.ensure_themes_loaded()
                    if theme_manager.themes:
                        theme_manager.current_theme_index %= len(theme_manager.themes)
                    return

        pygame.display.update()
        clock.tick(60)
        await asyncio.sleep(0)
