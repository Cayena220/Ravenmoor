"""Mountain ranges and woods for a layout plan (blender/world/world_plan.py), built in Blender only to show how the
land round Ravenmoor could rise and grow. The game has none of it yet: in Studio the ranges would be Terrain and the
trees MeshParts.

The ranges are one heightfield. Knife-edged ridges and needle spires climb out of the meadow wherever it is clear of
what players walk, and tower over it from beyond its edge. Each face takes its colour from its height and slope:
grass, then moor and heather, scree, crags in bands like strata, and snow on the highest peaks. Round-canopy trees
crowd the foot of the slopes and stand in woods across the open meadow, never on a road. mist() lays a ground mist
that pools in the low land, and a thin air that blues the far ranges, for the EEVEE pictures (rbx.beauty).

Points are in Roblox studs, (x, z) across the ground and y up, as the plan works; bl() turns one into Blender's axes.
"""
import math
import random
import bmesh
import bpy
from mathutils import Matrix, Vector, noise
import rbx
from palette import CRAG, FOLIAGE, HEATHER, HILLSIDE, MEADOW, MOOR, SCREE, SNOW, TRUNK

SEED = 5207
STEP = 6               # studs between the heightfield's points
CLEAR, RISE = 18, 140  # the flat ground kept beside everything players walk, then how far the land takes to rise
BEYOND = 480           # how far the ranges run on past the meadow's edge, enough to close every view
SINK = 0.6             # the heightfield lies this far below the meadow, so the flat land is the meadow's own


def bl(x, y, z): return Vector((-x, z, y))


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def ridged(x, z, scale, octaves):
    """Ridged fractal noise, 0 to about 1: sharp crests along the lines where the noise crosses zero."""
    total, amp, weight, norm = 0.0, 1.0, 1.0, 0.0
    for octave in range(octaves):
        f = 2.07 ** octave / scale
        n = 1 - abs(noise.noise(Vector((x * f, z * f, octave * 3.7))))
        n *= n * weight
        weight = min(1.0, n * 1.8)
        total += n * amp; norm += amp; amp *= 0.5
    return total / norm


def spires(x, z):
    """Needle pinnacles in about half the cells of a jittered grid 150 studs across, each its own height: 0 to 1."""
    distances, points = noise.voronoi(Vector((x / 150, z / 150, 0.5)))
    tall = max(-1.0, min(1.0, noise.cell(points[0])))   # below 0, the cell has no spire
    return max(0.0, 1 - distances[0] / 0.5) ** 2.2 * tall if tall > 0 else 0.0


class Land:
    """The plan's land: flat by `roads` ((a, b) centrelines with their widths) and `areas` (x0, x1, z0, z1 boxes),
    rising from CLEAR studs off them into ranges that stand tallest beyond `meadow`, the meadow's box."""

    def __init__(self, roads, areas, meadow):
        self.roads, self.areas, self.meadow = roads, areas, meadow
        noise.seed_set(SEED)

    def clearance(self, x, z):
        """How far (x, z) is from the nearest road's edge or area."""
        best = math.inf
        for ((ax, az), (bx, bz)), width in self.roads:
            dx, dz = bx - ax, bz - az
            t = max(0.0, min(1.0, ((x - ax) * dx + (z - az) * dz) / (dx * dx + dz * dz)))
            best = min(best, math.hypot(x - ax - t * dx, z - az - t * dz) - width / 2)
        for x0, x1, z0, z1 in self.areas:
            best = min(best, math.hypot(max(x0 - x, 0, x - x1), max(z0 - z, 0, z - z1)))
        return best

    def outside(self, x, z):
        """How far (x, z) lies outside the meadow."""
        x0, x1, z0, z1 = self.meadow
        return math.hypot(max(x0 - x, 0, x - x1), max(z0 - z, 0, z - z1))

    def height(self, x, z):
        lift = smooth((self.clearance(x, z) - CLEAR) / RISE)
        if lift <= 0: return 0.0
        stand = 0.55 + 0.45 * (1 + noise.noise(Vector((x / 900, z / 900, 9.1))))   # some ranges stand taller
        reach = (95 + 300 * smooth(self.outside(x, z) / 280)) * stand
        r = ridged(x, z, 260, 4)
        return lift * reach * (0.7 * r ** 1.7 + 0.8 * spires(x, z) * (0.3 + r))


class Heights:
    """The land's height on a grid STEP studs apart, read anywhere between the points."""

    def __init__(self, land):
        x0, x1, z0, z1 = land.meadow
        self.x0, self.z0 = x0 - BEYOND, z0 - BEYOND
        self.nx, self.nz = int((x1 - x0 + 2 * BEYOND) / STEP) + 1, int((z1 - z0 + 2 * BEYOND) / STEP) + 1
        self.grid = [[land.height(self.x0 + STEP * i, self.z0 + STEP * j) for j in range(self.nz)] for i in range(self.nx)]

    def point(self, i, j): return self.x0 + STEP * i, self.grid[i][j], self.z0 + STEP * j

    def at(self, x, z):
        """The height at (x, z), and the slope there as rise over run."""
        u, v = (x - self.x0) / STEP, (z - self.z0) / STEP
        i, j = max(0, min(self.nx - 2, int(u))), max(0, min(self.nz - 2, int(v)))
        fu, fv = u - i, v - j
        g = self.grid
        h00, h10, h01, h11 = g[i][j], g[i + 1][j], g[i][j + 1], g[i + 1][j + 1]
        h = h00 * (1 - fu) * (1 - fv) + h10 * fu * (1 - fv) + h01 * (1 - fu) * fv + h11 * fu * fv
        sx, sz = ((h10 - h00) * (1 - fv) + (h11 - h01) * fv) / STEP, ((h01 - h00) * (1 - fu) + (h11 - h10) * fu) / STEP
        return h, math.hypot(sx, sz)


def paint(h, up, x, z):
    """A face's colour from its height `h` and how far it faces up, `up` (1 is level)."""
    if h < 3: return MEADOW
    if h > 235 + 40 * noise.noise(Vector((x / 120, z / 120, 2.2))) and up > 0.42: return SNOW
    if up < 0.62 or h > 160: return CRAG[int(h / 8 + 1.5 * noise.noise(Vector((x / 60, z / 60, 5.5)))) % 3]
    if up < 0.8: return SCREE
    if h > 60: return HEATHER if noise.noise(Vector((x / 50, z / 50, 7.7))) > 0.35 else MOOR
    return HILLSIDE


def ranges(collection, land):
    """The ranges as one mesh, Mountains, in `collection`. The meadow's flat land is left to the meadow, so only
    faces that rise above it are made there. Returns the Heights, for woods()."""
    heights = Heights(land)
    mesh = rbx.Mesh('Mountains'); made = {}

    def vert(i, j):
        if (i, j) not in made:
            x, h, z = heights.point(i, j)
            made[i, j] = mesh.bm.verts.new(bl(x, h - SINK, z))
        return made[i, j]

    for i in range(heights.nx - 1):
        for j in range(heights.nz - 1):
            # Two triangles a quad, wound to face up in Blender's mirrored axes, split on alternate diagonals so the
            # facets don't line up into stripes.
            a, d, b, c = (i, j), (i, j + 1), (i + 1, j), (i + 1, j + 1)
            for tri in ((a, d, c), (a, c, b)) if (i + j) % 2 else ((a, d, b), (d, c, b)):
                (ax, ah, az), (bx, bh, bz), (cx, ch, cz) = (heights.point(*k) for k in tri)
                mx, mz = (ax + bx + cx) / 3, (az + bz + cz) / 3
                if max(ah, bh, ch) < 0.05 and land.outside(mx, mz) == 0: continue
                n = Vector((bx - ax, bh - ah, bz - az)).cross(Vector((cx - ax, ch - ah, cz - az)))
                rgba = (*(c / 255 for c in paint((ah + bh + ch) / 3, abs(n.y) / n.length, mx, mz)), 1.0)
                face = mesh.bm.faces.new([vert(*k) for k in tri])
                for loop in face.loops: loop[mesh.colour] = rgba
    obj = mesh.finish(sharp=0)   # every edge hard: flat facets
    for c in list(obj.users_collection): c.objects.unlink(obj)
    collection.objects.link(obj)
    return heights


def tree(mesh, x, y, z, rng):
    """A round-canopy tree standing on (x, y, z): a tapered trunk and two lumpy crowns in the FOLIAGE tones."""
    s = rng.uniform(0.7, 1.35); trunk = 7 * s
    mesh.cylinder(0.8 * s, trunk + 1, bl(x, y + trunk / 2, z), TRUNK, top=0.55 * s, segments=5)
    r = rng.uniform(4.5, 6.5) * s
    mesh.sphere(r, bl(x, y + trunk + r * 0.55, z), rng.choice(FOLIAGE), segments=8, scale=(1, 1, 0.8))
    r2 = r * rng.uniform(0.55, 0.75)
    ox, oz = rng.uniform(-0.5, 0.5) * r, rng.uniform(-0.5, 0.5) * r
    mesh.sphere(r2, bl(x + ox, y + trunk + r * 0.95 + r2 * 0.3, z + oz), rng.choice(FOLIAGE), segments=8, scale=(1, 1, 0.85))


def shapes(count=10):
    """`count` trees made once at the origin, each as (vertex positions, [(vertex indices, colour)] per face), to
    copy: bmesh's shape operators walk the whole mesh, so thousands of trees made one by one would crawl."""
    rng, made = random.Random(SEED + 1), []
    for _ in range(count):
        mesh = rbx.Mesh('_Tree'); tree(mesh, 0, 0, 0, rng)
        index = {v: i for i, v in enumerate(mesh.bm.verts)}
        made.append(([v.co.copy() for v in mesh.bm.verts],
                     [([index[v] for v in f.verts], tuple(f.loops[0][mesh.colour])) for f in mesh.bm.faces]))
        mesh.bm.free()
    return made


def woods(collection, land, heights, spacing=10):
    """Trees as one mesh, Woods, in `collection`: thick round the foot of the slopes and in woods across the
    meadow, thinning higher up, and none near a road or an area, on crags or above the tree line. Each is one of
    shapes(), turned and sized at random. Returns how many."""
    rng, kinds = random.Random(SEED), shapes()
    mesh, count = rbx.Mesh('Woods'), 0
    x0, x1, z0, z1 = land.meadow
    for gx in range(int(x0) - 150, int(x1) + 150, spacing):
        for gz in range(int(z0) - 150, int(z1) + 150, spacing):
            x, z = gx + rng.uniform(-4, 4), gz + rng.uniform(-4, 4)
            if land.clearance(x, z) < 8: continue
            h, slope = heights.at(x, z)
            if h > 150 or slope > 0.85: continue
            wood = 0.5 + 0.5 * noise.noise(Vector((x / 170, z / 170, 4.2)))   # where the woods stand
            foot = smooth(h / 10) * (1 - smooth((h - 80) / 60))                # the foot of the slopes
            if rng.random() > 0.03 + 0.8 * wood ** 3 + 0.55 * foot: continue
            points, faces = rng.choice(kinds)
            spin, size, at = Matrix.Rotation(rng.uniform(0, math.tau), 3, 'Z'), rng.uniform(0.85, 1.15), bl(x, h - SINK - 0.4, z)
            verts = [mesh.bm.verts.new(at + spin @ (p * size)) for p in points]
            for corners, rgba in faces:
                for loop in mesh.bm.faces.new([verts[k] for k in corners]).loops: loop[mesh.colour] = rgba
            count += 1
    obj = mesh.finish(sharp=40)
    if obj:
        for c in list(obj.users_collection): c.objects.unlink(obj)
        collection.objects.link(obj)
    return count


def mist(collection, meadow):
    """Two volumes over all the land, which only EEVEE and Cycles draw, so keep `collection` out of Workbench
    renders. A ground mist, thickest on the ground and gone 28 studs up, lies over the low land and pools between
    the slopes. A thin air up to 700 studs blues the far ranges: finite, unlike a world volume, so the sun still
    shines through it."""
    return (volume(collection, 'Mist', meadow, 28, (0.92, 0.94, 0.97), 0.004, 2.5),
            volume(collection, 'Air', meadow, 700, (0.70, 0.80, 1.0), 0.00007, 0.6))


def volume(collection, name, meadow, top, colour, density, falloff):
    """A box of scattering volume over the meadow and the ranges past it, from just under the ground to `top`.
    Its density is `density` on the ground and falls to nothing at the top, as (1 - height) ** `falloff`."""
    x0, x1, z0, z1 = meadow
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:   # corners set in Blender's axes, where x is mirrored, so the box stays outside out
        v.co = Vector((-(x1 + BEYOND) if v.co.x < 0 else -(x0 - BEYOND), z0 - BEYOND if v.co.y < 0 else z1 + BEYOND,
                       -2 if v.co.z < 0 else top))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    obj = bpy.data.objects.new(name, me); collection.objects.link(obj)
    mat = bpy.data.materials.new(name)
    if not mat.node_tree: mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    out, scatter = nodes.new('ShaderNodeOutputMaterial'), nodes.new('ShaderNodeVolumePrincipled')
    scatter.inputs['Color'].default_value = (*colour, 1); scatter.inputs['Anisotropy'].default_value = 0.3
    # The fall along the box's own height, Generated Z, from 0 at the bottom to 1 at the top.
    coords, split = nodes.new('ShaderNodeTexCoord'), nodes.new('ShaderNodeSeparateXYZ')
    fall, curve, scale = (nodes.new('ShaderNodeMath') for _ in range(3))
    fall.operation, curve.operation, scale.operation = 'SUBTRACT', 'POWER', 'MULTIPLY'
    fall.inputs[0].default_value, curve.inputs[1].default_value, scale.inputs[1].default_value = 1.0, falloff, density
    links.new(coords.outputs['Generated'], split.inputs['Vector'])
    links.new(split.outputs['Z'], fall.inputs[1]); links.new(fall.outputs['Value'], curve.inputs[0])
    links.new(curve.outputs['Value'], scale.inputs[0]); links.new(scale.outputs['Value'], scatter.inputs['Density'])
    links.new(scatter.outputs['Volume'], out.inputs['Volume'])
    me.materials.append(mat)
    return obj
