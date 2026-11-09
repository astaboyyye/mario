"""Game loop, state transitions, input bindings, and asset loading."""

from pathlib import Path

import pygame as pg

from . import constants as c


keybinding = {
    "action": pg.K_z,
    "jump": pg.K_SPACE,
    "left": pg.K_LEFT,
    "right": pg.K_RIGHT,
    "down": pg.K_DOWN,
    "run": pg.K_LSHIFT,
}


class SilentSound:
    """Keep the game playable when no audio device is available."""

    def play(self):
        return None

    def stop(self):
        return None

    def set_volume(self, volume):
        return None


class Control:
    """Run game states on a fixed 60 FPS logical canvas."""

    def __init__(self, caption: str, screen: pg.Surface):
        self.screen = screen
        self.done = False
        self.paused = False
        self.pause_background = None
        self.fullscreen = False
        self.windowed_size = pg.display.get_window_size()
        self.clock = pg.time.Clock()
        self.caption = caption
        self.fps = 60
        self.step_ms = 1000 / self.fps
        self.accumulator = self.step_ms
        self.show_fps = False
        self.muted = False
        self.current_time = 0
        self.keys = pg.key.get_pressed()
        self.state_dict = {}
        self.state_name = None
        self.state = None

    def setup_states(self, state_dict, start_state):
        self.state_dict = state_dict
        self.state_name = start_state
        self.state = self.state_dict[start_state]

    def update(self):
        if self.state.quit:
            self.done = True
        elif self.state.done:
            self.flip_state()
        if not self.done:
            self.state.update(self.screen, self.keys, self.current_time)

    def flip_state(self):
        previous, self.state_name = self.state_name, self.state.next
        persist = self.state.cleanup()
        self.state = self.state_dict[self.state_name]
        self.state.startup(self.current_time, persist)
        self.state.previous = previous

    def event_loop(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.done = True
            elif event.type == pg.VIDEORESIZE and not self.fullscreen:
                self.windowed_size = (max(320, event.w), max(240, event.h))
                pg.display.set_mode(self.windowed_size, pg.RESIZABLE)
            elif event.type == pg.WINDOWFOCUSLOST and self.state_name == c.LEVEL1:
                self.set_paused(True)
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_F5:
                    self.show_fps = not self.show_fps
                elif event.key == pg.K_F11:
                    self.toggle_fullscreen()
                elif event.key == pg.K_m:
                    self.toggle_mute()
                elif event.key in (pg.K_p, pg.K_ESCAPE) and self.state_name == c.LEVEL1:
                    self.set_paused(not self.paused)
                elif event.key == pg.K_ESCAPE and self.state_name == c.MAIN_MENU:
                    self.done = True
            if event.type in (pg.KEYDOWN, pg.KEYUP):
                self.keys = pg.key.get_pressed()
            self.state.get_event(event)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.windowed_size = pg.display.get_window_size()
            pg.display.set_mode((0, 0), pg.FULLSCREEN)
        else:
            pg.display.set_mode(self.windowed_size, pg.RESIZABLE)

    def set_paused(self, paused):
        if paused and not self.paused:
            self.pause_background = self.screen.copy()
            self.accumulator = 0
            if pg.mixer.get_init():
                pg.mixer.music.pause()
        elif not paused:
            self.pause_background = None
            if self.paused and pg.mixer.get_init():
                pg.mixer.music.unpause()
        self.paused = paused

    def toggle_mute(self):
        from . import setup

        self.muted = not self.muted
        volume = 0.0 if self.muted else 1.0
        if pg.mixer.get_init():
            pg.mixer.music.set_volume(volume)
        for sound in setup.SFX.values():
            sound.set_volume(volume)

    def present(self):
        display = pg.display.get_surface()
        width, height = display.get_size()
        logical_width, logical_height = self.screen.get_size()
        scale = min(width / logical_width, height / logical_height)
        target_size = (max(1, round(logical_width * scale)),
                       max(1, round(logical_height * scale)))
        display.fill((0, 0, 0))
        image = pg.transform.scale(self.screen, target_size)
        display.blit(image, image.get_rect(center=display.get_rect().center))
        pg.display.flip()

    def draw_pause_overlay(self):
        if self.pause_background is not None:
            self.screen.blit(self.pause_background, (0, 0))
        overlay = pg.Surface(self.screen.get_size(), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        font = pg.font.Font(None, 64)
        label = font.render("PAUSED", True, (255, 255, 255))
        self.screen.blit(label, label.get_rect(center=self.screen.get_rect().center))
        hint_font = pg.font.Font(None, 30)
        hint = hint_font.render("P / ESC  RESUME       M  MUTE       F11  FULLSCREEN",
                                True, (255, 255, 255))
        self.screen.blit(hint, hint.get_rect(center=(self.screen.get_width() // 2,
                                                   self.screen.get_height() // 2 + 52)))

    def advance(self, elapsed):
        """Catch up simulation in fixed steps after a slow display frame."""
        self.accumulator += min(elapsed, 250)
        while self.accumulator >= self.step_ms and not self.done:
            self.current_time += self.step_ms
            self.update()
            self.accumulator -= self.step_ms

    def main(self):
        while not self.done:
            elapsed = self.clock.tick(self.fps)
            self.event_loop()
            if not self.paused and not self.done:
                self.advance(elapsed)
            if self.paused:
                self.draw_pause_overlay()
            if not self.done:
                self.present()
            if self.show_fps:
                pg.display.set_caption(f"{self.caption} - {self.clock.get_fps():.1f} FPS")
            else:
                pg.display.set_caption(self.caption)


class _State:
    def __init__(self):
        self.start_time = 0
        self.current_time = 0
        self.done = False
        self.quit = False
        self.next = None
        self.previous = None
        self.persist = {}

    def get_event(self, event):
        pass

    def startup(self, current_time, persistent):
        self.persist = persistent
        self.start_time = current_time

    def cleanup(self):
        self.done = False
        return self.persist

    def update(self, surface, keys, current_time):
        pass


def load_all_gfx(directory: Path, colorkey=(255, 0, 255),
                 accept=(".png", ".jpg", ".bmp")):
    graphics = {}
    for path in sorted(directory.iterdir()):
        if path.suffix.lower() not in accept:
            continue
        image = pg.image.load(str(path))
        if image.get_alpha():
            image = image.convert_alpha()
        else:
            image = image.convert()
            image.set_colorkey(colorkey)
        graphics[path.stem] = image
    return graphics


def load_all_music(directory: Path, accept=(".wav", ".mp3", ".ogg")):
    return {path.stem: str(path) for path in sorted(directory.iterdir())
            if path.suffix.lower() in accept}


def load_all_fonts(directory: Path):
    return load_all_music(directory, (".ttf",))


def load_all_sfx(directory: Path, accept=(".wav", ".ogg")):
    return {path.stem: (pg.mixer.Sound(str(path)) if pg.mixer.get_init()
                        else SilentSound())
            for path in sorted(directory.iterdir())
            if path.suffix.lower() in accept}
