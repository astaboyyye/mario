"""Synthesise every sound and tune the game uses into resources/lantern_audio.

    python tools/make_audio.py

Pure standard library. The tunes are written out below as bars of eighth
notes over a chord per bar; a small chip-style synth renders them.
"""
import math
import os
import random
import struct
import wave

SR = 22050
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources', 'lantern_audio')
SEMIS = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def freq(name):
    letter, rest = name[0], name[1:]
    shift = 0
    while rest[0] in '#b':
        shift += 1 if rest[0] == '#' else -1
        rest = rest[1:]
    return 440 * 2 ** ((SEMIS[letter] + shift + (int(rest) - 4) * 12 - 9) / 12)


def chord(name, octave):
    root = name.rstrip('m')
    minor = name.endswith('m')
    base = SEMIS[root[0]] + (1 if '#' in root else -1 if 'b' in root[1:] else 0)
    return [440 * 2 ** ((base + step + (octave - 4) * 12 - 9) / 12) for step in (0, 3 if minor else 4, 7)]


def osc(kind, phase):
    phase %= 1
    if kind == 'tri':
        return 4 * abs(phase - 0.5) - 1
    if kind == 'sine':
        return math.sin(phase * 2 * math.pi)
    return 1.0 if phase < float(kind) else -1.0      # pulse with the given duty


def add_tone(buf, start, f0, dur, kind='0.25', vol=0.3, f1=None, attack=0.006, release=0.04, sustain=0.6,
             vibrato=0.0):
    n = int(dur * SR)
    begin = int(start * SR)
    phase = 0.0
    size = len(buf)
    for i in range(n):
        t = i / SR
        f = f0 if f1 is None else f0 + (f1 - f0) * i / n
        if vibrato and t > 0.12:
            f *= 1 + vibrato * math.sin(t * 34)
        phase += f / SR
        env = min(1, t / attack) * (sustain + (1 - sustain) * math.exp(-t * 9))
        if t > dur - release:
            env *= max(0, (dur - t) / release)
        buf[(begin + i) % size] += osc(kind, phase) * env * vol


def add_noise(buf, start, dur, vol=0.3, smooth=0.5, rng=random.Random(7)):
    n, begin, last, size = int(dur * SR), int(start * SR), 0.0, len(buf)
    for i in range(n):
        last += (rng.uniform(-1, 1) - last) * smooth
        buf[(begin + i) % size] += last * vol * (1 - i / n) ** 2


def save(name, buf, lowpass=0.62, peak=0.85):
    y, top = 0.0, 0.0001
    out = []
    for x in buf:
        y += (x - y) * lowpass
        out.append(y)
        top = max(top, abs(y))
    scale = peak / top * 32767
    with wave.open(os.path.join(OUT, name + '.wav'), 'wb') as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes(struct.pack('<%dh' % len(out), *(int(v * scale) for v in out)))
    print(name, '%.1fs' % (len(out) / SR))


def sfx(name, dur, build, peak=0.8):
    buf = [0.0] * int(dur * SR)
    build(buf)
    save(name, buf, 0.7, peak)


def notes(buf, names, step, kind='0.25', vol=0.3, last=None):
    for i, n in enumerate(names):
        add_tone(buf, i * step, freq(n), (last if last and i == len(names) - 1 else step * 1.1), kind, vol)


def make_sfx():
    sfx('jump', 0.16, lambda b: add_tone(b, 0, 300, 0.15, '0.25', 0.3, 640))
    sfx('jump2', 0.14, lambda b: add_tone(b, 0, 480, 0.13, '0.125', 0.3, 940))
    sfx('stomp', 0.14, lambda b: (add_tone(b, 0, 520, 0.12, '0.5', 0.3, 110), add_noise(b, 0, 0.06, 0.25)))
    sfx('coin', 0.3, lambda b: (add_tone(b, 0, freq('B5'), 0.06, '0.5', 0.25),
                                add_tone(b, 0.06, freq('E6'), 0.22, '0.5', 0.25, sustain=0.2)))
    sfx('gem', 0.5, lambda b: notes(b, ['E5', 'G#5', 'B5', 'E6', 'G#6'], 0.07, '0.25', 0.28, 0.2))
    sfx('bump', 0.1, lambda b: add_tone(b, 0, 190, 0.09, 'tri', 0.5, 90))
    sfx('break', 0.28, lambda b: (add_noise(b, 0, 0.26, 0.5, 0.35), add_tone(b, 0, 160, 0.12, 'tri', 0.3, 60)))
    sfx('hurt', 0.34, lambda b: add_tone(b, 0, 460, 0.32, '0.5', 0.3, 100, vibrato=0.08))
    sfx('die', 0.9, lambda b: notes(b, ['B4', 'A4', 'G4', 'E4', 'C4'], 0.15, '0.25', 0.3, 0.3))
    sfx('splash', 0.4, lambda b: (add_noise(b, 0, 0.38, 0.5, 0.18), add_tone(b, 0, 300, 0.2, 'sine', 0.2, 120)))
    sfx('spring', 0.3, lambda b: add_tone(b, 0, 180, 0.28, 'tri', 0.5, 950, vibrato=0.05))
    sfx('power', 0.6, lambda b: notes(b, ['C5', 'E5', 'G5', 'C6', 'E6', 'G6'], 0.075, '0.25', 0.28, 0.22))
    sfx('sprout', 0.25, lambda b: add_tone(b, 0, 280, 0.23, 'tri', 0.45, 620))
    sfx('heart', 0.36, lambda b: notes(b, ['E5', 'A5', 'C#6'], 0.09, '0.5', 0.25, 0.18))
    sfx('key', 0.26, lambda b: notes(b, ['A5', 'E6'], 0.08, '0.125', 0.28, 0.18))
    sfx('unlock', 0.4, lambda b: (add_noise(b, 0, 0.05, 0.4), notes(b, ['C5', 'G5', 'C6'], 0.09, '0.25', 0.26, 0.2)))
    sfx('button', 0.1, lambda b: add_tone(b, 0, 620, 0.08, '0.5', 0.28, 300))
    sfx('throw', 0.16, lambda b: (add_noise(b, 0, 0.12, 0.2, 0.7), add_tone(b, 0, 700, 0.14, 'tri', 0.3, 1150)))
    sfx('kick', 0.09, lambda b: add_tone(b, 0, 260, 0.08, '0.5', 0.3, 560))
    sfx('checkpoint', 0.6, lambda b: notes(b, ['G5', 'B5', 'D6', 'G6'], 0.1, '0.25', 0.26, 0.28))
    sfx('bosshit', 0.3, lambda b: (add_noise(b, 0, 0.2, 0.4, 0.4), add_tone(b, 0, 320, 0.28, '0.5', 0.3, 70)))
    sfx('boom', 0.6, lambda b: (add_noise(b, 0, 0.58, 0.7, 0.12), add_tone(b, 0, 90, 0.4, 'sine', 0.5, 36)))
    sfx('slam', 0.26, lambda b: (add_noise(b, 0, 0.18, 0.5, 0.2), add_tone(b, 0, 130, 0.24, 'sine', 0.6, 46)))
    sfx('crumble', 0.3, lambda b: [add_noise(b, i * 0.07, 0.08, 0.35, 0.3) for i in range(4)])
    sfx('select', 0.06, lambda b: add_tone(b, 0, 660, 0.05, '0.25', 0.22))
    sfx('confirm', 0.2, lambda b: notes(b, ['E5', 'B5'], 0.07, '0.25', 0.24, 0.12))

    def deliver(b):
        notes(b, ['C5', 'E5', 'G5', 'C6', 'E6'], 0.11, '0.25', 0.24)
        add_tone(b, 0.55, freq('G6'), 0.7, '0.25', 0.24, vibrato=0.006)
        add_tone(b, 0.55, freq('E6'), 0.7, '0.125', 0.14)
        add_tone(b, 0.55, freq('C4'), 0.7, 'tri', 0.3)
    sfx('deliver', 1.3, deliver)


# name: (bpm, chords per bar, melody bars, drum bar, lead wave, arp volume, bass pattern)
TUNES = {
    'title': (84, 'C Am F G C Am F G',
              ['G5 - E5 - C5 - E5 -', 'A5 - - - E5 - C5 -', 'F5 - A5 - C6 - A5 -', 'G5 - - - D5 - - .',
               'G5 - E5 - C5 - E5 -', 'A5 - C6 - E6 - - -', 'D6 - C6 - A5 - F5 -', 'G5 - - - - - . .'],
              '........', 'tri', 0.13, 'x...x...'),
    'greenway': (132, 'G G C D G Em C D C D Em C G Em D G',
                 ['D5 . G5 . B5 A5 G5 .', 'B5 . A5 G5 E5 . D5 .', 'E5 . G5 . C6 B5 A5 .', 'A5 - F#5 . D5 E5 F#5 .',
                  'D5 . G5 . B5 A5 G5 .', 'B5 . D6 B5 G5 . E5 .', 'E5 G5 C6 . B5 A5 G5 .', 'A5 - - . D5 F#5 A5 .',
                  'C6 . C6 B5 A5 . G5 .', 'D6 . D6 C6 B5 . A5 .', 'E6 - D6 B5 G5 . B5 .', 'A5 G5 E5 . G5 - . .',
                  'D5 . G5 . B5 A5 G5 .', 'B5 . D6 B5 E6 . D6 .', 'C6 B5 A5 G5 F#5 E5 D5 .', 'G5 - - - . . . .'],
                 'k.h.s.h.', '0.25', 0.1, 'x.x.x.x.'),
    'saltpan': (118, 'E F E Dm E F Am E Am G F E Am G F E',
                ['E5 . G#5 A5 B5 . G#5 .', 'A5 . C6 A5 F5 . A5 .', 'B5 - G#5 E5 F5 E5 D5 .', 'D5 F5 A5 . F5 - E5 .',
                 'E5 . G#5 A5 B5 . D6 .', 'C6 . A5 C6 F6 - E6 .', 'E6 D6 C6 B5 A5 . C6 .', 'B5 - G#5 - E5 - . .',
                 'A5 . A5 B5 C6 . E6 .', 'D6 . B5 . G5 A5 B5 .', 'C6 . A5 . F5 G5 A5 .', 'G#5 - B5 - E6 - . .',
                 'A5 . A5 B5 C6 . E6 .', 'D6 . G6 . D6 B5 G5 .', 'F5 A5 C6 F6 E6 C6 A5 .', 'E5 - - - . . E5 .'],
                'k..hs.kh', '0.125', 0.09, 'x..x..x.'),
    'frostline': (104, 'Am F C G Am F C E F G Am Am F G C E',
                  ['E5 - A5 - C6 - B5 A5', 'A5 - - . C6 - A5 .', 'G5 - C6 - E6 - D6 C6', 'D6 - - . B5 - G5 .',
                   'E5 - A5 - C6 - B5 A5', 'A5 - C6 - F6 - E6 .', 'E6 - D6 C6 G5 - C6 .', 'B5 - - - G#5 - . .',
                   'A5 C6 F6 - E6 - C6 .', 'B5 D6 G6 - F6 - D6 .', 'C6 E6 A6 - G6 - E6 .', 'E6 - - - . . . .',
                   'A5 C6 F6 - E6 - C6 .', 'B5 D6 G6 - F6 - D6 .', 'E6 - C6 - G5 - C6 .', 'B5 - - - . . E5 .'],
                  'k.h.h.h.', 'tri', 0.12, 'x...x.x.'),
    'underhollow': (92, 'Cm Cm Ab G Cm Cm Fm G Ab Bb Cm Cm Ab Bb G G',
                    ['C5 . . Eb5 . . G5 .', 'F5 - Eb5 . D5 . . .', 'C5 . . Eb5 . . Ab5 .', 'G5 - - . B4 . D5 .',
                     'C5 . . Eb5 . . G5 .', 'Bb5 - Ab5 . G5 . . .', 'F5 . Ab5 . C6 . Ab5 .', 'G5 - - - . . . .',
                     'Eb5 . Ab5 . C6 - Bb5 .', 'D5 . F5 . Bb5 - Ab5 .', 'G5 . Eb5 . C5 - . .', '. . . . G4 . C5 .',
                     'Eb5 . Ab5 . C6 - Bb5 .', 'D5 . F5 . Bb5 - D6 .', 'D6 - B5 . G5 - . .', 'D5 . . . B4 . . .'],
                    'k.....h.', '0.5', 0.07, 'x..x.x..'),
    'boss': (150, 'Em Em C D Em Em C B',
             ['E5 E5 G5 E5 B5 . E5 .', 'E5 E5 G5 E5 A5 G5 F#5 .', 'C5 C5 E5 C5 G5 . C5 .', 'D5 D5 F#5 D5 A5 F#5 D5 .',
              'E5 E5 G5 E5 B5 . E6 .', 'D6 B5 G5 B5 E6 . D6 .', 'C6 . E6 . G6 E6 C6 .', 'B5 - D#6 - F#6 - . .'],
             'k.hks.hk', '0.25', 0.1, 'xxxxxxxx'),
    'story': (70, 'F Dm Bb C F Dm Bb C',
              ['A5 - - - C6 - - -', 'F5 - - - A5 - - -', 'D5 - - - F5 - - -', 'E5 - - - G5 - - .',
               'A5 - - - C6 - F6 -', 'D6 - - - A5 - - -', 'Bb5 - - - D6 - - -', 'C6 - - - - - . .'],
              '........', 'tri', 0.14, 'x.......'),
    'ending': (100, 'C Am F G C Am F G F G Em Am F G C C',
               ['G5 - E5 - C5 - E5 G5', 'A5 - - . E5 - C6 -', 'A5 - F5 - C6 - A5 -', 'G5 - - . D5 E5 F5 G5',
                'G5 - E5 - C6 - E6 -', 'A5 - C6 - E6 - - .', 'D6 - C6 - A5 - F5 -', 'G5 - - - B5 - D6 -',
                'C6 - A5 - F5 - A5 -', 'D6 - B5 - G5 - B5 -', 'E6 - D6 - B5 - G5 -', 'A5 - - - C6 - E6 -',
                'F6 - E6 - C6 - A5 -', 'G6 - F6 - D6 - B5 -', 'C6 - - - E6 - G6 -', 'C6 - - - - - . .'],
               'k.h.s.h.', '0.25', 0.1, 'x...x.x.'),
}


def make_tune(name):
    bpm, chords, bars, drums, lead, arp_vol, bass_pattern = TUNES[name]
    chords = chords.split()
    eighth = 60 / bpm / 2
    bar = eighth * 8
    buf = [0.0] * int(bar * len(bars) * SR)
    for b, line in enumerate(bars):
        t0 = b * bar
        tokens = line.split()
        i = 0
        while i < 8:
            token = tokens[i]
            length = 1
            while i + length < 8 and tokens[i + length] == '-':
                length += 1
            if token not in '.-':
                add_tone(buf, t0 + i * eighth, freq(token), length * eighth * 0.95, lead, 0.22,
                         vibrato=0.005, sustain=0.55)
                add_tone(buf, t0 + i * eighth + eighth * 1.5, freq(token), eighth * 0.6, lead, 0.035)   # echo
            i += length
        tones = chord(chords[b], 4)
        low = chord(chords[b], 2)[0]
        for i in range(8):
            add_tone(buf, t0 + i * eighth, tones[(0, 1, 2, 1, 0, 1, 2, 1)[i]], eighth * 0.8, '0.125', arp_vol,
                     sustain=0.3)
            if bass_pattern[i] == 'x':
                add_tone(buf, t0 + i * eighth, low * (1.5 if i == 6 and bass_pattern != 'xxxxxxxx' else 1),
                         eighth * 1.6, 'tri', 0.34, sustain=0.7)
            hit = drums[i]
            if hit == 'k':
                add_tone(buf, t0 + i * eighth, 130, 0.11, 'sine', 0.5, 45)
            elif hit == 's':
                add_noise(buf, t0 + i * eighth, 0.13, 0.3, 0.6)
            elif hit == 'h':
                add_noise(buf, t0 + i * eighth, 0.04, 0.12, 0.95)
    save('music_' + name, buf, 0.55, 0.7)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    make_sfx()
    for tune in TUNES:
        make_tune(tune)
