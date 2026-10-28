"""Waystone, remodelled: a dressed runestone monolith on a three-step octagonal dais, banded in weathered bronze and
crowned with an iron talon cradle that holds a floating rune crystal. Glowing runes run down the front under a
ringed raven sigil and up the back, a ley line climbs each side, and eight more runes lie on the lowest step
around a lit ring at the monolith's foot.

The dais is 7.9 studs across and the talons stand 9.5 studs high, so the crystal floats well above a 5.5-stud
player and reads from across the square. It replaces the map's 3 x 7 x 3 slate block and neon ball (tools/build.py)
at the three Waystone points; the prompt at 3 studs up stays within reach of the front step.

Waystone.fbx holds one Model, Waystone, with one mesh per Roblox material:
    Stone     the dais, foot and monolith, with moss on the steps (Slate)
    Ironwork  the bronze bands and rivets, the crown's sheath and socket, and the talon cradle (Metal)
    Runes     every glowing inlay (Neon)
    Crystal   the floating crystal and its two shards (Neon), apart so a script can turn and bob it
The model is centred on its origin, standing on Z = 0, with the sigil face to the front (-Y).
"""
import math
import random
import bpy
from mathutils import Matrix, Vector
import rbx
from build import shade
from palette import COPPER, GOLD, GRANITE, IRON, PLAZA, PLINTH, RUNESTONE

RNG = random.Random(4417)
GLOW = (130, 228, 226)          # the map's Waystone rune
CRYSTAL = (176, 246, 240); MOSS = (84, 108, 66); ROBE = (52, 58, 92); SKIN = (226, 190, 156)
TIERS = ((0.0, 0.4, 3.95), (0.4, 0.8, 3.2), (0.8, 1.2, 2.5))   # each step's (bottom, top, corner radius)
FOOT = ((1.2, 1.8, 1.2, 0.42), (1.46, 1.8, 1.2, 0.42), (1.56, 1.68, 1.08, 0.38))
# The monolith's octagons up from the foot: (height, half-width, half-depth, corner cut). It flares a little at the
# foot and tapers faster towards the shoulders, which are bevelled under the iron crown.
SHAFT = ((1.5, 1.42, 0.86, 0.32), (1.72, 1.36, 0.82, 0.3), (3.0, 1.32, 0.8, 0.29), (4.4, 1.25, 0.76, 0.28),
         (5.7, 1.15, 0.7, 0.26), (6.75, 1.04, 0.63, 0.23), (7.0, 0.88, 0.53, 0.19), (7.12, 0.62, 0.38, 0.13))
CRADLE = 8.65                   # height of the crystal's centre, and of the talons' shared centre
SIDES = {'front': (0, 1), 'right': (90, 0), 'back': (180, 1), 'left': (-90, 0)}   # (turn from the front, w or d)

# Runes as strokes in a cell 0.6 wide and 1 tall, centred on the origin.
RUNES = {
    'way': [((0, -.5), (0, .5)), ((0, .5), (-.3, .2)), ((0, .5), (.3, .2))],
    'fork': [((0, -.5), (0, .5)), ((0, .05), (-.3, .4)), ((0, .05), (.3, .4))],
    'gate': [((-.3, -.5), (-.3, .5)), ((.3, -.5), (.3, .5)), ((-.3, .5), (.3, -.5)), ((-.3, -.5), (.3, .5))],
    'hearth': [((0, .5), (.3, 0)), ((.3, 0), (0, -.5)), ((0, -.5), (-.3, 0)), ((-.3, 0), (0, .5))],
    'hook': [((-.15, -.5), (-.15, .5)), ((-.15, .2), (.25, .5)), ((-.15, -.1), (.25, .2))],
    'bolt': [((.25, .5), (-.2, .1)), ((-.2, .1), (.2, -.1)), ((.2, -.1), (-.25, -.5))],
    'raven': [((0, -.5), (0, .3)), ((0, .3), (-.3, .5)), ((0, .3), (.3, .5)), ((0, -.15), (-.25, -.4)),
              ((0, -.15), (.25, -.4))],
}


def octagon(w, d, c):
    """A 2w x 2d rectangle with its corners cut back by c, as (x, y) points; side 7 is the front."""
    return [(w - c, -d), (w, -d + c), (w, d - c), (w - c, d), (-w + c, d), (-w, d - c), (-w, -d + c), (-w + c, -d)]


def column(mesh, rings, colours):
    """Skin octagons (height, w, d, c) up the Z axis, capped at both ends; `colours` gives each side its own colour,
    in octagon() order. loft() runs along Y, so the mesh frame turns it a quarter about X to run up Z."""
    mesh.frame = Matrix.Rotation(math.radians(90), 4, 'X')
    mesh.loft([(z, [(x, -y) for x, y in octagon(w, d, c)]) for z, w, d, c in rings], colours[0], colours=colours)
    mesh.frame = Matrix.Identity(4)


def slab(mesh, outline, z0, z1, colour):
    """Extrude an outline of (x, y) points from height z0 up to z1."""
    mesh.prism([(x, -y) for x, y in outline], z1 - z0, (0, 0, (z0 + z1) / 2), colour, turn=(90, 0, 0))


def corner(r, t):
    """A point on the octagon of corner radius r, t corners anticlockwise from its front-right corner."""
    j = math.floor(t)
    a, b = ((r * math.cos(math.radians(45 * n - 67.5)), r * math.sin(math.radians(45 * n - 67.5))) for n in (j, j + 1))
    return tuple(p + (q - p) * (t - j) for p, q in zip(a, b))


def octagon_run(r, t0, t1):
    return [corner(r, t) for t in [t0, *range(math.floor(t0) + 1, math.ceil(t1)), t1]]


def section(z):
    """The monolith's (w, d, c) at height z."""
    for (z0, *a), (z1, *b) in zip(SHAFT, SHAFT[1:]):
        if z0 <= z <= z1: return [p + (q - p) * (z - z0) / (z1 - z0) for p, q in zip(a, b)]
    raise ValueError(f'{z} is off the monolith')


def on_face(side, z):
    """A frame on one of the monolith's four faces at height z: X along the face, Z up its slope, -Y out of it."""
    turn, axis = SIDES[side]
    lean = math.atan((section(z - 0.05)[axis] - section(z + 0.05)[axis]) / 0.1)
    return (Matrix.Rotation(math.radians(turn), 4, 'Z') @ Matrix.Translation((0, -section(z)[axis], z))
            @ Matrix.Rotation(-lean, 4, 'X'))


def bar(mesh, p0, p1, out, colour, width, depth):
    """A bar from p0 to p1 standing `depth` proud of a surface facing `out`, lengthened by its width so that joined
    bars meet without a notch."""
    p0, p1, out = Vector(p0), Vector(p1), Vector(out).normalized()
    along = (p1 - p0).normalized(); m = Matrix.Identity(4)
    m.col[0], m.col[1] = (*(p1 - p0 + along * width), 0), (*(out * depth), 0)
    m.col[2], m.col[3] = (*(along.cross(out) * width), 0), (*((p0 + p1) / 2 + out * (depth / 2 - 0.01)), 1)
    mesh.block(m, colour)


def glyph(mesh, frame, rune, size, depth=0.05):
    """Inlay `rune`, `size` studs tall, on the face `frame` sits on."""
    out = frame.to_3x3() @ Vector((0, -1, 0))
    for a, b in RUNES[rune]:
        bar(mesh, frame @ Vector((a[0] * size, 0, a[1] * size)), frame @ Vector((b[0] * size, 0, b[1] * size)), out,
            GLOW, 0.12 * size, depth)


def ring_on(mesh, frame, radius, colour):
    """A half-sunk ring of light lying in the face `frame` sits on."""
    turn = (frame.to_3x3() @ Matrix.Rotation(math.radians(90), 3, 'X')).to_euler()
    mesh.torus(radius, 0.035, frame.translation, colour, turn=[math.degrees(a) for a in turn], segments=40, sides=6)


def dais(stone, runes):
    """Three octagonal steps of eight blocks each, a flat to the front. The middle step's joints fall at mid-side,
    so the courses break joint like laid masonry. Runes lie on the lowest tread and a lit ring circles the foot."""
    for k, (z0, z1, r) in enumerate(TIERS):
        inner = TIERS[k + 1][2] - 0.5 if k + 1 < len(TIERS) else 0
        # A core just inside the blocks closes the joints, so they read as mortar lines and let no light through.
        slab(stone, octagon_run(r - 0.08, 0, 8)[:-1], z0, z1 - 0.03, shade(PLINTH, 0.7))
        for i in range(8):
            t0, t1 = i + 0.5 * (k % 2), i + 1 + 0.5 * (k % 2)
            outline = octagon_run(r, t0 + 0.04 / r, t1 - 0.04 / r)
            outline += octagon_run(inner, t0 + 0.04 / inner, t1 - 0.04 / inner)[::-1] if inner else [(0, 0)]
            slab(stone, outline, z0, z1, shade(PLINTH, RNG.uniform(0.88, 1.06)))
    tread = (TIERS[0][2] + TIERS[1][2]) / 2 * math.cos(math.radians(22.5))
    for k, rune in enumerate(('way', 'hook', 'fork', 'hearth', 'gate', 'bolt', 'raven', 'hearth')):
        a = math.radians(45 * k - 90)    # from the front, anticlockwise; each rune reads from outside the dais
        frame = (Matrix.Translation((tread * math.cos(a), tread * math.sin(a), TIERS[0][1]))
                 @ Matrix.Rotation(a + math.pi / 2, 4, 'Z') @ Matrix.Rotation(math.radians(-90), 4, 'X'))
        glyph(runes, frame, rune, 0.42, depth=0.04)
    runes.torus(2.12, 0.045, (0, 0, TIERS[-1][1]), GLOW, segments=64, sides=6)
    # Moss in the angles of the steps, away from the runes.
    for reach, z, bearing in ((3.3, TIERS[0][1], 157.5), (2.65, TIERS[1][1], -22.5), (3.4, TIERS[0][1], 67.5),
                              (2.7, TIERS[1][1], 112.5)):
        for _ in range(4):
            a = math.radians(bearing + RNG.uniform(-9, 9)); rr = reach + RNG.uniform(-0.12, 0.12)
            stone.sphere(RNG.uniform(0.13, 0.24), (rr * math.cos(a), rr * math.sin(a), z), shade(MOSS, RNG.uniform(0.9, 1.1)),
                         segments=8, scale=(1, 1, 0.4))


def monolith(stone, runes, iron):
    column(stone, FOOT, [shade(GRANITE, 0.9), GRANITE] * 4)
    faces = [shade(RUNESTONE, k) for k in (1.0, 0.96, 0.98, 0.95)]   # front, right, back, left
    column(stone, SHAFT, [shade(RUNESTONE, 0.84), faces[1], shade(RUNESTONE, 0.84), faces[2], shade(RUNESTONE, 0.84),
                          faces[3], shade(RUNESTONE, 0.84), faces[0]])
    # Front: the raven sigil in its ring over three runes. Back: four runes. Sides: a ley line through a rune.
    ring_on(runes, on_face('front', 5.45), 0.48, GLOW)
    glyph(runes, on_face('front', 5.45), 'raven', 0.62)
    for z, rune in ((4.45, 'way'), (3.7, 'gate'), (2.95, 'fork')): glyph(runes, on_face('front', z), rune, 0.5)
    for z, rune in ((5.5, 'hook'), (4.7, 'bolt'), (3.9, 'hearth'), (3.1, 'fork')): glyph(runes, on_face('back', z), rune, 0.5)
    for side in ('left', 'right'):
        glyph(runes, on_face(side, 4.4), 'hearth', 0.6)
        for lo, hi in ((2.4, 4.02), (4.78, 6.15)):
            heights = [lo, *(z for z, *_ in SHAFT if lo < z < hi), hi]
            for z0, z1 in zip(heights, heights[1:]):
                f0, f1 = on_face(side, z0), on_face(side, z1)
                bar(runes, f0.translation, f1.translation, on_face(side, (z0 + z1) / 2).to_3x3() @ Vector((0, -1, 0)),
                    GLOW, 0.07, 0.05)
    # Two bronze bands with brass rivets.
    for z0, z1 in ((2.0, 2.22), (6.3, 6.52)):
        column(iron, [(z, w + 0.05, d + 0.05, c + 0.02) for z in (z0, z1) for w, d, c in [section(z)]], [COPPER] * 8)
        for side, xs in (('front', (-0.8, 0, 0.8)), ('back', (-0.8, 0, 0.8)), ('left', (0,)), ('right', (0,))):
            for x in xs: iron.sphere(0.055, on_face(side, (z0 + z1) / 2) @ Vector((x, -0.06, 0)), GOLD, segments=8)


def crown(iron, crystal):
    """An iron sheath over the bevelled shoulders and a turned socket, from which four talons curve up around the
    crystal on one shared circle, each with a brass knuckle at its widest."""
    column(iron, [(z, w + 0.07, d + 0.07, c + 0.03) for z in (6.8, 7.0, 7.12) for w, d, c in [section(z)]]
           + [(7.2, 0.64, 0.4, 0.13)], [IRON] * 8)
    column(iron, [(z, w + 0.1, d + 0.1, c + 0.04) for z in (6.78, 6.85) for w, d, c in [section(z)]], [GOLD] * 8)
    iron.lathe([(0, 7.18), (0.42, 7.18), (0.47, 7.3), (0.35, 7.45), (0.3, 7.6), (0.41, 7.7), (0.38, 7.8), (0, 7.8)],
               IRON, segments=16)
    iron.torus(0.4, 0.04, (0, 0, 7.7), GOLD, segments=24, sides=6)
    radius, low, high = 1.0, 68, 50    # degrees below and above the crystal's centre where each talon starts and ends
    for k in range(4):
        spin = 45 + 90 * k
        iron.torus(radius, 0.055, (0, 0, CRADLE), IRON, turn=(90, low, spin), segments=16, sides=8, arc=low + high)
        out = Vector((math.cos(math.radians(spin)), math.sin(math.radians(spin)), 0))
        iron.sphere(0.085, out * radius + Vector((0, 0, CRADLE)), GOLD, segments=10)
        tip = out * radius * math.cos(math.radians(high)) + Vector((0, 0, CRADLE + radius * math.sin(math.radians(high))))
        ahead = -out * math.sin(math.radians(high)) + Vector((0, 0, math.cos(math.radians(high))))
        iron.cylinder(0.055, 0.28, tip + ahead * 0.14, IRON, top=0.008, turn=(0, -high, spin), segments=8)
    # Its lower point floats a quarter stud over the socket and its upper point rises clear of the talons.
    crystal.lathe([(0, -0.6), (0.4, -0.12), (0.42, 0.24), (0, 1.0)], CRYSTAL, at=(0, 0, CRADLE), segments=6)
    for x, z in ((0.7, 0.22), (-0.7, -0.18)):
        crystal.lathe([(0, -0.16), (0.09, 0), (0, 0.16)], CRYSTAL, at=(x, 0, CRADLE + z), segments=4)


def preview_extras():
    """The plaza underfoot and a 5.5-stud player looking up at the stone, for the previews and the .blend only.
    Returns the player, so that it stands only in the first shot."""
    ground = rbx.Mesh('_Preview ground'); ground.box((40, 40, 0.1), (0, 0, -0.05), PLAZA)
    player = rbx.Mesh('_Preview player', frame=Matrix.Translation((-5.6, 0.5, 0)) @ Matrix.Rotation(math.radians(85), 4, 'Z'))
    for x in (-0.5, 0.5): player.box((0.95, 1, 2.2), (x, 0, 1.1), shade(ROBE, 0.8))
    player.box((2, 1, 2.1), (0, 0, 3.25), ROBE)
    for x in (-1.45, 1.45): player.box((0.9, 1, 2.0), (x, 0, 3.3), ROBE)
    player.box((1.2, 1.2, 1.2), (0, 0, 4.9), SKIN)
    ground.finish()
    return player.finish()


rbx.scene('Waystone')
stone, iron, runes, crystal = (rbx.Mesh(n) for n in ('Stone', 'Ironwork', 'Runes', 'Crystal'))
dais(stone, runes)
monolith(stone, runes, iron)
crown(iron, crystal)
waystone = rbx.group('Waystone', [stone.finish(sharp=35), iron.finish(sharp=35), runes.finish(sharp=35),
                                  crystal.finish(sharp=20)])
player = preview_extras()
rbx.viewport((0, 0, 4.6), 24, turn=(72, 0, 35))
rbx.export('Waystone', [waystone, *waystone.children_recursive], auto_preview=False)
# The preview's default light runs exactly along two of the monolith's chamfers, and Workbench's shadow volumes
# streak across the steps when light grazes a face; this one lights every face clearly or not at all.
bpy.context.scene.display.light_direction = Vector((0.45, 0.62, 0.64)).normalized()
rbx.shot('Waystone', (10, -14, 6.2), (0, 0, 4.4), lens=40, resolution=(1400, 1050))
player.hide_render = True
rbx.shot('Waystone_front', (0, -21, 4.8), (0, 0, 4.8), lens=60, resolution=(1000, 1250))
rbx.shot('Waystone_back', (-9.5, 12.5, 5.6), (0, 0, 4.4), lens=50, resolution=(1000, 1250))
rbx.shot('Waystone_crown', (2.6, -4.2, 9.6), (0, 0, 8.4), lens=45, resolution=(1000, 1000))
