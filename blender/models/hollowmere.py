"""Hollowmere remodelled: the village's four shops, six cottages, square furniture, road lamps, ferry dock and sky
ferry, rebuilt with what parts do badly. Windows sit in real openings with timber reveals, mullions and sills.
The half-timbering stands proud of the plaster, and the roofs are laid in rows of tiles over plastered,
framed gables. There are brick chimneys with pots, stone plinths in coursed blocks, plank doors with iron
straps, and raised lettering on the shop signs.

The layout is replayed from tools/build.py: the same footprints, walls, doors, windows, colours and night-light
pattern, so every door still meets its NPC prompt. The ground, square paving and lanes stay as the map's parts;
they appear here only in the previews and the .blend (_Preview ground).

Hollowmere.fbx holds one Model per building: a Building mesh, plus Lit window and Window glass meshes, named as
WorldService's night lights expect, and Display glass for Oakhart's bay. Street furniture, the Ferry dock
and the Sky ferry come with it. Imported with Insert Using Scene Position, it lands where the part village
stands. Run blender/after_import.lua afterwards; it also tidies Blender's .001 name suffixes.
"""
import math
import random
import xml.etree.ElementTree as ET
from mathutils import Matrix, Vector
import build
import rbx
from palette import (BEAM, BRICK, CLEAR_GLASS, COURSE, DOOR, FLOORBOARD, FOLIAGE, GOLD, GRANITE, HEDGE, IRON, LAMPLIGHT,
                     LIMESTONE, MEADOW, NIGHT_GLASS, PATH, PLANK, PLAZA, PLAZA_TILE, PLINTH, ROAD, SIGN_TEXT, SIGNBOARD,
                     SLATE, VILLAGE_STONE)

RNG = random.Random(1189)
TURN = {'+Z': 180, '+X': -90, '-X': 90, '-Z': 0}   # degrees that turn a door from -Y to face this way on the map
FACES = ('front', 'back', 'left', 'right')
AXES = {'front': ((1, 0, 0), (0, -1, 0)), 'back': ((-1, 0, 0), (0, 1, 0)),   # (along the face, out of the face)
        'left': ((0, -1, 0), (-1, 0, 0)), 'right': ((0, -1, 0), (1, 0, 0))}
POTS = (176, 98, 70); SAIL = (218, 209, 184); HULL = (77, 89, 105)
LIGHTS = [0]


def world(x, y, z):
    """A map position (studs, Y up) in Blender, Z up. The importer turns it back: Blender -X is the map's +X."""
    return Vector((-x, z, y))


def placement(x, z, facing='-Z'):
    return Matrix.Translation(world(x, 0, z)) @ Matrix.Rotation(math.radians(TURN[facing]), 4, 'Z')


def tone(colour, lo=0.9, hi=1.06): return build.shade(colour, RNG.uniform(lo, hi))


def lit():
    """Two windows in every three light up at night, as on the map."""
    LIGHTS[0] += 1
    return LIGHTS[0] % 3 < 2


def beam(mesh, p0, p1, normal, thick, width, colour):
    """A board from p0 to p1, `thick` along `normal` (which must be square to the run) and `width` across both."""
    p0, p1, n = Vector(p0), Vector(p1), Vector(normal).normalized()
    run = p1 - p0; m = Matrix.Identity(4)
    m.col[0], m.col[1] = (*run, 0), (*(n * thick), 0)
    m.col[2], m.col[3] = (*(run.normalized().cross(n) * width), 0), (*((p0 + p1) / 2), 1)
    return mesh.block(m, colour)


def replay():
    """Run the map builder once, noting the arguments of every house, lamp, bench and planter it places. Only the
    village's own houses count: the groundskeeper's hut by the forest (tools/grounds.py) is a timber house too."""
    calls = {}
    for name in ('timber_house', 'lamp', 'bench', 'planter'):
        def spy(*args, _real=getattr(build, name), _log=calls.setdefault(name, []), _name=name, **kw):
            if _name != 'timber_house' or args[0].findtext("Properties/string[@name='Name']") == 'Hollowmere':
                _log.append(args[1:])
            return _real(*args, **kw)
        setattr(build, name, spy)
    build.make_world(build.item(ET.Element('roblox'), 'Workspace', 'Workspace'))
    return calls


class Storey:
    """One storey's four wall faces in its house's frame, where the door wall faces -Y. A point on a face is
    (u, z): u runs along the face as tools/build.py's face_point() runs, and z is height."""

    def __init__(self, w, front, back, z0, h):
        self.w, self.yf, self.yb, self.z0, self.h, self.top = w, -front, back, z0, h, z0 + h
        self.yc = (back - front) / 2
        self.holes = {f: [] for f in FACES}   # (u0, u1, z0, z1) cut through the wall
        self.spans = {f: [] for f in FACES}   # (u, width) that framing posts keep clear of, as on the map

    def length(self, face): return self.w if face in ('front', 'back') else self.yb - self.yf

    def at(self, face, u, out, z):
        if face == 'front': return Vector((u, self.yf - out, z))
        if face == 'back': return Vector((-u, self.yb + out, z))
        return Vector(((self.w / 2 + out) * (1 if face == 'right' else -1), self.yc - u, z))

    def board(self, mesh, face, u0, u1, z0, z1, out, thick, colour):
        """A board on `face` over u0..u1 and z0..z1, its outer side `out` studs proud of the face."""
        a = Vector(AXES[face][0]); c = self.at(face, (u0 + u1) / 2, out - thick / 2, (z0 + z1) / 2)
        return beam(mesh, c - a * (u1 - u0) / 2, c + a * (u1 - u0) / 2, AXES[face][1], thick, z1 - z0, colour)

    def walls(self, mesh, colour, stone):
        """Walls 1 stud thick around every hole. The side walls fit between the front and back walls."""
        for face in FACES:
            half = self.length(face) / 2 - (1 if face in ('left', 'right') else 0)
            pieces, cursor = [], -half
            for u0, u1, z0, z1 in sorted(self.holes[face]):
                if u0 > cursor: pieces.append((cursor, u0, self.z0, self.top))
                if z0 > self.z0: pieces.append((u0, u1, self.z0, z0))
                if z1 < self.top: pieces.append((u0, u1, z1, self.top))
                cursor = u1
            if cursor < half: pieces.append((cursor, half, self.z0, self.top))
            for piece in pieces:
                if stone: self.ashlar(mesh, face, *piece)
                else: self.board(mesh, face, *piece, 0, 1, colour)

    def ashlar(self, mesh, face, u0, u1, z0, z1):
        """Dressed stone: a mortar core faced with staggered blocks."""
        self.board(mesh, face, u0, u1, z0, z1, -0.08, 0.92, build.shade(VILLAGE_STONE, 0.7))
        rows = max(1, round((z1 - z0) / 1.1))
        for r in range(rows):
            b0, b1 = z0 + (z1 - z0) * r / rows, z0 + (z1 - z0) * (r + 1) / rows
            edge = u0 - (1.1 if r % 2 else 0)
            while edge < u1:
                a, b = max(u0, edge), min(u1, edge + 2.2)
                if b - a > 0.3: self.board(mesh, face, a + 0.04, b - 0.04, b0 + 0.04, b1 - 0.04, 0, 0.12, tone(VILLAGE_STONE))
                edge += 2.2

    def framing(self, mesh):
        """Half-timbering as on the map: rails at sill and wall plate, posts at corners and beside openings, and
        braces in the open bays of the front and back walls, each leaning toward the middle."""
        for face in FACES:
            L = self.length(face)
            for z in (self.z0 + 0.2, self.top - 0.2):
                self.board(mesh, face, -L / 2 - 0.15, L / 2 + 0.15, z - 0.2, z + 0.2, 0.18, 0.22, BEAM)
            if face == 'front':
                posts = [-L / 2, L / 2] + [e for u, span in self.spans[face] for e in (u - span / 2 - 0.2, u + span / 2 + 0.2)]
            else:
                centres = sorted(u for u, _ in self.spans[face])
                posts = ([-L / 2, L / 2] if face == 'back' else []) + [(a + b) / 2 for a, b in zip(centres, centres[1:])]
            kept = []
            for p in sorted(p for p in posts if abs(p) <= L / 2):
                if not kept or p - kept[-1] > 1.2: kept.append(p)
            for p in kept: self.board(mesh, face, p - 0.2, p + 0.2, self.z0 + 0.4, self.top - 0.4, 0.16, 0.2, BEAM)
            if face not in ('front', 'back'): continue
            for a, b in zip(kept, kept[1:]):
                if b - a >= 2 and not any(a < u < b for u, _ in self.spans[face]):
                    outer, inner = (a + 0.2, b - 0.2) if abs(a) > abs(b) else (b - 0.2, a + 0.2)
                    beam(mesh, self.at(face, outer, 0.08, self.z0 + 0.4), self.at(face, inner, 0.08, self.top - 0.4),
                         AXES[face][1], 0.18, 0.3, BEAM)

    def window(self, house, face, u, ww, wh, stone):
        """A window in a real opening: glass set back, a timber-lined reveal, mullion and transom, a sill, and on
        the street side shutters and a window box of flowers (or the apothecary's bottles)."""
        spec, T = house.spec, house.body
        z = self.z0 + self.h * 0.55; z0, z1, a, b = z - wh / 2, z + wh / 2, u - ww / 2, u + ww / 2
        shutter = spec.get('shutter') if face == 'front' else None
        self.holes[face].append((a, b, z0, z1)); self.spans[face].append((u, ww + (2.2 if shutter else 0.6)))
        on = lit()
        self.board(house.lit if on else house.dark, face, a, b, z0, z1, -0.45, 0.1, LAMPLIGHT if on else NIGHT_GLASS)
        for piece in ((a, a + 0.18, z0, z1), (b - 0.18, b, z0, z1), (a, b, z1 - 0.18, z1)):
            self.board(T, face, *piece, 0.1, 0.6, BEAM)
        self.board(T, face, u - 0.07, u + 0.07, z0, z1, -0.32, 0.12, BEAM)
        if wh >= 2.4: self.board(T, face, a, b, z0 + wh * 0.62 - 0.07, z0 + wh * 0.62 + 0.07, -0.32, 0.12, BEAM)
        self.board(T, face, a - 0.35, b + 0.35, z0 - 0.24, z0 + 0.02, 0.32, 1.32, LIMESTONE if stone else BEAM)
        if stone: self.board(T, face, a - 0.3, b + 0.3, z1, z1 + 0.5, 0.08, 0.2, LIMESTONE)
        if shutter:
            for side in (-1, 1):
                c = u + side * (ww / 2 + 0.55)
                for k in range(3): self.board(T, face, c - 0.43 + 0.3 * k, c - 0.17 + 0.3 * k, z0, z1, 0.22, 0.1, tone(shutter))
                beam(T, self.at(face, c - 0.33 * side, 0.25, z0 + 0.25), self.at(face, c + 0.33 * side, 0.25, z1 - 0.25),
                     AXES[face][1], 0.05, 0.14, build.shade(shutter, 0.72))
        if face != 'front': return
        self.board(T, face, a - 0.2, b + 0.2, z0 - 0.8, z0 - 0.3, 0.85, 0.55, BEAM)
        bottles = spec.get('sill') == 'bottles' and self.z0 < 1
        n = max(2, round(ww / 0.5))
        for i in range(n):
            p = self.at(face, a + (i + 0.5) * ww / n, 0.57, z0 - 0.3)
            if bottles:
                colour = build.BOTTLES[i % 3]
                T.cylinder(0.16, 0.5, p + Vector((0, 0, 0.25)), colour, top=0.12, segments=8)
                T.cylinder(0.06, 0.2, p + Vector((0, 0, 0.6)), colour, segments=6)
            else:
                T.sphere(RNG.uniform(0.2, 0.28), p + Vector((0, 0, 0.1)), RNG.choice(build.FLOWERS + (HEDGE,)), segments=8)

    def door(self, house):
        """The doorway as on the map, with its leaves swung open inside, now framed in heavy timber with knee
        braces, a granite threshold, plank leaves with iron straps and ring pulls, and the shop's lettered sign."""
        spec, T = house.spec, house.body
        (dw, dh), z0 = spec['door'], self.z0
        self.holes['front'].append((-dw / 2, dw / 2, z0, z0 + dh)); self.spans['front'].append((0, dw + 0.8))
        for side in (-1, 1):
            self.board(T, 'front', side * dw / 2, side * (dw / 2 + 0.45), z0, z0 + dh, 0.3, 0.6, BEAM)
            foot = self.at('front', side * (dw / 2 + 0.2), 0.24, z0 + dh - 1.0)
            beam(T, foot, self.at('front', side * (dw / 2 - 0.6), 0.24, z0 + dh), (0, -1, 0), 0.2, 0.28, BEAM)
        self.board(T, 'front', -dw / 2 - 0.6, dw / 2 + 0.6, z0 + dh, z0 + dh + 0.5, 0.35, 0.65, BEAM)
        self.board(T, 'front', -dw / 2, dw / 2, z0 - 0.02, z0 + 0.06, 0.25, 1.25, GRANITE)
        leaves = (-1, 1) if dw >= 6 else (-1,)
        leaf, colour = dw / len(leaves), spec.get('door_color', DOOR)
        planks = max(2, round(leaf / 0.75))
        for side in leaves:
            x = side * (dw / 2 - 0.2)
            for k in range(planks):
                T.box((0.22, leaf / planks - 0.05, dh - 0.2), (x, self.yf + 1 + leaf * (k + 0.5) / planks, z0 + dh / 2), tone(colour))
            for zb in (z0 + dh * 0.22, z0 + dh * 0.78):
                T.box((0.06, leaf * 0.85, 0.22), (x - side * 0.14, self.yf + 1 + leaf * 0.45, zb), IRON)
            T.torus(0.16, 0.035, (x - side * 0.16, self.yf + 1 + leaf * 0.85, z0 + dh / 2), IRON, turn=(0, 90, 0), segments=10, sides=4)
        if spec.get('sign'):
            zs, bw = z0 + dh + 0.95, dw + 1.5
            self.board(T, 'front', -bw / 2, bw / 2, zs - 0.45, zs + 0.45, 0.55, 0.16, SIGNBOARD)
            for piece in ((-bw / 2, bw / 2, zs + 0.37, zs + 0.45), (-bw / 2, bw / 2, zs - 0.45, zs - 0.37),
                          (-bw / 2, -bw / 2 + 0.08, zs - 0.45, zs + 0.45), (bw / 2 - 0.08, bw / 2, zs - 0.45, zs + 0.45)):
                self.board(T, 'front', *piece, 0.6, 0.06, GOLD)
            T.text(spec['sign'], self.at('front', 0, 0.57, zs), SIGN_TEXT, height=0.46, width=bw - 0.8)


class House:
    """One timber house from tools/build.py's spec, modelled around its centre with the door toward -Y."""

    def __init__(self, name, cx, cz, facing, spec):
        frame = placement(cx, cz, facing)
        self.name, self.spec = name, spec
        self.body, self.lit, self.dark, self.display = (rbx.Mesh(n, frame) for n in ('Building', 'Lit window', 'Window glass', 'Display glass'))

    def build(self):
        spec = self.spec; w, d, jetty = spec['w'], spec['d'], spec.get('jetty', 0)
        self.plinth()
        z0 = 0.7
        for level, h in enumerate(spec['heights']):
            s = Storey(w, d / 2 + (jetty if level else 0), d / 2, z0, h)
            stone = level == 0 and spec.get('ground') == 'stone'
            if level == 0:
                s.door(self)
                if spec.get('bay'): s.spans['front'].append((-(spec['door'][0] / 2 + (w - spec['door'][0]) / 4), 6.4))
            elif jetty: self.jetty(jetty, z0)
            for face, u, ww, wh in spec['windows'][level]: s.window(self, face, u, ww, wh, stone)
            s.walls(self.body, spec['plaster'], stone)
            if not stone: s.framing(self.body)
            z0 += h
        self.roof(-(d / 2 + jetty), d / 2, z0)
        for feature in spec.get('features', ()): FEATURES[feature.__name__](self)
        return rbx.group(self.name, [m.finish(sharp=35) for m in (self.body, self.lit, self.dark, self.display)])

    def plinth(self):
        """The 0.7-stud stone base the NPCs stand on: coursed blocks over a mortar core, a granite coping, the
        floorboards and two steps up to the door."""
        T, (w, d), (dw, _) = self.body, (self.spec['w'], self.spec['d']), self.spec['door']
        W, D = w + 0.6, d + 0.6
        T.box((W - 0.16, D - 0.16, 0.7), (0, 0, 0.35), build.shade(PLINTH, 0.62))
        for horizontal, sign, length in ((True, -1, W), (True, 1, W), (False, -1, D), (False, 1, D)):
            for r, (z0, z1) in enumerate(((0, 0.35), (0.35, 0.7))):
                u = -length / 2 - (0.6 if r else 0)
                while u < length / 2:
                    step = RNG.uniform(1.4, 2.4); a, b = max(-length / 2, u), min(length / 2, u + step)
                    if b - a > 0.25:
                        size, mid = (b - a - 0.06, z1 - z0 - 0.06), (a + b) / 2
                        if horizontal: T.box((size[0], 0.14, size[1]), (mid, sign * (D / 2 - 0.07), (z0 + z1) / 2), tone(PLINTH))
                        else: T.box((0.14, size[0], size[1]), (sign * (W / 2 - 0.07), mid, (z0 + z1) / 2), tone(PLINTH))
                    u += step
        for sign in (-1, 1):
            T.box((W + 0.2, 0.5, 0.14), (0, sign * (D / 2 - 0.15), 0.77), GRANITE)
            T.box((0.5, D + 0.2, 0.14), (sign * (W / 2 - 0.15), 0, 0.77), GRANITE)
        T.box((w - 1.2, d - 1.2, 0.05), (0, 0, 0.725), FLOORBOARD)
        T.box((dw + 1.4, 1.5, 0.24), (0, -(D / 2 + 0.75), 0.12), tone(GRANITE))
        T.box((dw + 1.0, 0.75, 0.48), (0, -(D / 2 + 0.375), 0.24), tone(GRANITE))

    def jetty(self, jetty, z):
        """The upper storey's overhang: a bressumer beam, joist ends and four carved corbels."""
        T, w, d = self.body, self.spec['w'], self.spec['d']
        T.box((w, jetty, 0.5), (0, -d / 2 - jetty / 2, z - 0.25), BEAM)
        n, clear = int(w / 1.4), (self.spec['door'][0] + 2.1) / 2 if self.spec.get('sign') else 0
        for i in range(n + 1):
            x = -w / 2 + 0.2 + (w - 0.4) * i / n
            if abs(x) < clear: continue   # keep the shop sign below in view
            T.box((0.3, jetty + 0.25, 0.3), (x, -d / 2 - jetty / 2 - 0.1, z - 0.65), build.shade(BEAM, 0.85))
        for x in (-w / 2 + 1, -w / 4, w / 4, w / 2 - 1):
            T.prism([(0, 0), (jetty, 0), (0, -1.6)], 0.5, (x, -d / 2, z - 0.5), BEAM, turn=(0, 0, -90))

    def roof(self, yf, yb, top):
        """A gabled roof over boarding: staggered rows of tiles, fascia and barge boards, a ridge roll, plastered
        and framed gable ends (shops get an attic window), and a coursed brick chimney with pots."""
        spec, T, w = self.spec, self.body, self.spec['w']
        rh, over, eave, colour = spec.get('pitch', 6), 1, 1.2, spec['roof']
        yc, half, X = (yf + yb) / 2, (yb - yf) / 2 + eave, w / 2 + over
        ridge = Vector((0, yc, top + rh)); rows = max(4, round(math.hypot(half, rh) / 0.8))
        for side in (-1, 1):
            eaves = Vector((0, yc + side * half, top)); n = Vector((0, side * rh, half)).normalized()
            beam(T, eaves + n * 0.15, ridge + n * 0.15, n, 0.3, 2 * X, build.shade(colour, 0.7))
            for r in range(rows):
                lo, hi = eaves.lerp(ridge, r / rows), eaves.lerp(ridge, min(1, (r + 1.25) / rows))
                x0 = -X - (2.0 if r % 2 else 0)
                while x0 < X:
                    a, b = max(-X, x0), min(X, x0 + 4.0)
                    if b - a > 0.4:
                        mid = Vector(((a + b) / 2, 0, 0))
                        beam(T, lo + mid + n * 0.42, hi + mid + n * 0.34, n, 0.14, b - a - 0.05, tone(colour, 0.85, 1.08))
                    x0 += 4.0
            beam(T, eaves + Vector((-X - 0.15, side * 0.05, -0.2)), eaves + Vector((X + 0.15, side * 0.05, -0.2)), (0, side, 0), 0.14, 0.6, BEAM)
            for gx in (-X - 0.1, X + 0.1):
                beam(T, eaves + Vector((gx, 0, 0)) + n * 0.3, ridge + Vector((gx, 0, 0)) + n * 0.3, (1, 0, 0), 0.2, 0.7, BEAM)
        T.cylinder(0.34, 2 * X + 0.4, ridge + Vector((0, 0, 0.42)), build.shade(colour, 0.6), turn=(0, 90, 0), segments=8)
        rise = rh * eave / half   # where the roof's underside crosses the front and back wall faces
        plaster = spec['plaster']
        for gx in (-1, 1):
            T.prism([(yf, top), (yb, top), (yb, top + rise), (yc, top + rh), (yf, top + rise)], 1.0,
                    (gx * (w / 2 - 0.5), 0, 0), plaster, turn=(0, 0, 90))
            n, fx = Vector((gx, 0, 0)), gx * (w / 2 + 0.08)
            P = lambda y, z: Vector((fx, y, z))
            zc = top + rh * 0.5; ya = yf + (zc - top - rise) / (rh - rise) * (yc - yf)
            beam(T, P(ya + 0.3, zc), P(2 * yc - ya - 0.3, zc), n, 0.18, 0.4, BEAM)   # collar
            if w >= 20:
                glass = self.lit if lit() else self.dark
                beam(glass, P(yc - 0.9, top + 2.0), P(yc + 0.9, top + 2.0), n, 0.06, 1.6, LAMPLIGHT if glass is self.lit else NIGHT_GLASS)
                for y0, y1, z0, z1 in ((yc - 1.1, yc - 0.9, top + 1.2, top + 2.8), (yc + 0.9, yc + 1.1, top + 1.2, top + 2.8),
                                       (yc - 1.1, yc + 1.1, top + 0.95, top + 1.2), (yc - 1.1, yc + 1.1, top + 2.8, top + 3.0)):
                    beam(T, P(y0, (z0 + z1) / 2), P(y1, (z0 + z1) / 2), n, 0.2, z1 - z0, BEAM)
                beam(T, P(yc - 0.06, top + 3.0), P(yc + 0.06, top + 3.0), n, 0.2, 0.1, BEAM)
                beam(T, P(yc, zc + 0.2), P(yc, top + rh - 0.6), n, 0.18, 0.4, BEAM)
            else:
                beam(T, P(yc, top + 0.2), P(yc, top + rh - 0.6), n, 0.18, 0.4, BEAM)   # king post
                for s in (-1, 1): beam(T, P(yc, top + 0.5), P(yc + s * (yc - ya - 0.6), zc - 0.2), n, 0.16, 0.3, BEAM)
        cx, cy, z = w / 2 - 2.5, yc + half / 2, top
        course = 0
        while z < top + rh + 2.2:
            hgt = min(0.42, top + rh + 2.2 - z); inset = 0.05 if course % 2 else 0
            T.box((2 - inset, 2 - inset, hgt), (cx, cy, z + hgt / 2), tone(BRICK, 0.85, 1.05))
            z += hgt; course += 1
        T.box((2.4, 2.4, 0.25), (cx, cy, z + 0.125), COURSE)
        T.box((2.7, 2.7, 0.22), (cx, cy, z + 0.36), SLATE)
        for dx in (-0.45, 0.45): T.cylinder(0.26, 0.8, (cx + dx, cy, z + 0.87), POTS, top=0.2, segments=10)


def bay_window(house):
    """Oakhart's display bay, glazed on three sides, with a rack of wands under its own tiled lean-to."""
    s, T, G = house.spec, house.body, house.display
    w, d, dw = s['w'], s['d'], s['door'][0]
    u, y = -(dw / 2 + (w - dw) / 4), -d / 2
    T.box((5.6, 1.7, 1.0), (u, y - 0.85, 1.2), GRANITE)
    T.box((5.2, 0.1, 3.8), (u, y - 0.06, 3.6), (44, 36, 48))
    T.box((4.8, 0.6, 0.3), (u, y - 0.9, 2.0), BEAM)
    for i, colour in enumerate(((150, 112, 72), (60, 48, 44), (214, 206, 190), (118, 70, 52), (96, 80, 64))):
        x, z = u - 2 + i, 2.95 + 0.15 * (i % 2)
        T.cylinder(0.07, 1.6, (x, y - 0.9, z), colour, top=0.04, segments=6)
        T.sphere(0.09, (x, y - 0.9, z + 0.82), GOLD, segments=6)
    G.box((5.2, 0.08, 3.8), (u, y - 1.62, 3.6), CLEAR_GLASS)
    for k in (-1, 1):
        G.box((0.08, 1.5, 3.8), (u + k * 2.62, y - 0.85, 3.6), CLEAR_GLASS)
        T.box((0.3, 0.3, 3.8), (u + k * 2.65, y - 1.6, 3.6), BEAM)
    T.box((5.6, 0.3, 0.3), (u, y - 1.6, 5.4), BEAM); T.box((5.6, 0.3, 0.25), (u, y - 1.6, 1.82), BEAM)
    eaves, head = Vector((u, y - 2.1, 5.55)), Vector((u, y, 6.3))
    n = Vector((0, -0.75, 2.1)).normalized()
    for r in range(3):
        beam(T, eaves.lerp(head, r / 3) + n * 0.12, eaves.lerp(head, (r + 1.3) / 3) + n * 0.05, n, 0.14, 6.4, tone(s['roof']))


def columns(house):
    """Marble columns either side of the bank door: a moulded base, a slightly swelling shaft and a capital."""
    s, T = house.spec, house.body
    d, (dw, dh) = s['d'], s['door']
    for side in (-1, 1):
        x, y = side * (dw / 2 + 1.1), -(d / 2 + 1.3)
        T.box((1.6, 1.6, 0.35), (x, y, 0.175), (196, 192, 182))
        T.lathe([(0, 0.35), (0.72, 0.35), (0.72, 0.5), (0.58, 0.62), (0.55, 0.8), (0.5, dh + 0.25), (0.58, dh + 0.5),
                 (0.7, dh + 0.68), (0, dh + 0.68)], (214, 210, 200), at=(x, y, 0), segments=16)
        T.box((1.6, 1.6, 0.35), (x, y, dh + 0.855), (196, 192, 182))


def herb_planters(house):
    """Plank troughs of herbs and lavender either side of the apothecary door."""
    s, T = house.spec, house.body
    d, dw = s['d'], s['door'][0]
    for side in (-1, 1):
        x, y = side * (dw / 2 + 2.6), -(d / 2 + 0.9)
        for k in range(3): T.box((3.2, 1.0, 0.17), (x, y, 0.085 + 0.17 * k), tone(BEAM))
        T.box((3.0, 0.8, 0.04), (x, y, 0.52), (70, 52, 40))
        for k in (-1, 0, 1): T.sphere(0.45, (x + k * 0.95, y, 0.85), (88, 132 + 20 * k, 78), segments=8)
        for j in range(4): T.cylinder(0.05, 0.6, (x - 1.3 + j * 0.85, y + 0.3, 0.85), (156, 110, 206), segments=4)


def awnings(house):
    """Striped awnings with pennant valances on iron stays over the tailor's windows, and a bench of fabric bolts."""
    s, T = house.spec, house.body
    w, d, dw = s['w'], s['d'], s['door'][0]
    tilt, reach, strips = 0.35, 2.2, 6
    drop = Vector((0, -reach * math.cos(tilt), -reach * math.sin(tilt)))
    n = Vector((0, -math.sin(tilt), math.cos(tilt)))
    for side in (-1, 1):
        u, span = side * (dw / 2 + (w - dw) / 4), 7.6
        for i in range(strips):
            root = Vector((u - span / 2 + span / strips * (i + 0.5), -(d / 2 + 0.15), 8.0))
            colour = (182, 62, 72) if i % 2 == 0 else (236, 226, 206)
            beam(T, root, root + drop, n, 0.08, span / strips, colour)
            T.prism([(-span / strips / 2, 0), (span / strips / 2, 0), (0, -0.45)], 0.06, root + drop + Vector((0, -0.02, -0.02)), colour)
        for k in (-1, 1):
            beam(T, Vector((u + k * span / 2, -d / 2, 6.9)), Vector((u + k * span / 2, -d / 2 + drop.y, 8.0 + drop.z)), (1, 0, 0), 0.08, 0.08, IRON)
    x, y = -(dw / 2 + 3.2), -(d / 2 + 1.0)
    T.box((3.6, 1.2, 0.12), (x, y, 0.84), BEAM)
    for lx in (-1.6, 1.6):
        for ly in (-0.45, 0.45): T.box((0.15, 0.15, 0.8), (x + lx, y + ly, 0.4), BEAM)
    for i, colour in enumerate(((126, 72, 140), (70, 110, 160), (196, 150, 70))):
        T.cylinder(0.3, 2.8, (x, y + 0.35 - 0.35 * i, 1.2), colour, turn=(0, 90, 0), segments=10)


FEATURES = {f.__name__: f for f in (bay_window, columns, herb_planters, awnings)}


def lamp(posts, lanterns, x, z, side, axis='x'):
    """The village's iron lamp post: a turned granite base, a ringed post with a finial, an arm with a scroll
    bracket and a hexagonal lantern hung where the map hangs it."""
    dx, dz = (side, 0) if axis == 'x' else (0, side)
    frame = Matrix.Translation(world(x, 0, z)) @ Matrix.Rotation(math.atan2(dz, -dx), 4, 'Z')   # local +X: the lantern side
    posts.frame = lanterns.frame = frame
    posts.lathe([(0, 0), (0.62, 0), (0.62, 0.3), (0.45, 0.42), (0.36, 0.8), (0.24, 0.92), (0, 0.92)], GRANITE, segments=12)
    posts.cylinder(0.17, 6.6, (0, 0, 4.2), IRON, top=0.13, segments=10)
    for zr in (1.05, 4.2): posts.torus(0.2, 0.06, (0, 0, zr), IRON, segments=12, sides=5)
    posts.sphere(0.2, (0, 0, 7.6), IRON, segments=8)
    posts.cylinder(0.07, 1.8, (0.9, 0, 7.25), IRON, turn=(0, 90, 0), segments=6)
    posts.torus(0.42, 0.05, (0.45, 0, 6.85), IRON, turn=(90, 0, 0), segments=12, sides=4, arc=270)
    posts.cylinder(0.04, 0.3, (1.6, 0, 7.05), IRON, segments=4)
    posts.cylinder(0.48, 0.3, (1.6, 0, 6.78), IRON, top=0.08, segments=6)
    posts.cylinder(0.38, 0.07, (1.6, 0, 6.62), IRON, segments=6); posts.cylinder(0.36, 0.08, (1.6, 0, 5.76), IRON, segments=6)
    posts.cylinder(0.14, 0.25, (1.6, 0, 5.6), IRON, top=0.02, segments=6)
    lanterns.cylinder(0.32, 0.8, (1.6, 0, 6.2), LAMPLIGHT, segments=6)


def bench(m, x, z, top):
    """A slatted bench on cast-iron ends, its back toward the map's +Z as on the map."""
    m.frame = Matrix.Translation(world(x, top, z))
    for k in range(4): m.box((4.0, 0.26, 0.1), (0, -0.45 + 0.3 * k, 0.9), tone(PLANK))
    for k in range(3): m.box((4.0, 0.08, 0.22), (0, 0.6 + 0.05 * k, 1.2 + 0.27 * k), tone(PLANK), turn=(-12, 0, 0))
    for x0 in (-1.75, 1.75):
        for p0, p1 in (((x0, -0.55, 0), (x0, -0.5, 0.85)), ((x0, 0.45, 0), (x0, 0.75, 1.9)), ((x0, -0.6, 1.25), (x0, 0.5, 1.3)),
                       ((x0, -0.6, 0.82), (x0, 0.5, 0.82))):
            beam(m, p0, p1, (1, 0, 0), 0.12, 0.14, IRON)
        m.torus(0.15, 0.04, (x0, -0.6, 1.1), IRON, turn=(0, 90, 0), segments=10, sides=4)


def planter(m, x, z, top):
    """A coursed brick planter with a granite coping, a clipped shrub and a few flowers."""
    m.frame = Matrix.Translation(world(x, top, z))
    for r in range(3): m.box((2.44 - (0.05 if r % 2 else 0),) * 2 + (0.3,), (0, 0, 0.15 + 0.3 * r), tone(BRICK, 0.85, 1.05))
    m.box((2.8, 2.8, 0.16), (0, 0, 0.98), GRANITE)
    for (sx, sy, sz, r), tint in zip(((0, 0, 1.75, 0.95), (0.45, 0.3, 1.55, 0.7), (-0.4, -0.35, 1.6, 0.72), (0.1, -0.5, 2.15, 0.55)),
                                     (HEDGE,) + FOLIAGE):
        m.sphere(r, (sx, sy, sz), tint, segments=10)
    for _ in range(6):
        a = RNG.uniform(0, math.tau)
        m.sphere(0.14, (0.85 * math.cos(a), 0.85 * math.sin(a), RNG.uniform(1.6, 2.3)), RNG.choice(build.FLOWERS), segments=6)


def ferry_dock(m):
    """The dock where the sky ferry moors (26 x 30 studs, top at 1): planks over a frame, with posts and ropes."""
    m.frame = Matrix.Translation(world(90, 0, 206))
    m.box((26, 30, 0.75), (0, 0, 0.375), build.shade(PLANK, 0.55))
    for k in range(32): m.box((26, 30 / 32 - 0.08, 0.25), (0, -15 + 30 * (k + 0.5) / 32, 0.875), tone(PLANK, 0.85, 1.08))
    for side in (-1, 1):
        m.box((26.4, 0.4, 0.5), (0, side * 15, 0.75), build.shade(PLANK, 0.7))
        m.box((0.4, 30.4, 0.5), (side * 13, 0, 0.75), build.shade(PLANK, 0.7))
        for y in range(-15, 16, 5):
            m.cylinder(0.3, 2.4, (side * 13, y, 1.0), build.shade(PLANK, 0.65), segments=8)
            m.sphere(0.32, (side * 13, y, 2.2), build.shade(PLANK, 0.6), segments=8)
            if y < 15: m.cylinder(0.05, 5, (side * 13, y + 2.5, 1.9), (188, 160, 110), turn=(90, 0, 0), segments=4)


def sky_ferry(hull, sail, lights):
    """The sky ferry, moored over the dock as on the map, its deck at the map's height (7.5): a planked hull with
    a gold wale, deck boards, rails, a mast and yard with a bellied sail, gilded sky fins, stern lanterns and a wheel."""
    for m in (hull, sail, lights): m.frame = Matrix.Translation(world(90, 0, 213))
    top, fx = 7.38, (1, 0.98, 0.9, 0.7, 0.38, 0)   # outline from the deck edge down to the keel, as fractions
    fz = (1, 0.8, 0.55, 0.3, 0.06, 0)

    def beam_at(t):   # half-beam and keel height along the hull: t runs from -1 (stern) to 1 (bow, the map's +Z)
        return 10 * (1 - abs(t) ** 2.4 * (0.75 if t > 0 else 0.35)), 1.5 + 2.2 * abs(t) ** 3 * (1 if t > 0 else 0.5)

    sections = []
    for k in range(17):
        t = -1 + 2 * k / 16; b, keel = beam_at(t)
        side = [(b * x, keel + (top - keel) * z) for x, z in zip(fx, fz)]
        sections.append((14.5 * t, [(-x, z) for x, z in side] + [(x, z) for x, z in reversed(side[:-1])]))
    # One colour per outline edge: the gold wale, three planks, the keel pair, three planks, the wale, the deck.
    planks = [build.shade(HULL, 1.0 if k % 2 else 0.88) for k in range(3)]
    strakes = [GOLD] + planks + [build.shade(HULL, 0.8)] * 2 + planks[::-1] + [GOLD, (145, 116, 81)]
    hull.loft(sections, HULL, colours=strakes)
    for i in range(20):
        x = -9.5 + 19 * (i + 0.5) / 20
        ts = [k / 50 - 1 for k in range(101) if beam_at(k / 50 - 1)[0] > abs(x) + 0.35]
        if ts: hull.box((0.9, 14.5 * (ts[-1] - ts[0]), 0.12), (x, 14.5 * (ts[0] + ts[-1]) / 2, top + 0.06), tone((145, 116, 81)))
    for s in (-1, 1):
        rail = [Vector((s * (beam_at(t)[0] - 0.3), 14.5 * t, top + 1.2)) for t in (k / 8 - 1 for k in range(1, 16))]
        for p in rail: hull.cylinder(0.09, 1.2, p - Vector((0, 0, 0.6)), (120, 86, 58), segments=6)
        for p0, p1 in zip(rail, rail[1:]): beam(hull, p0, p1, (0, 0, 1), 0.12, 0.22, (120, 86, 58))
        hull.prism([(0, -6), (0, 5), (5.5 * s, -3)], 0.12, (s * 9.6, 0, 4.6), GOLD, turn=(90, -15 * s, 0))
        hull.cylinder(0.08, 1.6, (s * 6.5, -13.2, top + 0.8), IRON, segments=6)
        hull.cylinder(0.36, 0.25, (s * 6.5, -13.2, top + 2.25), IRON, top=0.06, segments=6)
        lights.cylinder(0.28, 0.6, (s * 6.5, -13.2, top + 1.85), LAMPLIGHT, segments=6)
    hull.cylinder(0.32, 18, (0, 0, top + 9), (120, 86, 58), top=0.22, segments=12)
    for zr in (top + 0.6, top + 8, top + 15.5): hull.torus(0.34, 0.07, (0, 0, zr), GOLD, segments=12, sides=4)
    hull.cylinder(0.18, 12, (0, 0.35, top + 16), (120, 86, 58), turn=(0, 90, 0), segments=8)
    for i in range(8):
        x = -5.5 + 11 * (i + 0.5) / 8
        sail.box((11 / 8 + 0.02, 0.08, 10.2), (x, 0.55 + 0.9 * (1 - (x / 5.5) ** 2), top + 10.6), tone(SAIL, 0.95, 1.03),
                 turn=(0, 0, math.degrees(math.atan(-2 * 0.9 * x / 5.5 ** 2))))
    hull.box((0.8, 0.8, 0.9), (0, -11.5, top + 0.45), (120, 86, 58))
    hull.torus(0.8, 0.06, (0, -11.5, top + 1.75), (120, 86, 58), turn=(90, 0, 0), segments=16, sides=4)
    for a in (0, 60, 120): hull.cylinder(0.04, 1.8, (0, -11.5, top + 1.75), (120, 86, 58), turn=(0, a, 0), segments=4)


def preview_ground():
    """The meadow, approach road, square with its checker paving, shop lanes and garden paths, laid as on the map,
    for the previews and the .blend only. In the game these stay the map's own parts."""
    g = rbx.Mesh('_Preview ground')
    g.box((420, 360, 0.1), world(85, -0.05, 140), MEADOW)
    g.box((22, 210, 0.375), world(85, 0.19, 55), ROAD)
    g.box((68, 65, 0.4), world(88, 0.25, 147), PLAZA)
    tw, td = 68 / 8, 65 / 8
    for i in range(8):
        for j in range(8):
            if (i + j) % 2: g.box((tw - 0.3, td - 0.3, 0.02), world(54 + tw * (i + 0.5), 0.46, 114.5 + td * (j + 0.5)), PLAZA_TILE)
    for (x, z), (w, d) in build.LANES: g.box((w, d, 0.4), world(x, 0.25, z), PLAZA)
    for (x, z), (w, d) in build.GARDEN_PATHS: g.box((w, d, 0.1), world(x, 0.05, z), PATH)
    return g.finish()


calls = replay()
rbx.scene('Hollowmere')
houses = [House(*args).build() for args in calls['timber_house']]
posts, lanterns, seats, planters = (rbx.Mesh(n) for n in ('Lamp posts', 'Lantern', 'Benches', 'Planters'))
for args in calls['lamp']:
    if len(args) == 3 and args[1] >= 60: lamp(posts, lanterns, *args)   # the road lamps in the village, not the academy's
for args in calls['bench']: bench(seats, *(args + (0.45,))[:3])
for args in calls['planter']: planter(planters, *(args + (0.45,))[:3])
dock = rbx.Mesh('Ferry dock'); ferry_dock(dock)
hull, sail, ferry_lights = rbx.Mesh('Hull'), rbx.Mesh('Sail'), rbx.Mesh('Lantern')
sky_ferry(hull, sail, ferry_lights)
furniture = rbx.group('Street furniture', [m.finish(sharp=35) for m in (posts, lanterns, seats, planters)])
ferry = rbx.group('Sky ferry', [m.finish(sharp=35) for m in (hull, sail, ferry_lights)])
village = rbx.group('Hollowmere', houses + [furniture, dock.finish(sharp=35), ferry])
preview_ground()
rbx.viewport(world(88, 0, 150), 230, turn=(55, 0, 153))
rbx.export('Hollowmere', [village, *village.children_recursive], auto_preview=False)
rbx.shot('Hollowmere', world(25, 110, 265), world(85, 0, 140), lens=30)
rbx.shot('Hollowmere_square', world(88, 7, 162), world(88, 8, 104), lens=26)
rbx.shot('Hollowmere_oakhart', world(68, 7, 140), world(49, 6.5, 118), lens=30)
rbx.shot('Hollowmere_cottage', world(44, 5, 122), world(22, 4, 128), lens=32)
rbx.shot('Hollowmere_ferry', world(58, 18, 248), world(90, 8, 210), lens=32)
