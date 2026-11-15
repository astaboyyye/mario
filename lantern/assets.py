"""Image, font and sound loading with caching."""
import os
import pygame as pg
from .settings import ART, AUDIO, FONTS, TILE

SCALE = TILE / 70
_images = {}
_fonts = {}
_sounds = {}
_state = {'audio': False, 'muted': False, 'music': None}


def img(name, scale=SCALE, flip=False, tint=None, alpha=None):
    """Load 'Folder/file' from the art pack, scaled; results are cached."""
    key = (name, scale, flip, tint, alpha)
    if key not in _images:
        surface = pg.image.load(os.path.join(ART, name + '.png')).convert_alpha()
        if scale != 1:
            size = (max(1, round(surface.get_width() * scale)), max(1, round(surface.get_height() * scale)))
            surface = pg.transform.smoothscale(surface, size)
        if flip:
            surface = pg.transform.flip(surface, True, False)
        if tint:
            surface.fill(tint + (255,), special_flags=pg.BLEND_RGBA_MULT)
        if alpha is not None:
            surface.set_alpha(alpha)
        _images[key] = surface
    return _images[key]


def font(size, bold=False):
    key = (size, bold)
    if key not in _fonts:
        f = pg.font.Font(os.path.join(FONTS, 'Nunito.ttf'), size)
        f.set_bold(bold)
        _fonts[key] = f
    return _fonts[key]


def text(surface, string, size, pos, color=(255, 255, 255), anchor='topleft', bold=False, shadow=None):
    rendered = font(size, bold).render(string, True, color)
    rect = rendered.get_rect(**{anchor: pos})
    if shadow:
        surface.blit(font(size, bold).render(string, True, shadow), rect.move(0, max(2, size // 14)))
    surface.blit(rendered, rect)
    return rect


def wrap(string, size, width, bold=False):
    f = font(size, bold)
    lines = []
    for paragraph in string.split('\n'):
        line = ''
        for word in paragraph.split(' '):
            trial = (line + ' ' + word).strip()
            if f.size(trial)[0] <= width:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def init_audio():
    try:
        pg.mixer.init(22050, -16, 2, 512)
        pg.mixer.set_num_channels(16)
        _state['audio'] = True
    except pg.error:
        _state['audio'] = False


def play(name, volume=0.6):
    if not _state['audio'] or _state['muted']:
        return
    if name not in _sounds:
        path = os.path.join(AUDIO, name + '.wav')
        _sounds[name] = pg.mixer.Sound(path) if os.path.exists(path) else None
    if _sounds[name]:
        _sounds[name].set_volume(volume)
        _sounds[name].play()


def music(name, volume=0.42):
    if not _state['audio'] or _state['music'] == name:
        return
    _state['music'] = name
    pg.mixer.music.stop()
    if name is None:
        return
    path = os.path.join(AUDIO, 'music_' + name + '.wav')
    if os.path.exists(path):
        pg.mixer.music.load(path)
        pg.mixer.music.set_volume(0 if _state['muted'] else volume)
        pg.mixer.music.play(-1, fade_ms=400)


def toggle_mute():
    _state['muted'] = not _state['muted']
    if _state['audio']:
        pg.mixer.music.set_volume(0 if _state['muted'] else 0.42)
    return _state['muted']
