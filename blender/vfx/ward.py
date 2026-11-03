"""Ward VFX: the glass ward a student raises with R (Aegara, Ward Shield), and the glass it breaks into.

WardVFX.fbx holds one Model, WardVFX, with near-white meshes. The game colours them, sets their materials and moves
them in code (EffectsController), so nothing here is animated:
    Shell    the ward: a geodesic bubble of 162 flat glass panes, hexagons and twelve pentagons, with hairline gaps.
    Frame    the gold leading between the panes: a thin bar along every edge where two panes meet.
    Circle   the rune circle on the ground under the ward as it rises: two rings, twelve diamond runes and three arcs.
    Crack    a spider-web crack where a hit lands: jagged lines running out from the impact over the shell, with
             broken rings between them. The game turns a copy to face each hit.
    Shard1-6 six broken panes: thin, sharp-cornered glass of different shapes and sizes. When the ward gives out,
             the game throws copies of them off the shell.
    Ring     a thin ring with a fainter ripple inside: the shock where a hit lands and as the ward bursts.
    Glint    a flat eight-pointed star: the flash at a hit.

The ward is a sphere RADIUS studs across from its middle, which the game sets 0.5 studs above the HumanoidRootPart, so
it rests on the floor and clears a raised wand. The Shell, Frame and Crack share that middle: the Crack is a patch of
the same sphere around the front (-Y), so a copy turned to face a hit lies on the glass there. Every other mesh is
centred on its own origin, and the flat ones (Circle, Ring, Glint, the shards) stand across Y.
"""
import math
import random
import bmesh
from mathutils import Matrix, Vector
import rbx

MIST = (240, 232, 214)   # near white: the part's Color sets the hue in game
WHITE = (255, 255, 255)
RADIUS = 3.5
PANE = 0.07              # how thick a pane of glass is
GAP = 0.93               # each pane is this much of its cell, which leaves the hairline the Frame covers
CENTRE = 0.5             # the ward's middle above the HumanoidRootPart (EffectsController's WARD_LIFT)
FLOOR = -2.971           # the floor under a standing avatar's HumanoidRootPart

rbx.scene('WardVFX')


def geodesic(radius, subdivisions=3):
    """The cells of a geodesic sphere: each vertex of an icosphere becomes the cell made of the middles of the faces
    round it. Returns each cell as (outward normal, corners in order round it), and every edge between two cells."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, radius=1.0)
    middle = {f.index: f.calc_center_median().normalized() * radius for f in bm.faces}
    cells = []
    for v in bm.verts:
        n = v.co.normalized(); across = n.orthogonal().normalized(); up = n.cross(across)
        corners = sorted((middle[f.index] for f in v.link_faces),
                         key=lambda c: math.atan2((c - n * radius).dot(up), (c - n * radius).dot(across)))
        cells.append((n, corners))
    edges = [(middle[e.link_faces[0].index], middle[e.link_faces[1].index]) for e in bm.edges]
    bm.free()
    return cells, edges


def plate(mesh, normal, corners, depth, colour):
    """A flat pane over `corners`, shrunk to GAP of its cell and `depth` thick, its outer face on the sphere."""
    across = normal.orthogonal().normalized(); up = across.cross(normal)
    surface = normal * max(c.dot(normal) for c in corners)   # the plane through the cell's outermost corner
    flat = [(c.dot(across), c.dot(up)) for c in corners]
    mx, my = sum(x for x, _ in flat) / len(flat), sum(y for _, y in flat) / len(flat)
    outline = [(mx + (x - mx) * GAP, my + (y - my) * GAP) for x, y in flat]
    frame = Matrix.Identity(4)
    for row in range(3): frame[row][0], frame[row][1], frame[row][2], frame[row][3] = across[row], normal[row], up[row], surface[row]
    mesh.frame = frame
    mesh.prism(outline, depth, (0, -depth / 2, 0), colour)
    mesh.frame = Matrix.Identity(4)


cells, edges = geodesic(RADIUS)
shell = rbx.Mesh('Shell')
for normal, corners in cells: plate(shell, normal, corners, PANE, MIST)

# The leading lies over the hairlines between the panes, a little proud of the glass.
frame = rbx.Mesh('Frame')
for a, b in edges:
    frame.tube([a * 1.004, b * 1.004], 0.03, MIST, sides=5)

# The rune circle: two rings, twelve diamond runes between them and three arcs outside, lying across Y.
circle = rbx.Mesh('Circle')
circle.torus(3.3, 0.05, (0, 0, 0), MIST, turn=(90, 0, 0), segments=64, sides=6)
circle.torus(2.75, 0.035, (0, 0, 0), MIST, turn=(90, 0, 0), segments=56, sides=5)
for k in range(12):
    a = math.radians(30 * k + 15); r = 3.02
    circle.prism([(0, 0.17), (0.07, 0), (0, -0.17), (-0.07, 0)], 0.04, (r * math.cos(a), 0, r * math.sin(a)), WHITE,
                 turn=(0, -math.degrees(a) + 90, 0))
for k in range(3):
    circle.torus(3.6, 0.03, (0, 0, 0), MIST, turn=(90, 120 * k, 0), segments=20, sides=5, arc=70)

# The crack: a patch of the sphere, just outside the glass, round the front (-Y). Eight jagged lines run out from
# the impact, a few of them forking, with two broken rings of crazing between them.
CRACK = RADIUS + 0.02
rand = random.Random(7)


def on_sphere(theta, phi):
    """The point `theta` radians off the front and `phi` round it."""
    return (CRACK * math.sin(theta) * math.cos(phi), -CRACK * math.cos(theta), CRACK * math.sin(theta) * math.sin(phi))


crack = rbx.Mesh('Crack')
rays = []
for k in range(8):
    phi, reach, line = 2 * math.pi * k / 8 + rand.uniform(-0.2, 0.2), rand.uniform(0.5, 0.78), []
    for step in range(8):
        theta = 0.01 + reach * step / 7
        phi += rand.uniform(-0.12, 0.12)
        line.append((theta, phi))
    rays.append(line)
    crack.tube([on_sphere(*p) for p in line], [0.035 * (1 - s / 9) + 0.008 for s in range(8)], WHITE, sides=4)
    if k % 2 == 0:   # a fork from partway out
        theta, phi = line[3]; side = rand.choice((-1, 1)); fork = [(theta, phi)]
        for _ in range(3):
            theta += 0.07; phi += side * rand.uniform(0.1, 0.18); fork.append((theta, phi))
        crack.tube([on_sphere(*p) for p in fork], [0.02, 0.016, 0.012, 0.008], WHITE, sides=4)
for ring in (2, 4):   # crazing: the rings break where a ray is skipped
    for k in range(8):
        if rand.random() < 0.3: continue
        (t1, p1), (t2, p2) = rays[k][ring], rays[(k + 1) % 8][ring]
        if p2 < p1: p2 += 2 * math.pi
        mid = ((t1 + t2) / 2 + rand.uniform(-0.04, 0.04), (p1 + p2) / 2)
        crack.tube([on_sphere(t1, p1), on_sphere(*mid), on_sphere(t2, p2)], 0.012, MIST, sides=4)
crack.sphere(0.07, on_sphere(0, 0), WHITE, segments=8)

# Six broken panes: sharp, irregular and thin, from a sliver to a big wedge.
shards = []
for k, (corners, size) in enumerate(((3, 0.55), (4, 0.7), (3, 0.9), (5, 0.6), (4, 1.05), (3, 0.42))):
    # Corners spread round the middle, so no shard is a needle with a stub.
    angles = [2 * math.pi * i / corners + rand.uniform(-0.5, 0.5) * math.pi / corners for i in range(corners)]
    outline = [(size * rand.uniform(0.55, 1.0) * math.cos(a), size * rand.uniform(0.55, 1.0) * math.sin(a)) for a in angles]
    shard = rbx.Mesh(f'Shard{k + 1}')
    shard.prism(outline, PANE, (0, 0, 0), MIST)
    shards.append(shard)

ring = rbx.Mesh('Ring')
ring.torus(1.0, 0.06, (0, 0, 0), WHITE, turn=(90, 0, 0), segments=40, sides=8)
ring.torus(0.7, 0.03, (0, 0, 0), MIST, turn=(90, 0, 0), segments=32, sides=6)

# The glint: four long points, four short ones between, and narrow waists.
glint = rbx.Mesh('Glint')
reach = [0.9 if i % 4 == 0 else 0.5 if i % 2 == 0 else 0.1 for i in range(16)]
glint.prism([(r * math.cos(math.radians(22.5 * i)), r * math.sin(math.radians(22.5 * i))) for i, r in enumerate(reach)],
            0.03, (0, 0, 0), WHITE)

meshes = [shell, frame, circle, crack, *shards, ring, glint]
pieces = [m.finish(sharp=25 if m is shell or m.name.startswith('Shard') else 70) for m in meshes]
ward = rbx.group('WardVFX', pieces)
rbx.viewport((0, 0, 0), 14, turn=(70, 0, 50))
rbx.export('WardVFX', [ward, *ward.children_recursive], auto_preview=False)


# ---------------------------------------------------------------------------------------------------------------
# Previews. The pieces in a row, then three EEVEE pictures of the ward round a student casting it (the CastWard
# gesture from exports/Casting.blend): raised, cracked by three hits, and bursting. The glass, glow and ground are
# preview materials only; the export above keeps every piece plain and centred.
if rbx.PREVIEW:
    import bpy
    sc = bpy.context.scene
    parts = {o.name: o for o in ward.children_recursive}
    # The big pieces along the top, the small ones and the shards below.
    for name, x in (('Shell', -8.5), ('Frame', 0), ('Circle', 8.5)): parts[name].location = (x, 0, 1.5)
    for name, x in (('Crack', -6), ('Ring', -1.5), ('Glint', 1.5)): parts[name].location = (x, 0, -4.5)
    for k in range(6): parts[f'Shard{k + 1}'].location = (4.5 + 1.8 * (k % 3), 0, -3.8 - 1.6 * (k // 3))
    rbx.shot('WardVFX', (0, -24, 4), (0, 0, -1.5), lens=30, resolution=(1600, 900))
    for o in parts.values(): o.hide_render = True

    def material(name, colour, alpha=1.0, glow=0.0, rough=0.4, metal=0.0):
        mat = bpy.data.materials.new(name); mat.use_nodes = True
        bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        rgba = (*(c / 255 for c in colour), 1)
        bsdf.inputs['Base Color'].default_value = rgba
        bsdf.inputs['Roughness'].default_value = rough
        bsdf.inputs['Metallic'].default_value = metal
        bsdf.inputs['Alpha'].default_value = alpha
        if glow:
            bsdf.inputs['Emission Color'].default_value = rgba
            bsdf.inputs['Emission Strength'].default_value = glow
        if alpha < 1:
            for attr, value in (('surface_render_method', 'BLENDED'), ('blend_method', 'BLEND')):
                if hasattr(mat, attr):
                    try: setattr(mat, attr, value)
                    except TypeError: pass
        return mat

    # The colours EffectsController gives them: gold leading and runes, pale gold glass, white-hot cracks.
    GOLD, PALE, HOT = (246, 186, 84), (255, 236, 190), (255, 244, 214)
    looks = {'Shell': material('_Glass', PALE, alpha=0.2, rough=0.04, glow=0.1),
             'Frame': material('_Leading', GOLD, glow=1.2, metal=0.5, rough=0.25),
             'Circle': material('_Runes', GOLD, glow=2.5),
             'Crack': material('_Crack', HOT, glow=3.5),
             'Ring': material('_Shock', PALE, glow=1.5, alpha=0.45),
             'Glint': material('_Glint', HOT, glow=6.0),
             'Shard': material('_ShardGlass', PALE, alpha=0.5, rough=0.04, glow=0.25),
             'Lit': material('_ShardLit', GOLD, glow=2.5)}
    copies = []

    def place(name, at, turn=Matrix.Identity(3), scale=1.0, look=None):
        o = parts[name].copy(); sc.collection.objects.link(o); o.parent = None; o.hide_render = False
        o.matrix_world = Matrix.Translation(at) @ turn.to_4x4() @ Matrix.Diagonal((scale, scale, scale, 1))
        o.data = o.data.copy(); o.data.materials.clear(); o.data.materials.append(looks[look or name])
        copies.append(o)
        return o

    def facing(direction):
        """The turn that points a piece's front (-Y) along `direction`."""
        return Vector(direction).normalized().to_track_quat('-Y', 'Z').to_matrix()

    def clear():
        for o in copies: bpy.data.objects.remove(o)
        copies.clear()

    # The student, mid-cast, and the ground.
    path = rbx.EXPORTS / 'Casting.blend'
    student = []
    if path.exists():
        with bpy.data.libraries.load(str(path)) as (source, target):
            target.objects = [n for n in source.objects if n in ('CharacterRig', 'Mannequin', 'Arms', '_Wand')]
            target.actions = [n for n in source.actions if n == 'CastWard']
        for o in target.objects:
            if o and o.type in ('ARMATURE', 'MESH'): sc.collection.objects.link(o); student.append(o)
        rig = next((o for o in student if o.type == 'ARMATURE'), None)
        if rig and target.actions:
            rig.animation_data_create(); rig.animation_data.action = target.actions[0]
            if getattr(target.actions[0], 'slots', None): rig.animation_data.action_slot = target.actions[0].slots[0]
            sc.frame_set(8)   # the wand stands before the face
    else:
        rbx.say('Student skipped from the pictures: build blender/animations/casting.py first')
    ground = bpy.data.meshes.new('_Ground'); ground.from_pydata([(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)], [], [(0, 1, 2, 3)])
    floor = bpy.data.objects.new('_Ground', ground); sc.collection.objects.link(floor); floor.location.z = FLOOR
    ground.materials.append(material('_Flagstone', (92, 88, 82), rough=0.85))

    middle = Vector((0, 0, CENTRE))
    EYE, AIM = (7.5, -10.5, 2.4), (0, 0, 0.1)

    def raised():
        place('Shell', middle); place('Frame', middle)
        circle = place('Circle', (0, 0, FLOOR + 0.03), turn=Matrix.Rotation(math.radians(90), 3, 'X'))
        return circle

    raised()
    rbx.beauty('WardVFX_raised', EYE, AIM, lens=35, resolution=(1600, 1000), sun=(9, 215))

    # Three hits from the front and front right: a crack round each, a ripple and a glint where it landed.
    for direction in ((-0.3, -1, 0.35), (0.55, -0.8, -0.1), (0.15, -0.6, 0.8)):
        d = Vector(direction).normalized()
        place('Crack', middle, turn=facing(d), scale=1.0)
        hit = middle + d * (RADIUS + 0.05)
        place('Ring', hit, turn=facing(d), scale=0.55)
        place('Glint', hit + d * 0.05, turn=facing(d), scale=0.7)
    rbx.beauty('WardVFX_cracked', EYE, AIM, lens=35, resolution=(1600, 1000), sun=(9, 215))
    clear()

    # The burst, 0.12 s after the last hit from the front: the shards thrown off the shell as EffectsController
    # throws them (WardBreak), the shock ring opening round the middle and a flash where the hit landed.
    hit = Vector((0.1, -1, 0.2)).normalized(); shake = random.Random(3); t = 0.12
    count = 60
    for i in range(count):
        y = 1 - 2 * (i + 0.5) / count; r = math.sqrt(1 - y * y); a = i * math.pi * (3 - math.sqrt(5))
        n = Vector((r * math.cos(a), r * math.sin(a), y))
        start = middle + n * RADIUS
        speed = n * shake.uniform(7, 13) - hit * shake.uniform(3, 9) * max(0.2, -n.dot(hit) + 0.6) + Vector((0, 0, shake.uniform(2, 6)))
        at = start + speed * t + Vector((0, 0, -0.5 * 34 * t * t))
        spin = Matrix.Rotation(shake.uniform(2, 9) * t, 3, Vector((shake.uniform(-1, 1), shake.uniform(-1, 1), shake.uniform(-1, 1))).normalized())
        place(f'Shard{1 + i % 6}', at, turn=spin @ facing(n), scale=shake.uniform(0.85, 1.5), look='Lit' if i % 3 == 0 else 'Shard')
    place('Ring', middle, turn=Matrix.Rotation(math.radians(90), 3, 'X'), scale=RADIUS * 1.3)
    place('Glint', middle + hit * RADIUS, turn=facing(hit), scale=1.6)
    rbx.beauty('WardVFX_shatter', EYE, AIM, lens=35, resolution=(1600, 1000), sun=(9, 215))
