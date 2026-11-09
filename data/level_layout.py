"""Editable placement data for World 1-1, in logical screen pixels."""

from . import constants as c


GROUND_RECTS = (
    (0, c.GROUND_HEIGHT, 2953, 60),
    (3048, c.GROUND_HEIGHT, 635, 60),
    (3819, c.GROUND_HEIGHT, 2735, 60),
    (6647, c.GROUND_HEIGHT, 2300, 60),
)

PIPE_RECTS = (
    (1202, 452, 83, 82), (1631, 409, 83, 140),
    (1973, 366, 83, 170), (2445, 366, 83, 170),
    (6989, 452, 83, 82), (7675, 452, 83, 82),
)

STEP_RECTS = (
    (5745, 495, 40, 44), (5788, 452, 40, 44),
    (5831, 409, 40, 44), (5874, 366, 40, 176),
    (6001, 366, 40, 176), (6044, 408, 40, 40),
    (6087, 452, 40, 40), (6130, 495, 40, 40),
    (6345, 495, 40, 40), (6388, 452, 40, 40),
    (6431, 409, 40, 40), (6474, 366, 40, 40),
    (6517, 366, 40, 176), (6644, 366, 40, 176),
    (6687, 408, 40, 40), (6728, 452, 40, 40),
    (6771, 495, 40, 40), (7760, 495, 40, 40),
    (7803, 452, 40, 40), (7845, 409, 40, 40),
    (7888, 366, 40, 40), (7931, 323, 40, 40),
    (7974, 280, 40, 40), (8017, 237, 40, 40),
    (8060, 194, 40, 40), (8103, 194, 40, 360),
    (8488, 495, 40, 40),
)

# Each brick or box is (x, y, contents). None is an ordinary brick.
BRICKS = (
    (858, 365, None), (944, 365, None), (1030, 365, None),
    (3299, 365, None), (3385, 365, None),
    (3430, 193, None), (3473, 193, None),
    (3516, 193, None), (3559, 193, None),
    (3602, 193, None), (3645, 193, None),
    (3688, 193, None), (3731, 193, None),
    (3901, 193, None), (3944, 193, None),
    (3987, 193, None), (4030, 365, c.SIXCOINS),
    (4287, 365, None), (4330, 365, c.STAR),
    (5058, 365, None), (5187, 193, None),
    (5230, 193, None), (5273, 193, None),
    (5488, 193, None), (5574, 193, None),
    (5617, 193, None), (5531, 365, None),
    (5574, 365, None), (7202, 365, None),
    (7245, 365, None), (7331, 365, None),
)

COIN_BOXES = (
    (685, 365, c.COIN), (901, 365, c.MUSHROOM),
    (987, 365, c.COIN), (943, 193, c.COIN),
    (3342, 365, c.MUSHROOM), (4030, 193, c.COIN),
    (4544, 365, c.COIN), (4672, 365, c.COIN),
    (4672, 193, c.MUSHROOM), (4800, 365, c.COIN),
    (5531, 193, c.COIN), (7288, 365, c.COIN),
)

FLAG_POLE_X = 8505
FLAG_POLE_SEGMENTS = (97, 137, 177, 217, 257, 297,
                      337, 377, 417, 450)

# Enemy waves are spawned when Mario crosses their matching checkpoints.
ENEMY_WAVES = (
    ((c.GOOMBA, c.GROUND_HEIGHT),),
    ((c.GOOMBA, c.GROUND_HEIGHT),),
    ((c.GOOMBA, c.GROUND_HEIGHT), (c.GOOMBA, c.GROUND_HEIGHT)),
    ((c.GOOMBA, 193), (c.GOOMBA, 193)),
    ((c.GOOMBA, c.GROUND_HEIGHT), (c.GOOMBA, c.GROUND_HEIGHT)),
    ((c.KOOPA, c.GROUND_HEIGHT),),
    ((c.GOOMBA, c.GROUND_HEIGHT), (c.GOOMBA, c.GROUND_HEIGHT)),
    ((c.GOOMBA, c.GROUND_HEIGHT), (c.GOOMBA, c.GROUND_HEIGHT)),
    ((c.GOOMBA, c.GROUND_HEIGHT), (c.GOOMBA, c.GROUND_HEIGHT)),
    ((c.GOOMBA, c.GROUND_HEIGHT), (c.GOOMBA, c.GROUND_HEIGHT)),
)

# (x, name, y, width, height)
CHECKPOINTS = (
    (510, "1", 0, 10, 600), (1400, "2", 0, 10, 600),
    (1740, "3", 0, 10, 600), (3080, "4", 0, 10, 600),
    (3750, "5", 0, 10, 600), (4150, "6", 0, 10, 600),
    (4470, "7", 0, 10, 600), (4950, "8", 0, 10, 600),
    (5100, "9", 0, 10, 600), (6800, "10", 0, 10, 600),
    (8504, "11", 5, 6, 600), (8775, "12", 0, 10, 600),
    (2740, "secret_mushroom", 360, 40, 12),
)
