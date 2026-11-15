"""Shared constants. Distances are pixels, speeds pixels per second."""
import os
import sys

W, H = 1280, 720
TILE = 48
FPS = 60
DT = 1 / FPS

# Movement. Tuned so a standing jump clears 4 tiles and a running jump ~4.7.
WALK_SPEED = 300
RUN_SPEED = 460
ACCEL_GROUND = 2300
ACCEL_AIR = 1500
FRICTION = 2600
SKID = 4400
GRAVITY = 2600
GRAVITY_HELD = 1500      # rising with jump held: floatier, gives variable height
GRAVITY_CUT = 4800       # rising with jump released: short hop
MAX_FALL = 900
JUMP_SPEED = 760
JUMP_RUN_BONUS = 0.13    # extra lift per px/s of horizontal speed
COYOTE = 0.10
JUMP_BUFFER = 0.12
STOMP_BOUNCE = 430
SPRING_SPEED = 1150
SPRING_GRAVITY = 2000
GLIDE_FALL = 120
GLIDE_TIME = 1.7
DOUBLE_JUMP = 700
CLIMB_SPEED = 200
MAX_HEARTS = 3

if getattr(sys, 'frozen', False):
    ROOT = sys._MEIPASS
    SAVE_DIR = os.path.dirname(sys.executable)
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SAVE_DIR = ROOT
ART = os.path.join(ROOT, 'resources', 'quest_pack')
AUDIO = os.path.join(ROOT, 'resources', 'lantern_audio')
FONTS = os.path.join(ROOT, 'resources', 'fonts')
LEVELS = os.path.join(ROOT, 'lantern', 'levels')
SAVE_FILE = os.path.join(SAVE_DIR, 'lantern-save.json')

INK = (52, 44, 60)
PAPER = (250, 243, 224)
GOLD = (255, 204, 0)
