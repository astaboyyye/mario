"""All story text: the route, the twelve letters and the scenes between them."""

WORLDS = ('Greenway', 'Saltpan', 'Frostline', 'Underhollow', 'Lanternhead')

# id, world, level title, addressee, their trade, letter, postscript (needs all three gems)
ROUTE = [
    ('w1_1', 0, 'First Round', 'Bram Thistle', 'bridge-keeper',
     "Bram,\nThe lamp is out. Before you reach for your boots: no, I don't need the bridge closed, and no, "
     "I don't need you to catch anyone. I need your storm lantern, the ugly brass one, on my hill by the "
     "Longest Night. Bring it lit.\nM.",
     "The carrier is new. Be kind. You fell off that bridge twice in your first week."),
    ('w1_2', 0, 'Shell Game', 'Odile Fenn', 'snail-herd',
     "Odile,\nYou told me once that a light is only a promise that somebody is awake. I have kept that "
     "promise for forty years. I am asking you to keep it for one night. Bring whatever burns.\nM.",
     "Your snails ate my cabbages again. I have decided I don't mind."),
    ('w1_3', 0, 'Loose Planks', 'Hesper and Wren Plank', 'bridge-wrights',
     "Hesper, Wren,\nDo you remember the child who used to sit on the rocks below the tower, just at the "
     "edge of the beam? I never asked where they came from. I am ashamed how long it took me to wonder. "
     "Bring your lamps.\nM.",
     "The planks on the old bridge are rotten. You both know this. Fix it."),
    ('w2_1', 1, 'Needle Flats', 'Cass Ardent', 'well-digger',
     "Cass,\nYou dig down for a living, so tell me honestly: how dark is it under the mountain? I have lit "
     "the sea for forty years and never once turned the lamp inland. Bring a light. And an answer.\nM.",
     "Mind the needles. They only come up when it's quiet."),
    ('w2_2', 1, "Locksmith's Well", 'Ibrahim Quill', 'locksmith',
     "Ibrahim,\nYou will hear the tower door was forced. It wasn't. I have left it unlocked every night "
     "for six years, because someone small kept coming to watch the lamp turn and I didn't want them to "
     "have to knock. Bring a lantern. Leave your locks at home.\nM.",
     "Yes, I know what you'll say about unlocked doors. I would do it again."),
    ('w2_3', 1, 'Red Tide, Blue Tide', 'Tamsin Roe', 'tide-reader',
     "Tamsin,\nI watched them take it, you know. I was on the stairs. They looked at me and I looked at "
     "them and neither of us said a word. I could have said 'stay'. I have been turning that over ever "
     "since. Bring a light.\nM.",
     "The lens weighs more than they do. They carried it anyway. Think about that."),
    ('w3_1', 2, 'Cold Feet', 'Old Pell', 'mountain guide',
     "Pell,\nYou have walked the pass more than anyone. Is it true there are doors in the mountain? Whole "
     "streets under the snow, and people who have never seen a sunrise? Why did none of us ever go and "
     "knock? Bring your lamp.\nM.",
     "Wear the good coat. I am not burying you in the bad one."),
    ('w3_2', 2, 'The Stone Faces', 'Sister Aldous', 'bell-ringer',
     "Aldous,\nRing the bell on the Longest Night. Ring it so they hear it underground. I don't know if "
     "sound carries that far down. I don't know if light does either. We are going to find out.\nM.",
     "The stone faces in the pass aren't angry. They have just been alone a long time."),
    ('w3_3', 2, 'Summit Lift', 'Yusra Vane', 'lift-keeper',
     "Yusra,\nFrom your summit you can see my tower and the mountain gate at once. Has anyone ever drawn a "
     "line between them? A lamp only shines where you point it. I pointed it at the sea.\nM.",
     "The carrier will want to go down after the thief. Let them. They have one more letter than you think."),
    ('w4_1', 3, 'The Gate Below', 'The Gatekeeper', 'of the Underhollow',
     "To whoever keeps the gate,\nWe haven't met. That is my fault, not yours. My name is Marigold. I keep "
     "a lamp on the hill above you. I would like to come down and say hello. May I?\nM.",
     "I'm told you have no word for 'morning'. I would like to hear what you say instead."),
    ('w4_2', 3, 'The Mirror Works', 'The Foreman', 'of the Mirror Works',
     "To the foreman,\nI'm told you make mirrors, fine ones, to pass what little glow you have from hall "
     "to hall. I have an idea involving your mirrors and a hundred lamps. It will need both of us.\nM.",
     "Nobody above knows how to build what you have built. They should."),
    ('w4_3', 3, 'The Lamp Room', 'The one who took it', '',
     "To the one who took it,\nYou could have asked. But I never offered, and that is the older fault. "
     "Keep the lens. It was only ever glass. On the Longest Night, look up the shaft above your lamp room. "
     "We are bringing you the rest.\nMarigold",
     "The tower door is still unlocked. It always will be. You never did tell me your name."),
    ('w5_1', 4, 'The Longest Night', '', '', '', ''),
]

INTRO = [
    ('tower_lit', "For a hundred years the lamp at Lanternhead has turned every night. Ships steer by it. "
                  "Children fall asleep by it."),
    ('tower_dark', "Last night it went dark. Someone climbed the tower and carried off the great lens."),
    ('letters', "This morning the keeper, Marigold Wick, handed twelve letters to the valley's newest post "
                "carrier. That's you, Juno. It is your first week."),
    ('juno', "\"Don't chase the thief,\" she said. \"Just deliver these. Every one. In order.\""),
]

# Shown after the letter for the given level.
AFTER = {
    'w1_3': [('rook_run', "On the far bank, someone small and pink is running flat out, with something "
                          "bright tucked under one arm."),
             ('rook_run', "They glance back once. They don't look like a thief. They look like someone "
                          "who is late getting home.")],
    'w2_3': [('desert', "Tracks in the salt: small, quick, heading for the mountains. Whoever it is, "
                        "they are carrying something heavy and not putting it down.")],
    'w3_3': [('rook_face', "\"Go HOME, postie!\" The thief stands at the mountain gate, hugging the lens. "
                           "\"You've had it a hundred years. It's ours now!\""),
             ('rook_face', "\"I'm not here for the lens,\" you start to say. But the gate has already "
                           "slammed. Three letters left. All of them are addressed below.")],
    'w4_3': [('rook_letter', "Rook reads it twice. Then a third time, slower."),
             ('rook_letter', "\"She's not... she isn't angry?\" A long pause. \"My name's Rook. "
                             "Nobody up there ever asked.\"")],
}

BOSS_OPEN = "\"YOU again! I told you, it's OURS. Do you know how long a hundred years is in the dark?\""
BOSS_END = "\"Fine! Take it. Take it back...\" But you aren't reaching for the lens. You're holding out an envelope."

ENDING = [
    ('night_lamps', "On the Longest Night they came up the hill one by one. A brass storm lantern. Two "
                    "bridge lamps. A bell you could hear in your teeth."),
    ('night_lamps', "The foreman's mirrors went down the shaft, hall after hall, and the hundred small "
                    "lights of the valley went down with them."),
    ('tower_lit', "Rook carried the lens back up before dawn and set it at the mountain gate instead, "
                  "where it could face both ways."),
    ('juno', "Twelve letters, twelve doors. Not bad for a first week.\n\nTHE END"),
]

# Things the valley says to you on the walk up the hill.
EPILOGUE_LINES = [
    "BRAM: Ugly brass lantern, as ordered. Lit. Tell her I only fell in once.",
    "ODILE: A promise that somebody is awake. Well. Here I am, awake.",
    "HESPER: We fixed the bridge. WREN: She fixed the bridge. I held the nails.",
    "CASS: How dark is it down there? Darker than she thinks. Not for much longer.",
    "IBRAHIM: I left my locks at home. I feel undressed.",
    "TAMSIN: She said 'stay' in the end. Took her a letter to do it.",
    "PELL: The good coat. Don't tell her it itches.",
    "ALDOUS: They heard the bell. They rang something back.",
    "YUSRA: A straight line from the tower to the gate. Look at it.",
    "ROOK: It's so BRIGHT up here. How do you people sleep?",
    "MARIGOLD: All twelve. In order. I knew you would. Go on up, Juno. The door's unlocked.",
]

CONTROLS = [
    ('Arrows / A D', 'Move'), ('Space / Z', 'Jump, hold to go higher'), ('Shift / X', 'Run, throw'),
    ('Up / Down', 'Ladders; Down + Jump drops through ledges'), ('R', 'Back to checkpoint'),
    ('Esc', 'Pause'), ('M', 'Mute'), ('F11', 'Fullscreen'),
]


def index_of(level_id):
    return [r[0] for r in ROUTE].index(level_id)
