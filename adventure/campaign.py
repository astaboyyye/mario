"""Hand-authored campaign. Coordinates are metres on the X/Z play plane."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Stage:
    name: str
    place: str
    speaker: str
    briefing: str
    objective: str
    ending: str
    theme: str
    ground: tuple
    platforms: tuple
    movers: tuple
    switches: tuple
    enemies: tuple
    medals: tuple
    checkpoint: float
    exit: float


STAGES = (
    Stage('A dry start', '01 / APPLEWATER ORCHARD', 'TOAD, stationmaster',
          'Bowser Jr. took the festival train! He shut the orchard sluice on his way out. Turn both wheels so our spare engine can fill its tank.',
          'Turn both water wheels with E',
          'Water is flowing! The spare engine is ready. The quarry crew saw the train heading uphill.',
          'orchard', ((-8,23,0),(27,51,0),(57,84,0)),
          ((10,14,2),(18,22,3.5),(23,27,-.4),(33,38,2),(44,48,3.5),(51,57,-.4),(61,66,2),(69,74,4)),
          (), ((20,4.0),(72,4.5)), ((31,39),(59,67),(76,81)),
          ((13,3.1),(46,4.6),(64,3.1)), 39, 80),
    Stage('The long way up', '02 / SWITCHBACK QUARRY', 'CAPTAIN TOAD',
          'Jr. pulled the lift brakes. Those crates will never reach the track. Ride the lifts and release both brake levers. Mind the gaps!',
          'Ride the lifts; release both brakes with E',
          'The track is clear. One problem: Jr. has barricaded the foundry. Take the service line.',
          'quarry', ((-8,19,0),(25,41,1),(47,65,0),(71,91,1)),
          ((10,15,2),(30,35,4),(52,58,3),(76,81,5)),
          ((19,24,1,0,3,2.0),(41,46,2,0,3,1.7),(65,70,2,0,3,1.5)),
          ((33,4.5),(79,5.5)), ((27,38),(49,61),(73,86)),
          ((13,3.1),(55,4.1),(79,6.2)), 37, 87),
    Stage('Wrong-way works', '03 / COPPERPIPE FOUNDRY', 'LUIGI, over the radio',
          'I found the service door. Jr. wired the belts backwards! Hit the two fuse boxes with Z, then meet me at the freight platform.',
          'Use Z near both fuse boxes to reverse the belts',
          'Nice work! I uncoupled a freight car. Hop on; we can catch the train before it reaches Starfall Bridge.',
          'foundry', ((-8,22,0),(27,49,0),(54,78,0),(83,100,0)),
          ((12,17,2.5),(32,38,3),(43,47,5),(60,66,2.5),(72,77,4),(86,91,2)),
          ((22,27,1,0,1.5,2),(49,54,1,0,1.5,2),(78,83,1,0,1.5,2)),
          ((35,3.5),(74,4.5)), ((10,20),(30,43),(57,69),(86,95)),
          ((15,3.6),(45,6.1),(89,3.1)), 40, 96),
    Stage('Tickets, please!', '04 / THE SKY EXPRESS', 'LUIGI',
          'We caught up! The front carriage is locked. Grab the conductor keys from the two guards. Z knocks them off balance; jumping works too.',
          'Defeat both key guards and reach the front carriage',
          'The keys fit. Jr. is up front, feeding the stolen Power Star into his engine. Time to pull the brakes.',
          'train', ((-8,17,0),(22,40,0),(46,65,0),(71,91,0)),
          ((8,14,2),(26,33,2.5),(49,56,2),(75,83,2.5)),
          ((17,22,0,0,1,2),(40,46,0,0,1.4,2),(65,71,0,0,1,2)),
          ((30,3),(79,3)), ((24,36),(73,85)),
          ((11,3.2),(52,3.2),(81,3.7)), 36, 87),
    Stage('End of the line', '05 / STARFALL ENGINE', 'BOWSER JR.',
          'The festival can wait. This is MY train now! ...Hey! Keep your hands off those steam valves!',
          'Vent both valves with Z, then hit Jr. three times',
          'The brakes hold. Mario returns the Power Star, and the first train rolls into Starfall just as the festival lights come on. Luigi saved you a seat.',
          'citadel', ((-8,24,0),(29,50,0),(55,91,0)),
          ((10,16,2.5),(33,39,3),(60,66,2)),
          ((24,29,1,0,2,1.6),(50,55,1,0,2,1.6)),
          ((13,3),(36,3.5)), ((31,44),(58,69)),
          ((13,3.7),(37,4.2),(80,3.2)), 59, 86),
)
