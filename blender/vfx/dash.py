"""Dash VFX: the wind, speed lines and shock ring a character throws off when they dodge (Shift / LB).

DashVFX.fbx holds one Model, DashVFX, with three near-white meshes. The game tints them and makes them Neon, then
EffectsController:Dash stretches, moves and fades them, so nothing here is animated:
    Streak       two crescent ribbons that twist round the dash path, full at the front and thinning to the
                 tail. It is stretched to the dash's real length, which is up to 10 studs (CombatService:Dodge).
    Speed lines  ten tapered needles that trail behind where the character lands.
    Ring         a shock ring, with a fainter ripple inside it, that blooms where the dash began. Laid flat, it
                 is also the dust ring at the landing.

Every mesh lies along the dash: its front (Blender -Y, the part's LookVector) is where the character arrives, and
every piece is centred on the origin, so a part's CFrame is simply the middle of what it covers.
"""
import math
import rbx

MIST = (236, 228, 255)   # near white: the part's Color sets the hue in game
LENGTH = 10              # studs, the longest dodge

rbx.scene('DashVFX')


def crescent(radius, thick, span, centre, points=8):
    """A closed (x, z) outline: an arc band `thick` studs deep and `span` degrees wide, centred on angle `centre`."""
    angles = [math.radians(centre - span / 2 + span * k / (points - 1)) for k in range(points)]
    outer = [((radius + thick / 2) * math.cos(a), (radius + thick / 2) * math.sin(a)) for a in angles]
    inner = [((radius - thick / 2) * math.cos(a), (radius - thick / 2) * math.sin(a)) for a in reversed(angles)]
    return outer + inner


# Two ribbons, half a turn apart, each twisting most of a turn from front to tail, with open gaps between them.
# They grow out of a character-sized body at the front, billow out midway and narrow to a point at the tail.
streak = rbx.Mesh('Streak')
STEPS = 28
for start in (0, 180):
    sections = []
    for i in range(STEPS + 1):
        t = i / STEPS
        grow = 0.4 + 0.6 * min(1, t / 0.15)     # the front end fans in from a narrow edge
        radius = 0.85 + 0.6 * math.sin(math.pi * t) - 0.55 * t
        thick, span = (0.2 * (1 - t) + 0.02) * grow, (110 * (1 - t) + 20) * grow
        sections.append((-LENGTH / 2 + LENGTH * t, crescent(radius, thick, span, start + 300 * t)))
    streak.loft(sections, MIST)

# Speed lines start near the front, 1.5 to 2.4 studs off the axis, and run 3 to 6.5 studs back to a point.
lines = rbx.Mesh('Speed lines')
for k in range(10):
    a = math.radians(36 * k + (13 if k % 2 else 0))
    r = 1.5 + 0.9 * ((7 * k) % 5) / 4
    length = 3 + 3.5 * ((3 * k) % 4) / 3
    y = -2.5 + length / 2 + 0.6 * ((5 * k) % 3)
    lines.cylinder(0.07, length, (r * math.cos(a), y, r * math.sin(a)), MIST, top=0.0, turn=(-90, 0, 0), segments=6)

# The shock ring stands across the dash (in Blender's XZ plane), with a fainter ripple inside.
ring = rbx.Mesh('Ring')
ring.torus(1.6, 0.12, (0, 0, 0), MIST, turn=(90, 0, 0), segments=40, sides=8)
ring.torus(1.1, 0.05, (0, 0, 0), MIST, turn=(90, 0, 0), segments=32, sides=6)

dash = rbx.group('DashVFX', [streak.finish(sharp=70), lines.finish(sharp=70), ring.finish(sharp=70)])
rbx.viewport((0, 0, 0), 22, turn=(70, 0, 50))
rbx.export('DashVFX', [dash, *dash.children_recursive], auto_preview=False)

# Previews: the three pieces side by side (moved apart only for the pictures; the export keeps them centred),
# seen from the front right, and the streak alone from the side.
if rbx.PREVIEW:
    parts = {o.name: o for o in dash.children_recursive}
    parts['Speed lines'].location.x, parts['Ring'].location.x = -6.5, 6.0
    rbx.shot('DashVFX', (13, -15, 8), (0, 0, 0), lens=32, resolution=(1400, 900))
    parts['Speed lines'].hide_render = parts['Ring'].hide_render = True
    rbx.shot('DashVFX_side', (16, 0, 2.5), (0, 0, 0), lens=40, resolution=(1400, 700))
