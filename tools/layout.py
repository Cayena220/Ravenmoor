"""Ravenmoor's layout: where the academy and Whisperwood stand from Hollowmere, the roads between them, the land
round them and the Castle Grounds landmarks on it.

tools/build.py's builders lay every area out beside the village, where the map was first made, at the points in
build.LAID_OUT. lay() then moves the academy, with its grounds, yard, duel arena and Mirrorlake, 300 studs north,
and Whisperwood, with Tobb, 300 west, so the walks between them take half a minute. It carries the academy road and
the forest path out to them and lays a forest road straight from the academy gate to the forest path. It also
carries the west wing's campus path down to that road, widens the meadow and the world's edge to hold it all, and
builds the Castle Grounds landmarks (tools/grounds.py) on the land between. build.POINTS are the points after the
move.

Points are Roblox studs: (x, z) across the ground, X east and Z south.
"""
import math

MOVES = {'Academy': (0, -300), 'Forest': (-300, 0)}   # (x, z) from where each was laid out; the village stays
AZ, FX = MOVES['Academy'][1], MOVES['Forest'][0]
MEADOW = (-330 + FX, 330, -650 + AZ, 285)             # x0, x1, z0, z1 of the ground
ACADEMY_TOPS = {'Ravenmoor Academy', 'Castle Grounds', 'Dueling Club', 'Mirror of Choosing', 'Mirrorlake'}
ACADEMY_MARKERS = {'Mirror', 'Library', 'Duelmaster', 'Training', 'Waystone_Castle'}   # and every Teacher_
FOREST_MARKERS = {'ForestGate', 'SpiderClearing', 'Moonwell', 'HowlerDen', 'Rotbark', 'Vexweave', 'Waystone_Whisperwood',
                  'Tobb'}
TOBB = 'Tobb Brambleworth'   # the groundskeeper, who sends players into Whisperwood, stands at its edge
GROUNDS = {   # landmark: (centre, where its gravel path leaves a road)
    'Flying pitch': ((215, -32), (96, -4)),                  # off the academy road's east side
    'Ruins of Old Ravenmoor': ((-20, -60), (-20, 10.5)),     # off the forest path's north side
    'Greenhouses': ((-130, 90), (-130, 25.5)),               # off the forest path's south side
    "Groundskeeper's hut": ((-290, 54), (-290, 25.5)),       # across the forest path from Tobb
}
GATE_Z, PATH_X = -47, -25   # where the academy road met the gate, and where the forest path's curbs ended, as laid out


def moved(point, area):
    """A point (x, z) or (x, y, z) laid out with `area` ('Academy', 'Forest' or 'City'), where it stands now."""
    dx, dz = MOVES.get(area, (0, 0))
    return (point[0] + dx, point[1] + dz) if len(point) == 2 else (point[0] + dx, point[1], point[2] + dz)


def marker_area(name):
    if name in ACADEMY_MARKERS or name.startswith('Teacher_'): return 'Academy'
    return 'Forest' if name in FOREST_MARKERS else 'City'


def moved_points(points): return {k: moved(v, marker_area(k)) for k, v in points.items()}


def area_of(path, name, x, z):
    """Which area a map part moves with: Academy, Forest or City. `path` is its model's names from the map's top."""
    top = path[0] if path else ''
    if top in ACADEMY_TOPS: return 'Academy'
    if top == 'Academy staff':   # teachers and the Duelmaster go north, Tobb west with his forest, and Oakhart stays
        return 'Forest' if path[1:2] == [TOBB] else 'Academy' if z < -40 else 'City'
    if top == 'Whisperwood': return 'Forest'
    if top.startswith('RuneChest'): return 'Forest' if x < -40 else 'City'
    if top == 'Lamps': return 'Academy' if z < -46 else 'City'           # the campus's own lamps; the road's stay
    if top == 'Land': return 'Forest' if name == 'Forest floor' else 'City'
    if top == 'Roads': return 'Forest' if name in ('Worn path', 'Cobble remnant') else 'City'
    return 'City'


class Slant:
    """A straight road at any angle from a to b, laid as build.road_trim lays the axis-aligned ones: a cobbled bed
    with slate curbs, dirt verges and paving bands. Its ends stop inside the roads it joins. Across the road, +s is
    the bed's +X side."""

    def __init__(self, a, b, width):
        self.a, self.b, self.width = a, b, width
        self.length = math.dist(a, b)
        self.d = ((b[0] - a[0]) / self.length, (b[1] - a[1]) / self.length)

    def at(self, t, s=0):
        """The point t studs along the road and s across it."""
        (x, z), (dx, dz) = self.a, self.d
        return x + dx * t + dz * s, z + dz * t - dx * s

    def meets(self, s, axis, value):
        """How far along the road its line s studs across reaches x (axis 0) or z (axis 1) = value."""
        across = (self.d[1], -self.d[0])[axis]
        return (value - self.a[axis] - across * s) / self.d[axis]

    def covers(self, x, z, margin=0):
        (ax, az), (dx, dz) = self.a, self.d
        t, s = (x - ax) * dx + (z - az) * dz, (x - ax) * dz - (z - az) * dx
        return -margin <= t <= self.length + margin and abs(s) <= self.width / 2 + margin

    def lay(self, parent, name, top, trims, gaps=((), ())):
        """The bed from the ground up to `top`. trims gives the stretch (from, to), in studs along the road, that
        the curb and verge run on each side (-s, then +s); gaps the openings in each curb, also in studs along."""
        import build
        yaw, w = math.atan2(*self.d), self.width

        def strip(label, t0, t1, s, y, size, colour, material, **kw):
            x, z = self.at((t0 + t1) / 2, s)
            build.part(parent, label, (x, y, z), (size[0], size[1], t1 - t0), colour, material, yaw=yaw, **kw)

        strip(name, 0, self.length, 0, top / 2, (w, top), build.ROAD, 'Cobblestone')
        for side, (t0, t1), side_gaps in zip((-1, 1), trims, gaps):
            cur = t0
            for g0, g1 in sorted(side_gaps) + [(t1, t1)]:
                if g0 > cur: strip('Curb', cur, g0, side * (w / 2 - 0.4), top + 0.15, (0.8, 0.3), build.CURB, 'Slate', query=False)
                cur = max(cur, g1)
            strip('Verge', t0, t1, side * (w / 2 + 0.6), 0.03, (1.2, 0.06), build.VERGE, 'Sand', **build.TRIM)
        for t in build.frange(max(t for t, _ in trims) + 4, min(t for _, t in trims) - 2, 8):
            strip('Paving band', t - 0.35, t + 0.35, 0, top + 0.01, (w - 1.6, 0.02), build.ROAD_BAND, 'Cobblestone', **build.TRIM)


# The forest road leaves the academy road just south of the gate and joins the forest path 25 studs east of Tobb
# (laid out at x -5), so the Castle Waystone, the yard and the west wing reach Whisperwood without the square.
FOREST_ROAD = Slant((85, GATE_Z + AZ + 23.5), (-5 + FX + 25, 18), 15)
CAMPUS_END = FOREST_ROAD.at(FOREST_ROAD.meets(0, 0, 10))[1]   # where the west wing's campus path meets it (z)
# The roads players walk, as ((a, b) centreline, width): the walking times follow them and the mountains keep off them.
ROADS = [(((85, 114), (85, GATE_Z - 6 + AZ)), 22), (((85, 18), (-38 + FX, 18)), 15),
         (((10, -20 + AZ), (10, CAMPUS_END)), 16), ((FOREST_ROAD.a, FOREST_ROAD.b), FOREST_ROAD.width)]


def name_of(node): return node.findtext("Properties/string[@name='Name']")


def walk(node, path):
    for child in node.findall('Item'):
        yield path, child
        yield from walk(child, path + [name_of(child)])


def lay(world):
    """Move the map's academy and forest parts (laid out by build.make_world), then lay the new ground, roads and
    Castle Grounds into the map's Land, Roads and Lamps groups and beside them."""
    import build
    import grounds
    groups = {name_of(top): top for top in world.findall('Item')}
    for top in world.findall('Item'):
        for path, node in [([], top)] + list(walk(top, [name_of(top)])):
            cf = node.find("Properties/CoordinateFrame[@name='CFrame']")
            if node.get('class') not in ('Part', 'WedgePart') or cf is None: continue
            x, z = float(cf.findtext('X')), float(cf.findtext('Z'))
            dx, dz = MOVES.get(area_of(path or [name_of(top)], name_of(node), x, z), (0, 0))
            if dx: cf.find('X').text = str(x + dx)
            if dz: cf.find('Z').text = str(z + dz)
    land, roads, lamps = groups['Land'], groups['Roads'], groups['Lamps']
    # The meadow and the invisible world edge round it.
    x0, x1, z0, z1 = MEADOW
    for node in land.findall('Item'):
        size, cf = node.find("Properties/Vector3[@name='size']"), node.find("Properties/CoordinateFrame[@name='CFrame']")
        if name_of(node) == 'Meadow':
            cf.find('X').text, cf.find('Z').text = str((x0 + x1) / 2), str((z0 + z1) / 2)
            size.find('X').text, size.find('Z').text = str(x1 - x0), str(z1 - z0)
        elif name_of(node) == 'World boundary':
            if float(size.findtext('X')) < 10:   # a wall along z, west or east
                cf.find('X').text = str(x0 - 1 if float(cf.findtext('X')) < 0 else x1 + 1)
                cf.find('Z').text, size.find('Z').text = str((z0 + z1) / 2), str(z1 - z0)
            else:
                cf.find('Z').text = str(z0 - 1 if float(cf.findtext('Z')) < 0 else z1 + 1)
                cf.find('X').text, size.find('X').text = str((x0 + x1) / 2), str(x1 - x0)
    # The forest road, with openings in the academy road's west curb and the forest path's north curb where it joins
    # them, curbs and verges from the one's edge to the other's, and an opening for the campus path on its north-west.
    road = FOREST_ROAD
    edges = [road.at(road.meets(s, 0, 74.4), s) for s in (-7.5, 7.5)]
    road_gap = ((min(z for _, z in edges) - 1, max(z for _, z in edges) + 1),)
    edges = [road.at(road.meets(s, 1, 10.9), s) for s in (-7.5, 7.5)]
    path_gap = ((min(x for x, _ in edges) - 1, max(x for x, _ in edges) + 1),)
    trims = [(road.meets(s, 0, 74), road.meets(s, 1, 10.5)) for s in (-7.5, 7.5)]
    campus = sorted(road.meets(-7.5, 0, x) for x in (18, 2))
    road.lay(roads, 'Forest road', 0.33, trims, (((campus[0] - 1, campus[1] + 1),), ()))
    # The academy road carried north to the gate, with its lamps (none in the forest road's mouth), and the campus
    # path down from the west wing stair to the forest road, a little lower than both so the road covers its end.
    build.part(land, 'Academy approach', (85, 0.2, GATE_Z - 3 + AZ / 2), (22, 0.35, -AZ), build.ROAD, 'Cobblestone')
    build.road_trim(roads, 'z', 85, 22, GATE_Z + AZ, GATE_Z, 0.375, gaps=(road_gap, ()))
    for z in range(GATE_Z - 22, GATE_Z + AZ, -24):
        for x, side in ((70, 1), (100, -1)):
            if not road.covers(x, z, 2.5): build.lamp(lamps, x, z, side)
    south = 10.5 + AZ
    build.part(roads, 'Campus path', (10, 0.16, (south + CAMPUS_END) / 2), (16, 0.32, CAMPUS_END - south), build.ROAD, 'Cobblestone')
    # The forest path carried west to the forest.
    build.part(land, 'Forest path', (-130 + FX / 2, 0.23, 18), (-FX, 0.4, 15), build.ROAD, 'Cobblestone')
    build.road_trim(roads, 'x', 18, 15, PATH_X + FX, PATH_X, 0.43, gaps=(path_gap, ()))
    for name, (centre, start) in GROUNDS.items(): grounds.build(world, name, centre, start)
