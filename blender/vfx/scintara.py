"""Scintara VFX: the spark bolt a left click throws, and the spark lance a held right click pours out of the wand.

ScintaraVFX.fbx holds one Model, ScintaraVFX, with seven near-white meshes. The game tints them arcane violet and
makes them Neon, then EffectsController moves, stretches and fades them, so nothing here is animated:
    Spark   the bolt's core: a six-spiked star with four shorter spikes between, round a small ball.
    Tail    the bolt's comet tail: a tapered core and three ribbons that twist back from the spark.
    Flash   a flat twelve-pointed star, the flash at the wand's tip as a bolt leaves or while the lance pours.
    Beam    the lance's core: a tube 1 stud long and 1 across, stretched to the beam's length and thickness.
    Coil    two helix ribbons round the beam, 6 studs long. Copies tile end to end along the beam and scroll
            forward, so the twist seems to pour out of the wand.
    Ring    a thin ring with a fainter ripple inside, standing across the beam. A few travel out along it.
    Splash  where the lance strikes: seven sparks spraying back toward the caster round a shock ring.

Every mesh lies along the way the spell travels: its front (Blender -Y, the part's LookVector) points away from
the wand, and every piece is centred on the origin.
"""
import math
from mathutils import Vector
import rbx

MIST = (236, 228, 255)   # near white: the part's Color sets the hue in game
WHITE = (255, 255, 255)

rbx.scene('ScintaraVFX')


def spike(mesh, direction, length, radius, colour, base=0.0):
    """A cone from `base` studs out along `direction` to a point `length` further, `radius` thick at its foot."""
    d = Vector(direction).normalized()
    turn = d.to_track_quat('Z', 'Y').to_euler()
    mesh.cylinder(radius, length, tuple(d * (base + length / 2)), colour, top=0.0,
                  turn=tuple(math.degrees(a) for a in turn), segments=6)


def crescent(radius, thick, span, centre, points=7):
    """A closed (x, z) outline: an arc band `thick` studs deep and `span` degrees wide, centred on angle `centre`."""
    angles = [math.radians(centre - span / 2 + span * k / (points - 1)) for k in range(points)]
    outer = [((radius + thick / 2) * math.cos(a), (radius + thick / 2) * math.sin(a)) for a in angles]
    inner = [((radius - thick / 2) * math.cos(a), (radius - thick / 2) * math.sin(a)) for a in reversed(angles)]
    return outer + inner


def star(points, outer, inner, turn=0.0):
    """A closed (x, z) star outline of `points` points."""
    return [((outer if k % 2 == 0 else inner) * math.cos(math.radians(turn + 180 * k / points)),
             (outer if k % 2 == 0 else inner) * math.sin(math.radians(turn + 180 * k / points)))
            for k in range(points * 2)]


# The spark: long spikes up, down and to each side, shorter ones fore and aft, and four short ones between.
spark = rbx.Mesh('Spark')
spark.sphere(0.16, (0, 0, 0), WHITE, segments=10)
for d in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1)): spike(spark, d, 0.5, 0.09, WHITE, base=0.05)
for d in ((0, -1, 0), (0, 1, 0)): spike(spark, d, 0.36, 0.09, WHITE, base=0.05)
for d in ((1, 0, 1), (-1, 0, 1), (1, 0, -1), (-1, 0, -1)): spike(spark, d, 0.28, 0.06, MIST, base=0.05)

# The tail runs 3.4 studs back from the spark: a tapered core, and three ribbons a third of a turn apart that
# twist most of a turn as they thin to the end.
TAIL = 3.4
tail = rbx.Mesh('Tail')
tail.cylinder(0.13, TAIL, (0, 0, 0), WHITE, top=0.0, turn=(-90, 0, 0), segments=8)
STEPS = 24
for start in (0, 120, 240):
    sections = []
    for i in range(STEPS + 1):
        t = i / STEPS
        radius = 0.3 * (1 - t) + 0.04
        thick, span = 0.09 * (1 - t) + 0.015, 70 * (1 - t) + 15
        sections.append((-TAIL / 2 + TAIL * t, crescent(radius, thick, span, start + 220 * t)))
    tail.loft(sections, MIST)

# The flash: two six-pointed stars a twelfth of a turn apart, standing across the way the spell goes.
flash = rbx.Mesh('Flash')
flash.prism(star(6, 0.7, 0.16), 0.04, (0, 0, 0), WHITE)
flash.prism(star(6, 0.42, 0.12, turn=30), 0.08, (0, 0, 0), MIST)

# The lance's core: one stud each way, so the game sets its Size to (thickness, thickness, length).
beam = rbx.Mesh('Beam')
beam.cylinder(0.5, 1.0, (0, 0, 0), WHITE, turn=(-90, 0, 0), segments=16)

# Two helix ribbons, half a turn apart, 2.5 turns in 6 studs. Each ends where the other began, so copies tile
# seamlessly end to end.
COIL, PITCH, RADIUS = 6.0, 2.4, 0.55
coil = rbx.Mesh('Coil')
for start in (0, math.pi):
    points = [(RADIUS * math.cos(start + 2 * math.pi * y / PITCH), y, RADIUS * math.sin(start + 2 * math.pi * y / PITCH))
              for y in (-COIL / 2 + COIL * k / 60 for k in range(61))]
    coil.tube(points, 0.05, MIST, sides=5)

ring = rbx.Mesh('Ring')
ring.torus(0.75, 0.05, (0, 0, 0), WHITE, turn=(90, 0, 0), segments=32, sides=6)
ring.torus(0.45, 0.03, (0, 0, 0), MIST, turn=(90, 0, 0), segments=24, sides=5)

# The splash: seven sparks thrown back toward the caster (+Y) and out, round a shock ring on the struck surface.
splash = rbx.Mesh('Splash')
for k in range(7):
    a = math.radians(360 * k / 7 + 10)
    out = 0.75 + 0.25 * ((3 * k) % 3)
    spike(splash, (math.cos(a) * out, 0.8, math.sin(a) * out), 0.7 + 0.3 * ((2 * k) % 3) / 2, 0.06, WHITE, base=0.2)
splash.torus(0.9, 0.06, (0, 0, 0), MIST, turn=(90, 0, 0), segments=32, sides=6)
splash.sphere(0.22, (0, 0, 0), WHITE, segments=10)

pieces = [m.finish(sharp=70) for m in (spark, tail, flash, beam, coil, ring, splash)]
vfx = rbx.group('ScintaraVFX', pieces)
rbx.viewport((0, 0, 0), 14, turn=(70, 0, 50))
rbx.export('ScintaraVFX', [vfx, *vfx.children_recursive], auto_preview=False)

# Previews (moved and copied only for the pictures; the export keeps every piece centred):
#   ScintaraVFX.png        the seven pieces in a row
#   ScintaraVFX_bolt.png   the bolt as the game puts it together, flying toward the left of the picture
#   ScintaraVFX_lance.png  a 14-stud lance as the game puts it together, from the wand's flash to the splash
if rbx.PREVIEW:
    import bpy
    parts = {o.name: o for o in vfx.children_recursive}
    for k, name in enumerate(('Spark', 'Tail', 'Flash', 'Beam', 'Coil', 'Ring', 'Splash')):
        parts[name].location.x = 3 * k - 9
    rbx.shot('ScintaraVFX', (0, -16, 7), (0, 0, 0), lens=30, resolution=(1600, 700))

    sc = bpy.context.scene
    for o in parts.values(): o.hide_render = True
    copies = []

    def place(name, at, scale=(1, 1, 1)):
        o = parts[name].copy(); sc.collection.objects.link(o); o.parent = None
        o.location, o.scale, o.hide_render = at, scale, False
        copies.append(o)
        return o

    # The bolt flies toward -Y: the spark at the front of its tail.
    place('Spark', (0, -TAIL / 2, 0), (1.2, 1.2, 1.2))
    place('Tail', (0, 0, 0))
    rbx.shot('ScintaraVFX_bolt', (8, -7, 3), (0, -2.5, 0), lens=35, resolution=(1200, 700))
    for o in copies: bpy.data.objects.remove(o)
    copies.clear()

    # The lance pours toward -Y from the wand at the origin, 14 studs to the splash. As in the game, the fewest
    # Coils that cover the beam are each stretched a little so they end exactly at the splash.
    LENGTH = 14
    place('Beam', (0, -LENGTH / 2, 0), (0.45, LENGTH, 0.45))
    count = math.ceil(LENGTH / COIL); each = LENGTH / count
    for k in range(count):
        place('Coil', (0, -each * (k + 0.5), 0), (1, each / COIL, 1))
    for y in (2.5, 7, 11.5):
        place('Ring', (0, -y, 0))
    place('Flash', (0, 0, 0), (1.3, 1.3, 1.3))
    place('Splash', (0, -LENGTH, 0))
    rbx.shot('ScintaraVFX_lance', (12, -8, 3.5), (0, -7, 0), lens=30, resolution=(1600, 700))
