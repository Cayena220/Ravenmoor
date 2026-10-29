"""Flying brooms: the academy's own broom and three more to ride, each with its own silhouette.

    Ashwind     the primary broom, issued to every first-year: a straight ash shaft that lifts a little at the tip
                under a brass finial, a leather grip, brass collars and stirrups, an arcane rune on each side of the
                collar, and a classic flared tail of straw-brown twigs bound in three brass bands.
    Swiftquill  a racer: a long slim silverbirch shaft with a frost-blue crystal held in silver claws at the nose,
                glowing speed stripes, a low padded seat, swept silver stirrup fins and a tight tail that tapers to a
                point between three silver stabiliser fins.
    Stoutbough  a hauler: a thick knotted ironoak shaft with an iron cap and tow ring on the tip and a lantern hung
                under it, iron bands and rivets, a deep saddle with a pommel and saddlebags, a plank footboard on iron
                struts, and a big round bushy tail lashed with rope.
    Nightwing   a wild one: a twisting blackthorn shaft wound with a vine and set with thorns, curling into a crook
                at the tip that cradles an ember gem, pewter claws gripping a ragged fan of raven-dark twigs and
                feathers whose tips smoulder like embers.

Each broom is 7 to 9 studs long and lies along Y with its tip to the front (-Y). Its seat, where a rider sits on the
shaft, is the origin of its own model. Brooms.fbx holds one Model, Brooms, with the four side by side SPACING studs
apart along Blender X (Roblox -X), Ashwind first. Each broom is a Model of up to five meshes, one per Roblox material:
    Wood      the shaft and anything carved (Wood)
    Bristles  the tail's twigs, feathers and lashings (Wood: Fabric darkens the straw)
    Metal     bands, finials, stirrups, fins, claws and the lantern's frame (Metal)
    Leather   grips, seats and saddlebags (Leather)
    Glow      runes, crystals, gems, stripes and lamplight (Neon, in the broom's GLOW colour)
blender/place_brooms.lua puts them in ReplicatedStorage.Brooms in Studio, each pivoted on its seat.
"""
import math
import random
import bpy
from mathutils import Matrix, Vector
import rbx
from build import shade
from palette import GOLD, IRON, LAMPLIGHT, PLAZA

RNG = random.Random(7316)
SPACING = 3.2                     # studs between seats along Blender X in Brooms.fbx
MATERIALS = ('Wood', 'Bristles', 'Metal', 'Leather', 'Glow')
GLOW = {'Ashwind': (194, 163, 255), 'Swiftquill': (140, 220, 255), 'Stoutbough': LAMPLIGHT,
        'Nightwing': (255, 140, 64)}   # the arcane dash, Frostfang, lamplight and Emberplume
BRASS = GOLD


def spline(ctrl, steps=6):
    """A Catmull-Rom curve through control points (x, y, z, radius): the points along it and the radius at each."""
    p = [Vector(c) for c in ctrl]
    p = [2 * p[0] - p[1], *p, 2 * p[-1] - p[-2]]
    out = []
    for i in range(1, len(p) - 2):
        a, b, c, d = p[i - 1:i + 3]
        for s in range(steps):
            t = s / steps
            out.append(0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (3 * b - a - 3 * c + d) * t ** 3))
    out.append(p[-2])
    return [v.xyz for v in out], [v.w for v in out]


def turn_to(axis):
    """The turn (degrees about X, Y, Z) that points a shape's Z axis along `axis`."""
    return [math.degrees(a) for a in Vector((0, 0, 1)).rotation_difference(Vector(axis)).to_euler()]


def plate(mesh, outline, thickness, colour, plane, at=(0, 0, 0)):
    """A flat plate `thickness` studs thick: `outline` is (y, z) points in the YZ plane, or (x, y) points in XY."""
    if plane == 'yz': mesh.prism(list(outline), thickness, at, colour, turn=(0, 0, 90))
    else: mesh.prism([(x, -y) for x, y in outline], thickness, at, colour, turn=(90, 0, 0))


class Shaft:
    """A broom's shaft: a tube through control points (x, y, z, radius) from the tip back, smoothed into a curve.
    Fittings are placed by y, along the part of the shaft that runs toward the tail."""

    def __init__(self, mesh, ctrl, colour, sides=12, steps=6):
        self.path, self.radii = spline(ctrl, steps)
        mesh.tube(self.path, self.radii, colour, sides=sides)
        self.tip, self.ahead = self.path[0], (self.path[0] - self.path[1]).normalized()

    def at(self, y):
        """The shaft's centre at y, its heading there and its radius."""
        for i, (a, b) in enumerate(zip(self.path, self.path[1:])):
            if a.y <= y <= b.y and b.y > a.y:
                t = (y - a.y) / (b.y - a.y)
                return a.lerp(b, t), (b - a).normalized(), self.radii[i] + (self.radii[i + 1] - self.radii[i]) * t
        raise ValueError(f'the shaft never reaches y = {y}')

    def surface(self, y, angle, out=0.0):
        """The point `out` studs off the shaft's surface at y, `angle` degrees round from +X toward +Z."""
        p, _, r = self.at(y); a = math.radians(angle)
        return p + Vector((math.cos(a), 0, math.sin(a))) * (r + out)

    def band(self, mesh, y, colour, thickness=0.035, radius=None, sides=6):
        """A ring round the shaft at y, hugging it, or `radius` studs out from its centre."""
        p, heading, r = self.at(y)
        mesh.torus(radius or r + thickness * 0.5, thickness, p, colour, turn=turn_to(heading), segments=20, sides=sides)

    def sleeve(self, mesh, y0, y1, gap, colour, sides=12):
        """A wrap round the shaft from y0 to y1, `gap` studs thick."""
        ys = [y0 + (y1 - y0) * k / 8 for k in range(9)]
        mesh.tube([self.at(y)[0] for y in ys], [self.at(y)[2] + gap for y in ys], colour, sides=sides)

    def knots(self, mesh, spots, colour):
        for y, angle, size in spots:
            mesh.sphere(size, self.surface(y, angle, -size * 0.35), colour, segments=8, scale=(1, 1.7, 1))


def tail(mesh, start, length, flare, colours, count, core, thick=(0.035, 0.012), droop=0.05, squash=1.0,
         reach=(0.88, 1.05)):
    """A broom's tail from its binding at y=`start` back `length` studs: a solid core and `count` twigs on it, the
    bundle `flare(f)` studs in radius at fraction f of the way. The twigs sag a little toward their tips, and `squash`
    flattens the bundle top to bottom. Returns each twig's tip and heading, for anything set on the ends."""
    def sag(f): return -droop * f * f * length
    mesh.loft([(start + length * f, [(flare(f) * 0.8 * math.cos(t), flare(f) * 0.8 * squash * math.sin(t) + sag(f))
                                     for t in (2 * math.pi * k / 14 for k in range(14))])
               for f in (k / 10 for k in range(11))], core)
    tips = []
    for _ in range(count):
        a, u, far = RNG.uniform(0, 2 * math.pi), RNG.uniform(0.72, 1.04), RNG.uniform(*reach)
        points = []
        for f in (0, 0.33, 0.66, 1):
            g = f * far; r = flare(min(g, 1)) * u
            points.append(Vector((r * math.cos(a), start + length * g, r * math.sin(a) * squash + sag(g))))
        mesh.tube(points, [thick[0] + (thick[1] - thick[0]) * f for f in (0, 0.33, 0.66, 1)], RNG.choice(colours), sides=3)
        tips.append((points[-1], (points[-1] - points[-2]).normalized()))
    return tips


def ring_point(a, r, y, squash=1.0):
    a = math.radians(a)
    return (r * math.cos(a), y, r * math.sin(a) * squash)


# Ashwind, the primary broom.
ASH = (186, 150, 104); ASH_KNOT = shade(ASH, 0.78); GRIP = (104, 66, 44); GRIP_WRAP = (74, 44, 28)
STRAW = ((166, 130, 80), (148, 114, 68), (180, 146, 94), (130, 100, 60)); STRAW_CORE = (118, 90, 54)


def ashwind(m):
    wood, metal, leather, glow = m['Wood'], m['Metal'], m['Leather'], m['Glow']
    shaft = Shaft(wood, [(0, -3.7, 0.3, 0.115), (0, -3.15, 0.16, 0.13), (0, -2.3, 0.04, 0.142), (0, -1.3, 0, 0.15),
                         (0, 0, 0, 0.155), (0, 1.1, 0, 0.16), (0, 2.3, 0, 0.15)], ASH)
    shaft.knots(wood, [(-2.75, 40, 0.05), (-0.35, 210, 0.045), (0.62, 125, 0.05)], ASH_KNOT)
    metal.sphere(0.15, shaft.tip + shaft.ahead * 0.06, BRASS, segments=14)
    for y in (-3.5, -3.34): shaft.band(metal, y, BRASS, 0.03)
    # The grip, wound with a darker thong between two brass collars.
    shaft.sleeve(leather, -2.0, -0.85, 0.022, GRIP)
    for k in range(8): shaft.band(leather, -1.94 + k * 0.152, GRIP_WRAP, 0.022, sides=5)
    for y in (-2.05, -0.8): shaft.band(metal, y, BRASS, 0.035, radius=0.2)
    # The academy's collar: a brass medallion on each side with an arcane rune.
    for y in (-0.68, -0.42): shaft.band(metal, y, BRASS, 0.028)
    for s in (-1, 1):
        metal.cylinder(0.12, 0.05, (s * 0.17, -0.55, 0), BRASS, turn=(0, 90, 0), segments=16)
        glow.cylinder(0.065, 0.03, (s * 0.2, -0.55, 0), GLOW['Ashwind'], turn=(0, 90, 0), segments=12)
    # Stirrups hung from a clamp behind the seat.
    shaft.band(metal, 0.55, BRASS, 0.035)
    for s in (-1, 1):
        metal.tube([(s * 0.07, 0.55, -0.13), (s * 0.22, 0.6, -0.7), (s * 0.3, 0.66, -1.22)], 0.038, BRASS, sides=6)
        metal.tube([(s * 0.28, 0.66, -1.25), (s * 0.66, 0.7, -1.27)], 0.05, BRASS, sides=8)
        metal.box((0.34, 0.24, 0.04), (s * 0.48, 0.69, -1.23), BRASS)

    def flare(f):
        return (0.22 + 0.05 * min(f / 0.22, 1) + 0.33 * math.sin(math.pi / 2 * min(max(f - 0.22, 0) / 0.6, 1))
                - 0.06 * max(f - 0.85, 0) / 0.15)
    tail(m['Bristles'], 1.0, 2.6, flare, STRAW, 220, STRAW_CORE)
    for y in (1.06, 1.28, 1.5): shaft.band(metal, y, BRASS, 0.045, radius=flare((y - 1.0) / 2.6) + 0.03)


# Swiftquill, the racer.
BIRCH = (222, 220, 208); BIRCH_MARK = (66, 62, 60); SILVER = (214, 220, 228); SEAT = (58, 70, 96)
PALE = ((208, 198, 170), (192, 184, 158), (172, 178, 186), (220, 212, 188)); PALE_CORE = (172, 164, 142)


def swiftquill(m):
    wood, metal, leather, glow = m['Wood'], m['Metal'], m['Leather'], m['Glow']
    frost = GLOW['Swiftquill']
    shaft = Shaft(wood, [(0, -4.2, 0, 0.1), (0, -3.4, 0, 0.115), (0, -2.0, 0, 0.125), (0, 0, 0, 0.132),
                         (0, 1.3, 0, 0.128), (0, 2.6, 0, 0.12)], BIRCH)
    for _ in range(34):   # the birch's dark lenticels, running round the shaft
        y, a = RNG.uniform(-3.9, 1.1), RNG.uniform(0, 360)
        wood.box((0.02, 0.03, RNG.uniform(0.07, 0.15)), shaft.surface(y, a, -0.004), BIRCH_MARK, turn=(0, -a, 0))
    # The nose: a frost crystal held out in front by three silver claws.
    shaft.band(metal, -4.08, SILVER, 0.035)
    for a in (90, 210, 330):
        metal.tube([ring_point(a, 0.1, -4.1), ring_point(a, 0.16, -4.32), ring_point(a, 0.14, -4.52),
                    ring_point(a, 0.05, -4.7)], [0.03, 0.028, 0.022, 0.01], SILVER, sides=5)
    glow.sphere(0.12, (0, -4.45, 0), frost, segments=8, scale=(0.85, 1.7, 0.85))
    for s in (-1, 1): glow.box((0.015, 1.3, 0.03), (s * 0.116, -3.0, 0), frost)
    # A low padded racing seat between two silver clamps.
    leather.sphere(1, (0, 0.08, 0.13), SEAT, segments=16, scale=(0.2, 0.52, 0.075))
    leather.sphere(1, (0, 0.56, 0.2), SEAT, segments=12, scale=(0.18, 0.1, 0.09))
    for y in (-0.45, 0.68): shaft.band(metal, y, SILVER, 0.025)
    # Swept stirrup fins with foot pegs.
    for s in (-1, 1):
        plate(metal, [(0.25, -0.1), (0.7, -0.1), (1.12, -1.02), (0.98, -1.12), (0.62, -0.6), (0.3, -0.3)], 0.035,
              SILVER, 'yz', at=(s * 0.1, 0, 0))
        metal.tube([(s * 0.1, 1.02, -1.05), (s * 0.46, 1.06, -1.08)], 0.045, SILVER, sides=8)

    def flare(f): return 0.16 + 0.15 * math.sin(math.pi * min(f, 1)) - 0.1 * f
    tail(m['Bristles'], 1.25, 3.0, flare, PALE, 170, PALE_CORE, thick=(0.03, 0.01), droop=0.015, reach=(0.9, 1.03))
    for y in (1.3, 1.52): shaft.band(metal, y, SILVER, 0.035, radius=flare((y - 1.25) / 3.0) + 0.03)
    shaft.band(glow, 1.41, frost, 0.022, radius=flare(0.05) + 0.035)
    # Stabiliser fins over and beside the tail.
    plate(metal, [(1.7, 0.18), (2.7, 0.22), (2.95, 0.62), (2.45, 0.6)], 0.035, SILVER, 'yz')
    for s in (-1, 1): plate(metal, [(s * 0.2, 1.7), (s * 0.25, 2.7), (s * 0.62, 2.95), (s * 0.6, 2.45)], 0.035, SILVER, 'xy')


# Stoutbough, the hauler.
OAK = (98, 80, 62); OAK_KNOT = (72, 58, 44); RIVET = (92, 94, 100)
SADDLE = (114, 72, 44); SADDLE_DARK = (82, 50, 30); ROPE = (156, 132, 94)
HEATHER = ((106, 82, 56), (90, 70, 48), (122, 96, 66), (78, 62, 44)); HEATHER_CORE = (70, 54, 38)


def stoutbough(m):
    wood, metal, leather, glow = m['Wood'], m['Metal'], m['Leather'], m['Glow']
    shaft = Shaft(wood, [(0, -3.3, 0.16, 0.17), (0.02, -2.6, 0.05, 0.2), (-0.03, -1.6, 0, 0.21), (0.01, -0.6, 0, 0.22),
                         (0, 0.4, 0, 0.22), (0, 1.4, 0, 0.22), (0, 2.3, 0, 0.2)], OAK, sides=10)
    shaft.knots(wood, [(-2.85, 300, 0.08), (-2.2, 60, 0.09), (-0.3, 170, 0.07), (0.85, 20, 0.08), (0.4, 250, 0.06)],
                OAK_KNOT)
    # An iron cap on the tip, riveted on, with a tow ring through an eye bolt.
    shaft.sleeve(metal, -3.29, -3.08, 0.03, IRON, sides=10)
    metal.cylinder(0.2, 0.04, shaft.tip, IRON, turn=turn_to(shaft.ahead), segments=10)
    for a in (45, 135, 225, 315): metal.sphere(0.03, shaft.surface(-3.18, a, 0.05), RIVET, segments=6)
    metal.tube([shaft.tip, shaft.tip + shaft.ahead * 0.08], 0.045, IRON, sides=6)
    metal.torus(0.12, 0.035, shaft.tip + shaft.ahead * 0.19, IRON, turn=(0, 90, 0), segments=16, sides=6)
    # Iron bands with four rivets each.
    for y in (-2.5, -1.15, 1.16):
        shaft.band(metal, y, IRON, 0.04)
        for a in (0, 90, 180, 270): metal.sphere(0.035, shaft.surface(y, a, 0.04), RIVET, segments=6)
    # A lantern hung under the tip on an iron strap.
    lamp = Vector((0, -2.95, 0))
    metal.tube([lamp + Vector((0, 0, -0.16)), lamp + Vector((0, 0, -0.5))], 0.025, IRON, sides=6)
    metal.torus(0.06, 0.018, lamp + Vector((0, 0, -0.56)), IRON, turn=(90, 0, 0), segments=12, sides=5)
    metal.cylinder(0.17, 0.1, lamp + Vector((0, 0, -0.66)), IRON, top=0.06, segments=6)
    metal.cylinder(0.19, 0.03, lamp + Vector((0, 0, -0.72)), IRON, segments=6)
    metal.cylinder(0.19, 0.06, lamp + Vector((0, 0, -1.15)), IRON, segments=6)
    for k in range(6):
        a = math.radians(60 * k + 30); post = lamp + Vector((0.17 * math.cos(a), 0.17 * math.sin(a), 0))
        metal.tube([post + Vector((0, 0, -0.72)), post + Vector((0, 0, -1.12))], 0.018, IRON, sides=4)
    glow.cylinder(0.15, 0.38, lamp + Vector((0, 0, -0.93)), GLOW['Stoutbough'], segments=6)
    # The grip.
    shaft.sleeve(leather, -2.05, -0.95, 0.025, SADDLE_DARK)
    for k in range(7): shaft.band(leather, -1.99 + k * 0.165, SADDLE, 0.025, sides=5)
    # A deep saddle: seat, cantle, pommel and skirts, held by two iron rings.
    leather.sphere(1, (0, 0.08, 0.26), SADDLE, segments=18, scale=(0.32, 0.58, 0.1))
    leather.sphere(1, (0, 0.6, 0.38), SADDLE, segments=14, scale=(0.3, 0.1, 0.2))
    leather.tube([(0, -0.42, 0.24), (0, -0.48, 0.42), (0, -0.52, 0.5)], [0.07, 0.06, 0.05], SADDLE_DARK, sides=8)
    leather.sphere(0.08, (0, -0.53, 0.53), SADDLE_DARK, segments=10)
    for s in (-1, 1):
        plate(leather, [(-0.4, 0.2), (0.62, 0.22), (0.56, -0.3), (-0.32, -0.26)], 0.04, SADDLE_DARK, 'yz', at=(s * 0.3, 0, 0))
    for y in (-0.5, 0.74): shaft.band(metal, y, IRON, 0.03)
    # Saddlebags slung over the shaft behind the saddle.
    for s in (-1, 1):
        leather.box((0.24, 0.5, 0.46), (s * 0.44, 1.0, -0.3), SADDLE)
        leather.box((0.27, 0.53, 0.17), (s * 0.45, 1.0, -0.1), SADDLE_DARK)
        metal.box((0.03, 0.09, 0.09), (s * 0.59, 1.0, -0.2), BRASS)
    leather.tube([(-0.44, 1.0, -0.08), (-0.24, 1.0, 0.2), (0, 1.0, 0.27), (0.24, 1.0, 0.2), (0.44, 1.0, -0.08)],
                 0.035, SADDLE_DARK, sides=6)
    # A plank footboard on two iron struts.
    shaft.band(metal, 0.5, IRON, 0.04)
    for s in (-1, 1): metal.tube([(s * 0.12, 0.5, -0.16), (s * 0.5, 0.56, -1.26)], 0.045, IRON, sides=6)
    wood.box((1.3, 0.34, 0.09), (0, 0.58, -1.3), OAK)

    def flare(f): return 0.27 + 0.6 * math.sin(math.pi / 2 * min(f / 0.55, 1)) - 0.16 * max(f - 0.72, 0) / 0.28
    tail(m['Bristles'], 1.2, 2.3, flare, HEATHER, 260, HEATHER_CORE, thick=(0.045, 0.016), droop=0.08)
    for y in (1.3, 1.48, 1.66): shaft.band(m['Bristles'], y, ROPE, 0.05, radius=flare((y - 1.2) / 2.3) + 0.03)


# Nightwing, the wild one.
THORN = (54, 45, 43); THORN_DARK = (36, 30, 30); PEWTER = (112, 106, 122); WRAP = (40, 30, 36)
RAVEN = ((34, 30, 40), (46, 38, 54), (28, 26, 32), (58, 46, 66)); RAVEN_CORE = (24, 22, 28)
FEATHER = ((22, 22, 28), (36, 34, 48), (30, 28, 40))


def nightwing(m):
    wood, metal, leather, glow = m['Wood'], m['Metal'], m['Leather'], m['Glow']
    ember = GLOW['Nightwing']
    # The tip curls up and back into a crook; the rest wanders a little either side of straight.
    shaft = Shaft(wood, [(0, -3.42, 0.98, 0.065), (0, -3.72, 0.92, 0.08), (0, -3.88, 0.66, 0.095),
                         (0, -3.72, 0.36, 0.11), (0.05, -3.3, 0.14, 0.12), (-0.06, -2.6, 0.02, 0.135),
                         (0.05, -1.8, -0.03, 0.14), (-0.03, -0.9, 0, 0.145), (0, 0, 0, 0.15), (0.03, 0.8, 0, 0.15),
                         (0, 1.6, 0, 0.14), (0, 2.4, 0, 0.13)], THORN, steps=7)
    ys = [-3.25 + 2.3 * k / 48 for k in range(49)]
    wood.tube([shaft.surface(y, 360 * (y + 3.25) / 0.8, 0.01) for y in ys], 0.035, THORN_DARK, sides=5)
    shaft.knots(wood, [(-2.95, 80, 0.06), (-2.35, 230, 0.065), (0.45, 300, 0.06), (0.75, 120, 0.05)], THORN_DARK)
    for _ in range(12):
        y, a = RNG.uniform(-3.2, -2.25), RNG.uniform(0, 360)
        out = Vector((math.cos(math.radians(a)), 0.45, math.sin(math.radians(a)))).normalized()
        wood.cylinder(0.035, 0.2, shaft.surface(y, a) + out * 0.08, THORN_DARK, top=0.003, turn=turn_to(out), segments=5)
    glow.sphere(0.12, (0, -3.62, 0.62), ember, segments=6, scale=(1, 1, 1.25))
    # A grip of dark leather between pewter collars.
    shaft.sleeve(leather, -1.95, -0.85, 0.022, WRAP)
    for k in range(8): shaft.band(leather, -1.89 + k * 0.142, shade(WRAP, 0.7), 0.02, sides=5)
    for y in (-2.0, -0.8): shaft.band(metal, y, PEWTER, 0.035, radius=0.2)
    # Branch stubs for stirrups, each with a thorn.
    for s in (-1, 1):
        wood.tube([(s * 0.08, 0.42, -0.1), (s * 0.28, 0.5, -0.55), (s * 0.34, 0.66, -1.02), (s * 0.58, 0.76, -1.22)],
                  [0.075, 0.065, 0.055, 0.04], THORN, sides=7)
        out = Vector((s, 0.3, 0.25)).normalized()
        wood.cylinder(0.03, 0.16, Vector((s * 0.33, 0.6, -0.78)) + out * 0.08, THORN_DARK, top=0.003, turn=turn_to(out), segments=5)

    def flare(f): return 0.2 + 0.58 * f ** 0.8
    tips = tail(m['Bristles'], 1.0, 3.0, flare, RAVEN, 230, RAVEN_CORE, thick=(0.032, 0.008), droop=0.07, squash=0.62,
                reach=(0.75, 1.15))
    # Raven feathers splayed out of the fan's sides and end.
    for k in range(18):
        s = -1 if k % 2 else 1
        phi = s * RNG.uniform(0.05, 0.45); length, width = RNG.uniform(1.2, 1.8), RNG.uniform(0.12, 0.16)
        base = (s * RNG.uniform(0.15, 0.35), RNG.uniform(1.6, 2.4))
        vane = [(0, 0), (0.7, 0.2), (1, 0.55), (0.6, 0.88), (0, 1), (-0.5, 0.85), (-0.9, 0.5), (-0.6, 0.18)]
        outline = [(base[0] + u * width * math.cos(phi) + v * length * math.sin(phi),
                    base[1] - u * width * math.sin(phi) + v * length * math.cos(phi)) for u, v in vane]
        plate(m['Bristles'], outline, 0.02, RNG.choice(FEATHER), 'xy', at=(0, 0, RNG.uniform(-0.14, 0.1)))
    for tip, _ in RNG.sample(tips, 45): glow.sphere(0.035, tip, ember, segments=6, scale=(1, 1.8, 1))
    # Pewter claws gripping the tail.
    shaft.band(metal, 0.95, PEWTER, 0.04)
    for k in range(5):
        a = 72 * k + 18
        metal.tube([ring_point(a, 0.16, 0.95, 0.75), ring_point(a, 0.3, 1.2, 0.75), ring_point(a, 0.36, 1.5, 0.75),
                    ring_point(a, 0.33, 1.75, 0.75), ring_point(a, 0.24, 1.9, 0.75)],
                   [0.045, 0.04, 0.032, 0.022, 0.008], PEWTER, sides=6)


def preview_rider():
    """A rider in a 5.5-stud avatar's proportions sitting Ashwind, for the previews and the .blend only: hands on the
    grip, feet on the stirrups."""
    rider, robe, trousers, skin = rbx.Mesh('_Preview rider'), (52, 58, 92), (44, 40, 38), (226, 190, 156)
    rider.box((1.6, 0.9, 0.7), (0, 0.05, 0.55), trousers)
    rider.box((1.8, 1.0, 1.6), (0, -0.25, 1.65), robe, turn=(20, 0, 0))
    rider.sphere(0.6, (0, -0.75, 2.85), skin, segments=16)
    for s, y in ((-1, -1.75), (1, -1.25)):
        rider.tube([(s * 0.95, -0.45, 2.25), (s * 0.62, -1.2, 1.3), (s * 0.2, y + 0.1, 0.3)], [0.3, 0.27, 0.25], robe, sides=8)
        rider.sphere(0.24, (s * 0.15, y, 0.24), skin, segments=10)
        rider.tube([(s * 0.45, 0.05, 0.4), (s * 0.6, -0.75, -0.35), (s * 0.5, 0.55, -1.08)], [0.32, 0.3, 0.26], trousers, sides=8)
        rider.box((0.5, 0.8, 0.34), (s * 0.5, 0.5, -1.1), shade(trousers, 0.8))
    return rider.finish(sharp=40)


rbx.scene('Brooms')
models = []
for k, (name, build) in enumerate((('Ashwind', ashwind), ('Swiftquill', swiftquill), ('Stoutbough', stoutbough),
                                   ('Nightwing', nightwing))):
    meshes = {n: rbx.Mesh(n, frame=Matrix.Translation((SPACING * k, 0, 0))) for n in MATERIALS}
    build(meshes)
    models.append(rbx.group(name, [meshes[n].finish(sharp=35) for n in MATERIALS]))
brooms = rbx.group('Brooms', models)
ground = rbx.Mesh('_Preview ground'); ground.box((60, 40, 0.1), (SPACING * 1.5, 0, -2.95), PLAZA); ground.finish()
rider = preview_rider()

rbx.viewport((SPACING * 1.5, 0, 0), 18, turn=(68, 0, 40))
rbx.export('Brooms', [brooms, *brooms.children_recursive], auto_preview=False)
for model in models:
    tris = {o.name.split('.')[0]: len(o.data.loop_triangles) for o in model.children}
    rbx.say(f'{model.name}: ' + ', '.join(f'{n} {t:,}' for n, t in tris.items()) + f' triangles; glow {GLOW[model.name]}')


def show(only=None, with_rider=False):
    """Hide every broom but `only` (all, if None) from the renders, and the rider unless asked for."""
    for k, model in enumerate(models):
        for o in model.children: o.hide_render = only is not None and k != only
    rider.hide_render = not with_rider


centre = SPACING * 1.5
show()
rbx.shot('Brooms', (centre + 9, -11, 5.5), (centre, 0.3, -0.3), lens=35, resolution=(1600, 900))
for k, model in enumerate(models):
    show(k)
    x = SPACING * k
    rbx.shot(f'Brooms_{model.name}', (x + 11, -1.5, 2.2), (x, 0.1, -0.15), lens=40, resolution=(1600, 800))
show(0, with_rider=True)
rbx.shot('Brooms_rider', (8, -7, 3.5), (0, 0, 0.6), lens=40, resolution=(1200, 1000))
show(with_rider=True)
# For the picture only (the files are already written): the Glow meshes shine as Neon does in game, and the
# exposure comes down for a close view over pale paving.
for model in models:
    for o in model.children:
        if o.name.split('.')[0] != 'Glow': continue
        bsdf = next(n for n in o.data.materials[0].node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        bsdf.inputs['Emission Color'].default_value = (*((c / 255) ** 2.2 for c in GLOW[model.name]), 1)
        bsdf.inputs['Emission Strength'].default_value = 6
bpy.context.scene.view_settings.exposure = -1.2
rbx.beauty('Brooms_picture', (centre + 13, -15, 6), (centre - 0.5, 0.3, -0.6), lens=40, resolution=(1920, 1080))
