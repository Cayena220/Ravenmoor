"""Castle Grounds landmarks from the design plan (docs/Original-design-plan.txt), blocked out in the build kit: the
greenhouses where students gather herbs, the groundskeeper's hut, the Ruins of Old Ravenmoor where the House War is
fought, and the flying pitch, empty at launch, for the flying sport to come. They are plain parts at full size, to
walk and judge before any detail. tools/layout.py stands them on the land between the village, the academy and the
forest (GROUNDS).

build() takes a landmark's name, its centre and the point on a road where its gravel path starts, which must line
up with the landmark's entrance in x or z. Points are Roblox studs, (x, z) across the ground.
"""
import math
import random
from build import HOUSE_COLORS, TRIM, frange, label, light, model, part, sign, timber_house
from palette import (BEAM, BRICK, CASTLE_STONE, CLEAR_GLASS, COURSE, DOOR, GOLD, HEDGE, IRON, LAMPLIGHT, LIMESTONE,
                     PATH, PLANK, ROCK, RUNESTONE, SIGNBOARD, SLATE, TRUNK, WEATHERED)

HERBS = ((86, 128, 72), (112, 146, 84), (132, 112, 168), (198, 168, 84))   # herb leaves and flowers
PITCH = (96, 136, 84)                                                     # mown grass, brighter than the meadow
UPRIGHT = {'shape': 2, 'roll': math.pi / 2}                               # a cylinder standing on end


def lantern(parent, x, y, z, reach=16):
    light(part(parent, 'Lantern', (x, y, z), (0.7, 1, 0.7), LAMPLIGHT, 'Glass', **TRIM), 1.2, reach)


def signpost(parent, x, z, title, subtitle):
    """A board on two posts facing north and south, lettered on both faces, with a nameplate over it."""
    for dx in (-2.4, 2.4): part(parent, 'Sign post', (x + dx, 2.6, z), (0.4, 5.2, 0.4), BEAM, 'Wood')
    board = part(parent, 'Sign', (x, 4.4, z), (5.6, 2.2, 0.25), SIGNBOARD, 'Wood')
    sign(board, title); sign(board, title, face=2)
    label(board, title, subtitle, 4, 90)


def path(parent, a, b, width=5):
    """A gravel path from a to b, which share x or z."""
    (ax, az), (bx, bz) = a, b
    assert ax == bx or az == bz, f'a path runs straight along x or z: {a} to {b}'
    size = (width, 0.1, abs(bz - az)) if ax == bx else (abs(bx - ax), 0.1, width)
    part(parent, 'Gravel path', ((ax + bx) / 2, 0.05, (az + bz) / 2), size, PATH, 'Sand')


def greenhouses(parent, cx, cz):
    """Three glasshouses in a row, doors north, with potting benches of herbs inside, raised herb beds before
    them, a potting shed and water butts. Returns the model and its entrance."""
    m = model(parent, 'Greenhouses'); rng = random.Random(41)
    for i in (-1, 0, 1):
        x = cx + 36 * i; x0, x1, z0, z1 = x - 15, x + 15, cz - 9, cz + 9
        g = model(m, f'Glasshouse {i + 2}')
        part(g, 'Plinth', (x, 0.6, cz), (31, 1.2, 19), BRICK, 'Brick')
        for z in (z0, z1): part(g, 'Glass wall', (x, 5.2, z), (30, 8, 0.2), CLEAR_GLASS, 'Glass', transparent=0.45)
        for wx in (x0, x1): part(g, 'Glass wall', (wx, 5.2, cz), (0.2, 8, 18), CLEAR_GLASS, 'Glass', transparent=0.45)
        for wx in frange(x0, x1, 5):
            for z in (z0, z1): part(g, 'Frame post', (wx, 5.2, z), (0.4, 8, 0.4), BEAM, 'Wood')
        for z, yaw in ((cz - 4.75, 0), (cz + 4.75, math.pi)):   # a glass gable roof along x, as roof() lays slate
            part(g, 'Glass roof', (x, 11.95, z), (31, 5.5, 9.5), CLEAR_GLASS, 'Glass', yaw=yaw, transparent=0.45, cls='WedgePart')
        part(g, 'Ridge', (x, 14.85, cz), (31.4, 0.4, 0.6), BEAM, 'Wood', **TRIM)
        part(g, 'Door', (x, 4.4, z0 - 0.2), (4, 6.4, 0.3), DOOR, 'WoodPlanks')
        for z in (z0 + 2.5, z1 - 2.5):
            part(g, 'Potting bench', (x, 2.6, z), (26, 0.4, 3), PLANK, 'WoodPlanks')
            for hx in frange(x0 + 2.5, x1 - 2.5, 3):
                part(g, 'Herb', (hx, 3.5, z), (1.5, 1.5, 1.5), rng.choice(HERBS), 'LeafyGrass', shape=0, **TRIM)
    # Raised beds along a cross path in front, and the path down from the forest path.
    front = cz - 21
    path(m, (cx - 54, front), (cx + 54, front))
    for bx in frange(cx - 48, cx + 48, 12):
        if abs(bx - cx) < 4: continue
        for bz in (front - 6, front + 6 - 0.5):
            part(m, 'Herb bed', (bx, 0.6, bz), (9, 1.2, 3), BRICK, 'Brick')
            for hx in (bx - 3, bx, bx + 3): part(m, 'Herb', (hx, 1.9, bz), (2, 1.6, 2), rng.choice(HERBS), 'LeafyGrass', shape=0, **TRIM)
    # The potting shed and water butts at the east end.
    sx = cx + 62
    part(m, 'Potting shed', (sx, 3.5, cz), (8, 7, 10), PLANK, 'WoodPlanks')
    part(m, 'Shed roof', (sx, 7.75, cz), (11, 1.5, 9), SLATE, 'Slate', yaw=math.pi / 2, cls='WedgePart')   # falls west
    part(m, 'Shed door', (sx - 4.1, 3.2, cz), (0.3, 6, 3.6), DOOR, 'WoodPlanks')
    for bz in (cz - 8, cz + 8):
        part(m, 'Water butt', (sx - 1, 1.6, bz), (3.2, 3.2, 3.2), BEAM, 'Wood', **UPRIGHT)
    signpost(m, cx + 6, cz - 58, 'GREENHOUSES', 'Herbology · gather herbs')
    return m, (cx, front - 2.5)


HUT = {'w': 14, 'd': 12, 'heights': (7,), 'door': (4, 6.2), 'pitch': 6.5, 'ground': 'stone',
       'plaster': (229, 214, 188), 'roof': (86, 64, 58), 'shutter': (92, 120, 84),
       'windows': ([('front', -4.6, 2.4, 2.4), ('front', 4.6, 2.4, 2.4), ('left', 0, 2.2, 2.2), ('right', 0, 2.2, 2.2),
                    ('back', 0, 2.4, 2.2)],)}


def hut(parent, cx, cz):
    """Tobb's stone cottage at the edge of Whisperwood, door north, with a fenced vegetable plot, a woodpile, a pen
    for the beasts he studies and a lantern by the path. Returns the model and its entrance."""
    m = model(parent, "Groundskeeper's hut"); rng = random.Random(23)
    timber_house(m, 'Cottage', cx, cz, '-Z', HUT)

    def fence(x0, x1, z0, z1, gate=None):
        """Posts and two rails round x0..x1, z0..z1, with a gate 4 wide at gate = (x, z) on the west or east side."""
        for z in (z0, z1):
            for x in frange(x0, x1, 3): part(m, 'Fence post', (x, 1.6, z), (0.4, 3.2, 0.4), BEAM, 'Wood')
            for y in (1.2, 2.6): part(m, 'Fence rail', ((x0 + x1) / 2, y, z), (x1 - x0, 0.25, 0.25), BEAM, 'Wood', **TRIM)
        for x in (x0, x1):
            for z in frange(z0, z1, 3): part(m, 'Fence post', (x, 1.6, z), (0.4, 3.2, 0.4), BEAM, 'Wood')
            for y in (1.2, 2.6):
                runs = [(z0, z1)] if gate is None or x != gate[0] else [(z0, gate[1] - 2), (gate[1] + 2, z1)]
                for a, b in runs: part(m, 'Fence rail', (x, y, (a + b) / 2), (0.25, 0.25, b - a), BEAM, 'Wood', **TRIM)

    # The vegetable plot east of the cottage, its gate on the path side.
    fence(cx + 11, cx + 27, cz - 7, cz + 7, gate=(cx + 11, cz - 3))
    for vx in frange(cx + 13.5, cx + 25, 3):
        for vz in (cz - 4, cz, cz + 4):
            part(m, 'Cabbage', (vx, 0.7, vz), (1.6, 1.3, 1.6), rng.choice((HEDGE, HERBS[0], HERBS[1])), 'LeafyGrass', shape=0, **TRIM)
    # The beast pen behind, with a trough and straw.
    fence(cx - 9, cx + 9, cz + 9, cz + 23)
    part(m, 'Trough', (cx, 0.7, cz + 16), (6, 1.4, 1.6), BEAM, 'Wood')
    for k in range(4):
        part(m, 'Straw', (cx - 5 + 3.2 * k, 0.4, cz + 20.5), (2.6, 0.8, 2), (196, 170, 102), 'Fabric', **TRIM)
    # A woodpile against the west wall, logs lying north to south, and the chopping block.
    for level in range(3):
        for k in range(4 - level):
            part(m, 'Log', (cx - 8 - 1.05 * k - 0.52 * level, 0.5 + 0.9 * level, cz - 2), (4, 1, 1), TRUNK, 'Wood', shape=2, yaw=math.pi / 2)
    part(m, 'Chopping block', (cx - 10, 0.8, cz - 8), (1.6, 1.8, 1.8), TRUNK, 'Wood', **UPRIGHT)
    door = (cx, cz - 7.5)
    part(m, 'Lamp post', (cx + 3.5, 3, door[1] - 4), (0.35, 6, 0.35), IRON, 'Metal')
    lantern(m, cx + 3.5, 6.4, door[1] - 4)
    signpost(m, cx - 6, door[1] - 10, 'GROUNDSKEEPER', 'Tobb Brambleworth · beast lore')
    return m, door


def ruins(parent, cx, cz):
    """The Ruins of Old Ravenmoor: a breached curtain wall round a court 120 × 110 with stumps of corner towers, the
    shell of the old keep and its broken tower, a colonnade of fallen columns, rubble, and the House War's three
    control points. The gate is south. Returns the model and its entrance."""
    m = model(parent, 'Ruins of Old Ravenmoor'); rng = random.Random(77)
    w, d = 120, 110; x0, x1, z0, z1 = cx - w / 2, cx + w / 2, cz - d / 2, cz + d / 2
    part(m, 'Old flagstones', (cx, 0.15, cz), (w - 6, 0.3, d - 6), COURSE, 'Slate')

    def wall(axis, at, a, b, gaps, thick=3):
        """Broken wall from a to b along `axis`: blocks 5 to 8 long, some fallen to their footings, none in `gaps`."""
        t = a
        while t < b - 0.5:
            n = min(rng.uniform(5, 8), b - t); mid = t + n / 2
            stand, h = rng.random(), rng.uniform(3, 13)
            if stand > 0.18 and not any(g0 <= mid <= g1 for g0, g1 in gaps):
                h = h if stand > 0.45 else rng.uniform(1.2, 3)
                pos, size = ((mid, h / 2, at), (n, h, thick)) if axis == 'x' else ((at, h / 2, mid), (thick, h, n))
                part(m, 'Curtain wall', pos, size, rng.choice((CASTLE_STONE, CASTLE_STONE, WEATHERED)), 'Slate')
            t += n

    wall('x', z1, x0, x1, [(cx - 8, cx + 8)])        # south, the gate
    wall('x', z0, x0, x1, [(x0, x0 + 18)])           # north, breached at the west end, toward the forest road
    wall('z', x0, z0, z1, [(cz + 8, cz + 18)])
    wall('z', x1, z0, z1, [(cz - 6, cz + 6)])        # east, breached toward the academy road
    for x, z in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        h = rng.uniform(8, 18)
        part(m, 'Tower stump', (x, h / 2, z), (h, 12, 12), WEATHERED, 'Slate', **UPRIGHT)
    for side in (-1, 1): part(m, 'Gate pier', (cx + side * 9.5, 8, z1), (4, 16, 4), CASTLE_STONE, 'Slate')
    part(m, 'Broken lintel', (cx - 6, 16.6, z1), (11, 1.4, 4), LIMESTONE, 'Limestone')
    # The keep: a roofless shell 30 × 26 at the north of the court, doorway south, and its broken north-east tower.
    kx, kz = cx, z0 + 22
    wall('x', kz - 13, kx - 15, kx + 15, [], 2.5); wall('x', kz + 13, kx - 15, kx + 15, [(kx - 3, kx + 3)], 2.5)
    wall('z', kx - 15, kz - 13, kz + 13, [], 2.5); wall('z', kx + 15, kz - 13, kz + 13, [], 2.5)
    part(m, 'Keep tower', (kx + 15, 15, kz - 13), (30, 12, 12), CASTLE_STONE, 'Slate', **UPRIGHT)
    for k in range(5):   # a jagged crown where the tower broke
        a = k * math.tau / 5 + 0.4; h = rng.uniform(1.5, 5)
        part(m, 'Tower crown', (kx + 15 + 4.6 * math.cos(a), 30 + h / 2, kz - 13 + 4.6 * math.sin(a)), (3, h, 3), CASTLE_STONE, 'Slate', yaw=a)
    # A colonnade up the court from the gate to the keep: standing columns, stumps and fallen drums.
    for side in (-1, 1):
        for z in frange(kz + 22, z1 - 14, 10):
            x, kind = cx + side * 11, rng.random()
            if kind < 0.25:
                part(m, 'Column', (x, 7, z), (14, 2.4, 2.4), LIMESTONE, 'Limestone', **UPRIGHT)
                part(m, 'Capital', (x, 14.5, z), (3.2, 1, 3.2), LIMESTONE, 'Limestone')
            elif kind < 0.75:
                h = rng.uniform(1.5, 6)
                part(m, 'Column stump', (x, h / 2, z), (h, 2.4, 2.4), LIMESTONE, 'Limestone', **UPRIGHT)
            else:
                part(m, 'Fallen column', (x + side * 5, 1.2, z), (10, 2.4, 2.4), LIMESTONE, 'Limestone', shape=2, yaw=rng.uniform(-0.6, 0.6))
    for _ in range(26):
        x, z, s = rng.uniform(x0 + 4, x1 - 4), rng.uniform(z0 + 4, z1 - 4), rng.uniform(1.5, 4)
        if abs(x - cx) < 6: continue   # keep the colonnade's walk clear
        part(m, 'Rubble', (x, s * 0.35, z), (s, s * 0.7, s * 1.2), rng.choice((ROCK, WEATHERED, CASTLE_STONE)), 'Rock', shape=0)
    # The House War's control points, west, middle and east.
    for letter, (px, pz) in zip('ABC', ((x0 + 22, cz + 12), (cx, cz + 6), (x1 - 22, cz + 12))):
        part(m, 'Control ring', (px, 0.36, pz), (0.08, 14, 14), RUNESTONE, 'Neon', **UPRIGHT, **TRIM)
        part(m, 'Control stone', (px, 0.38, pz), (0.1, 12.6, 12.6), SLATE, 'Slate', **UPRIGHT, **TRIM)
        stone = part(m, 'Control obelisk', (px, 3.8, pz), (2, 7, 2), RUNESTONE, 'Slate')
        label(stone, f'CONTROL POINT {letter}', 'House War', 6, 90)
        lantern(m, px, 7.8, pz)
    signpost(m, cx + 14, z1 + 6, 'RUINS OF OLD RAVENMOOR', 'House War · every two hours')
    return m, (cx, z1)


def pitch(parent, cx, cz):
    """The flying pitch: a field 160 × 84 with its markings, a beacon spire with two marker posts at each end for
    the flying sport to come, and three tiers of timber stands down both sides under the house banners. Empty at
    launch. Its path comes in at the south-west. Returns the model and its entrance."""
    m = model(parent, 'Flying pitch')
    length, width = 160, 84; x0, x1 = cx - length / 2, cx + length / 2
    part(m, 'Field', (cx, 0.1, cz), (length, 0.2, width), PITCH, 'Grass')
    for z in (cz - width / 2 + 1, cz + width / 2 - 1):
        part(m, 'Line', (cx, 0.22, z), (length - 2, 0.04, 0.6), LIMESTONE, 'Limestone', **TRIM)
    for x in (x0 + 1, cx, x1 - 1): part(m, 'Line', (x, 0.22, cz), (0.6, 0.04, width - 2), LIMESTONE, 'Limestone', **TRIM)
    part(m, 'Centre circle', (cx, 0.21, cz), (0.04, 24, 24), LIMESTONE, 'Limestone', **UPRIGHT, **TRIM)
    part(m, 'Centre', (cx, 0.215, cz), (0.05, 22.8, 22.8), PITCH, 'Grass', **UPRIGHT, **TRIM)
    for side in (-1, 1):
        x = cx + side * (length / 2 + 6)
        part(m, 'Spire base', (x, 1, cz), (8, 2, 8), CASTLE_STONE, 'Slate')
        part(m, 'Spire', (x, 16, cz), (3, 28, 3), CASTLE_STONE, 'Slate')
        part(m, 'Spire crown', (x, 30.5, cz), (4.4, 1, 4.4), GOLD, 'Metal')
        light(part(m, 'Beacon', (x, 32.4, cz), (2.6, 2.6, 2.6), LAMPLIGHT, 'Neon', shape=0, **TRIM), 1.6, 40)
        for dz in (-16, 16):
            part(m, 'Marker post', (x, 6, cz + dz), (1.6, 12, 1.6), CASTLE_STONE, 'Slate')
            part(m, 'Marker cap', (x, 12.4, cz + dz), (2.2, 0.8, 2.2), GOLD, 'Metal')
    for side in (-1, 1):
        edge = cz + side * (width / 2 + 4)
        for tier in range(3):
            part(m, 'Stand tier', (cx, (tier + 1) * 1.25, edge + side * (tier * 3 + 1.5)), (110, (tier + 1) * 2.5, 3), PLANK, 'WoodPlanks')
        back = edge + side * 9.6
        for x in frange(cx - 54, cx + 54, 12): part(m, 'Stand post', (x, 6, back), (0.8, 12, 0.8), BEAM, 'Wood')
        part(m, 'Stand rail', (cx, 11.6, back), (110, 0.6, 0.8), BEAM, 'Wood')
        for k, colour in enumerate(HOUSE_COLORS):
            part(m, 'House banner', (cx - 42 + 28 * k, 8.4, back + side * 0.5), (4, 6, 0.2), colour, 'Fabric', **TRIM)
    entrance = (x0, cz + width / 2 - 14)
    signpost(m, x0 - 8, entrance[1] + 6, 'FLYING PITCH', 'Empty until the flying sport')
    return m, entrance


BUILDERS = {'Greenhouses': greenhouses, "Groundskeeper's hut": hut, 'Ruins of Old Ravenmoor': ruins, 'Flying pitch': pitch}


def build(parent, name, centre, road):
    """The landmark `name` centred on `centre`, with a gravel path to it from `road`. Returns its Model."""
    m, entrance = BUILDERS[name](parent, *centre)
    path(m, road, entrance)
    return m
