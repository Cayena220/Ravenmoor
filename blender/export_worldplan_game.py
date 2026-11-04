"""Export WorldPlan.blend to Roblox at a game budget: a few FBX files of merged meshes, for install_worldplan.lua.

    blender -b blender/exports/WorldPlan.blend --python blender/export_worldplan_game.py -- [--preview] [--only Garden,Stoneroot]
        [--patch WP_Nightfang_004,WP_Skyquill_005]

WorldPlan is built at film detail, 15 million triangles. Roblox streams a few million at most, so every object is cut
down by what it is (CUTS): carved ornament keeps 7% of its triangles, buildings 20%, ground 30%. Grass, ferns and other
planting made of many small tufts keep about one tuft in twelve, each grown to cover the gaps. The academy interior,
a scene of its own, stands 1,500 studs above the campus (INSIDE), where its portals lead.

--patch re-exports only the named meshes of the current manifest, by today's rules, as WP_Patch.fbx with new names
(WP_<Area>_P01 ...), and updates manifest.json to match; every other mesh keeps its name, so only the patch needs
importing. install_worldplan.lua's Patch stage swaps the meshes in the place.

Roblox gives each MeshPart one material. Meshes that come out as the same Roblox material (ROBLOX) are merged within a
cell of the map, with each Blender material's colour baked into the vertex colours, so a facade of five limestones is
one mesh. Collidable meshes use smaller cells, so their collision stays close to the shape.

Writes exports/RobloxWorld/WP_<Area>.fbx and manifest.json: every mesh's place, size, material and collision, the oak
templates and their 4,316 placements, the portals, the staff and props moved into the interior, and the lamps.
With --preview, renders exports/RobloxWorld/preview_<view>.png of the cut-down world beside the source.
Reads WorldPlan without saving it.
"""
import bpy, bmesh, hashlib, json, math, re, sys, time
import numpy as np
from collections import defaultdict
from pathlib import Path
from mathutils import Matrix, Vector

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PREVIEW = '--preview' in ARGS
ONLY = set(ARGS[ARGS.index('--only') + 1].split(',')) if '--only' in ARGS else None
OUT = Path(__file__).resolve().parent / 'exports' / 'RobloxWorld'
OUT.mkdir(parents=True, exist_ok=True)
PATCH, PATCH_SOURCES = None, set()
if '--patch' in ARGS:
    old_manifest = json.loads((OUT / 'manifest.json').read_text())
    PATCH = {r['name']: r for r in old_manifest['meshes'] if r['name'] in ARGS[ARGS.index('--patch') + 1].split(',')}
    ONLY = {r['group'] for r in PATCH.values()}
    PATCH_SOURCES = {s for r in PATCH.values() for s in r['sources']}
    PATCH_MATERIALS = {r['material'] for r in PATCH.values()}
SOURCE = Path(bpy.data.filepath)
assert SOURCE.name == 'WorldPlan.blend', 'Open blender/exports/WorldPlan.blend'
AX = Matrix(((-1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))   # Blender (x, y, z) is Roblox (-x, z, y)
INSIDE = Vector((85, 1500, -580))   # where the interior scene's origin stands in Roblox
LIMIT = 18000                       # triangles in one MeshPart; Roblox allows 20,000
PER_FILE = 120                      # meshes in one FBX, so each import stays a manageable upload

# What an object is, from its name: the share of triangles it keeps, whether players collide with it, and the cell
# (studs) its meshes merge within. The first match wins; FONT objects are lettering.
CUTS = [
    ('planting', ('grass blades', 'groundcover', 'ferns', 'fronds', 'low plants', 'reeds', 'ivy', 'planting', 'hedges',
                  'flowering beds', 'herbs'), .08, False, 192),
    ('lamp', ('lantern',), 1, False, 192),
    # Window glass is solid, so no one comes in through a window; doors (cloth) stay open to walk through.
    ('glass', ('window glass', 'glass panes', 'stained glass', 'display glass', 'lit window'), 1, True, 192),
    ('cloth', ('banner', 'textile', 'sail', 'door'), .3, False, 192),
    ('rail', ('balusters', 'handrails'), .15, True, 96),
    ('ornament', ('arches', 'quoins', 'cornices', 'tracery', 'mullions', 'finials', 'ironwork', 'coat of arms', 'crest',
                  'relief', 'medallion', 'wyvern', 'heraldry', 'sculptural', 'statuary', 'rose window', 'bear over',
                  'owl', 'firecat'), .07, False, 192),
    ('rock', ('mountains', 'outcrops', 'boulders', 'masonry', 'rubble'), .12, True, 256),
    ('ground', ('meadow', 'forest floor', 'village ground', 'roads', 'walks', 'paving', 'paths', 'lawn', 'shoreline',
                'pitch', 'kerbstones', 'lake', 'land', 'stair', 'terrace'), .3, True, 256),
    ('building', ('',), .2, True, 96),
]
LETTERING = ('lettering', (), .4, False, 192)
MIN_KEEP = 300   # small objects keep at least this many triangles

# Roblox material from words in the Blender material's name; the first match wins.
ROBLOX = [
    ('Glass', ('glass', 'glazing', 'window', 'lantern')), ('Water', ('water', 'lake')),
    ('Metal', ('iron', 'bronze', 'brass', 'gilt', 'gilded', 'gold', 'silver', 'copper', 'steel', 'pewter')),
    ('Marble', ('marble',)), ('Slate', ('slate',)), ('Granite', ('granite',)), ('Brick', ('brick', 'terracotta')),
    ('Cobblestone', ('cobble', 'sett')), ('Pebble', ('gravel', 'pebble', 'shingle')),
    ('Grass', ('grass', 'lawn', 'meadow', 'turf')),
    ('LeafyGrass', ('leaf', 'leaves', 'foliage', 'hedge', 'box', 'laurel', 'fern', 'moss', 'ivy', 'shoots', 'flower',
                    'herb', 'plant', 'reed')),
    ('WoodPlanks', ('boards', 'plank')), ('Wood', ('oak', 'walnut', 'wood', 'timber', 'joinery', 'bark', 'beam')),
    ('Fabric', ('velvet', 'cloth', 'fabric', 'carpet', 'textile', 'banner', 'linen', 'wool', 'silk', 'sail')),
    ('Rock', ('rock', 'mountain', 'scree', 'crag', 'stratified', 'boulder', 'fractured', 'rubble')),
    ('Sandstone', ('sandstone',)), ('Limestone', ('limestone', 'ashlar', 'stone', 'mortar', 'masonry')),
    ('Plaster', ('render', 'plaster', 'lime')),
]
NIGHT = ('Lit window', 'Lantern')   # WorldService.SetNightLights finds parts by these names
# Gameplay models, and models the place already has (Waystones, the duel arena, the road lamps that light at night).
EXCLUDED_COLLECTIONS = {'Showcase', 'Spawns', 'Academy staff', 'Rune chests', 'Academy | Relocated staff and teaching props',
                        'Waystones', 'Markers', 'Config zones', 'Mist', 'Dueling Club', 'Lamps', 'Whisperwood preview'}
EXCLUDED_NAMES = ('Training Dummy', 'Gloomspider', 'Lanternwisp', 'Moonhowler', 'Mother Vexweave', 'Rotbark',
                  'Thornimp', 'Subtle valley atmosphere')
HOUSES = [('EMBERCLAW HOUSE', 'EmberClaw'), ('STONEROOT HOUSE', 'Stoneroot'), ('SKYQUILL HOUSE', 'Skyquill'),
          ('NIGHTFANG HOUSE', 'Nightfang'), ('ACADEMY CAMPUS INTEGRATION', 'AcademyExterior'),
          ('FOUR HOUSES AND COMMON GARDEN', 'Garden')]


def log(s): print('[WORLDPLAN] ' + s, flush=True)


def visible(c, found):
    if c.hide_render or c.name in EXCLUDED_COLLECTIONS or c.name.startswith('90 |'): return
    for o in c.objects:
        if not o.hide_render: found.add(o)
    for child in c.children: visible(child, found)


def area(o, inside):
    if inside: return 'AcademyInterior'
    for name, group in HOUSES:
        c = bpy.data.collections.get(name)
        if c and o.name in c.all_objects: return group
    names = ' '.join(c.name for c in o.users_collection)
    if 'Hollowmere' in names or 'illage' in names: return 'Hollowmere'
    if any(s in names for s in ('Terrain', 'Mirrorlake', 'Land', 'Scenery', 'Whisperwood', 'Roads', 'woodland')): return 'Landscape'
    return 'Grounds'


def cut_of(o, label):
    # These tufts already use only two crossed quads. Keep their coverage and UVs.
    if o.get('wp_grass_cards') or o.get('wp_grass_card_prototype'):
        return ('cards', (), 1, False, 192)
    if o.type == 'FONT': return LETTERING
    low = label.lower()
    return next(c for c in CUTS if any(w in low for w in c[1]))


def feeders(socket, depth=5):
    """Every node feeding a shader socket, nearest first."""
    found, frontier = [], [l.from_node for l in socket.links]
    while frontier and depth:
        found += frontier; depth -= 1
        frontier = [l.from_node for n in frontier for i in n.inputs for l in i.links]
    return found


SHADES = {}
def shade(m):
    """What a Blender material becomes: Roblox material, linear colour, whether vertex colours carry the colour, the
    image maps (base colour, normal, roughness) it keeps, and a slope ramp if its colour follows the ground's slope
    (a ColorRamp on the normal's Z, as on the mountains), sampled at 65 steps of Z from 0 to 1."""
    key = m.name if m else ''
    if key in SHADES: return SHADES[key]
    low = key.lower(); colour = list(m.diffuse_color[:3]) if m else [.5, .5, .5]; images = {}; uses_vc = False
    slope = None
    principled = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if m and m.node_tree else None
    if principled:
        for socket in ('Base Color', 'Normal', 'Roughness'):
            image = next((n.image for n in feeders(principled.inputs[socket]) if n.type == 'TEX_IMAGE' and n.image), None)
            if image: images[socket] = image
        # SurfaceAppearance uses the ColorMap's alpha, so require the same RGBA
        # image in both sockets instead of silently exporting an opaque card.
        alpha_links = principled.inputs['Alpha'].links
        if alpha_links:
            link = alpha_links[0]
            if (link.from_node.type == 'TEX_IMAGE' and link.from_node.image and link.from_socket.name == 'Alpha'
                    and link.from_node.image == images.get('Base Color')):
                images['Alpha'] = link.from_node.image
            else:
                raise ValueError(f'{key}: bake opacity into the Base Color image alpha before Roblox export')
        base = feeders(principled.inputs['Base Color'])
        uses_vc = any(n.type in {'VERTEX_COLOR', 'ATTRIBUTE'} for n in base)
        ramp = next((n for n in base if n.type == 'VALTORGB' and any(f.type == 'NEW_GEOMETRY' for f in feeders(n.inputs[0]))), None)
        if ramp and 'Base Color' not in images:
            # The ramp is multiplied by half-strength noise in WorldPlan: three quarters of it on average.
            slope = np.array([ramp.color_ramp.evaluate(i / 64)[:3] for i in range(65)], np.float32) * .75
    roblox = next((r for r, words in ROBLOX if any(w in low for w in words)), 'SmoothPlastic')
    if principled and roblox not in ('Glass', 'Water'):
        if principled.inputs['Metallic'].default_value > .5: roblox = 'Metal'
        weight = principled.inputs.get('Transmission Weight')
        if weight and weight.default_value > .1: roblox = 'Glass'
    SHADES[key] = (roblox, colour, uses_vc, images, slope)
    return SHADES[key]


def islands(tris, count):
    """Island of every vertex: the lowest vertex index it is joined to through triangles."""
    label = np.arange(count)
    a, b, c = tris.T
    while True:
        low = np.minimum(np.minimum(label[a], label[b]), label[c])
        before = label.copy()
        for side in (a, b, c): np.minimum.at(label, side, low)
        label = label[label]
        if np.array_equal(label, before): return label


def thin(v, t, keep, grow, foot=True):
    """Keep about `keep` of the mesh's separate tufts, leaves or blades, each grown by `grow` about its foot (or its
    centre, for leaves)."""
    label = islands(t, len(v))
    roots = np.unique(label[t[:, 0]])
    chosen = roots[(roots.astype(np.int64) * 2654435761 % 4294967296) / 4294967296 < keep]
    if len(chosen) == 0: chosen = roots[:1]
    kept = np.isin(label[t[:, 0]], chosen)
    n = np.bincount(label, minlength=len(v)).astype(np.float64); n[n == 0] = 1
    pivot = np.stack([np.bincount(label, v[:, k], minlength=len(v)) for k in range(3)], 1) / n[:, None]
    if foot:
        lowest = np.full(len(v), np.inf); np.minimum.at(lowest, label, v[:, 2]); pivot[:, 2] = lowest
    v = (pivot[label] + (v - pivot[label]) * grow).astype(np.float32)
    return v, kept


class Bucket:
    """Triangles waiting to become meshes of one Roblox material, collision and cell size in one area."""
    def __init__(self): self.v, self.t, self.uv, self.col, self.sources, self.tris = [], [], [], [], defaultdict(int), 0

    def add(self, v, t, uv, col, source):
        offset = sum(len(x) for x in self.v)
        self.v.append(v); self.t.append(t + offset); self.uv.append(uv); self.col.append(col)
        self.sources[source] += len(t); self.tris += len(t)


buckets = defaultdict(Bucket)
manifest = {'source': str(SOURCE), 'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'axis': 'Roblox = (-Blender X, Blender Z, Blender Y)', 'interior_offset': list(INSIDE),
            'meshes': [], 'files': [], 'trees': [], 'templates': {}, 'markers': {}, 'props': {}, 'lights': [], 'excluded': []}
sources = [s for s in bpy.data.scenes]
export_scene = bpy.data.scenes.new('WorldPlan Roblox export')
export_scene.unit_settings.system = 'NONE'
cache, pending = {}, []
started = time.time(); source_tris = 0


def mesh_arrays(mesh):
    """Positions, triangles, per-corner UVs, colours (or None) and material slots of an evaluated mesh."""
    mesh.calc_loop_triangles()
    n, nt = len(mesh.vertices), len(mesh.loop_triangles)
    v = np.empty(n * 3, np.float32); mesh.vertices.foreach_get('co', v); v = v.reshape(-1, 3)
    t = np.empty(nt * 3, np.int32); mesh.loop_triangles.foreach_get('vertices', t); t = t.reshape(-1, 3)
    loops = np.empty(nt * 3, np.int32); mesh.loop_triangles.foreach_get('loops', loops); loops = loops.reshape(-1, 3)
    mids = np.empty(nt, np.int32); mesh.loop_triangles.foreach_get('material_index', mids)
    uv = np.zeros((nt, 3, 2), np.float32)
    if mesh.uv_layers.active:
        u = np.empty(len(mesh.loops) * 2, np.float32); mesh.uv_layers.active.data.foreach_get('uv', u)
        uv = u.reshape(-1, 2)[loops]
    col = None
    attr = mesh.color_attributes.active_color
    if attr:
        c = np.empty(len(attr.data) * 4, np.float32); attr.data.foreach_get('color', c); c = c.reshape(-1, 4)
        col = c[t] if attr.domain == 'POINT' else c[loops]
    return v, t, uv, col, mids, [mesh.materials[i] for i in range(len(mesh.materials))]


def place(shape, matrix, group, label, cut):
    """Put one cut-down shape into the buckets, moved by `matrix` (Blender world space)."""
    v, t, uv, col, mids, mats = shape
    a = np.array(matrix, np.float64)
    w = (v @ a[:3, :3].T + a[:3, 3]).astype(np.float32)
    tt, uu, cc = t, uv, col
    if np.linalg.det(a[:3, :3]) < 0: tt, uu = t[:, ::-1], uv[:, ::-1]; cc = None if col is None else col[:, ::-1]
    kind, _, _, collide, cell = cut
    night = next((n for n in NIGHT if label.split(' / ')[-1].startswith(n)), None)
    for mid in np.unique(mids):
        ids = np.flatnonzero(mids == mid)
        m = mats[mid] if mid < len(mats) else None
        roblox, colour, uses_vc, images, slope = shade(m)
        if PATCH and roblox not in PATCH_MATERIALS: continue   # a patch rebuilds only what the patched meshes held
        textured = 'Base Color' in images
        corner = np.ones((len(ids), 3, 4), np.float32)
        if textured: pass   # the image carries the colour
        elif slope is not None:
            p = w[tt[ids]]; n = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
            z = n[:, 2] / np.maximum(np.linalg.norm(n, axis=1), 1e-9)
            corner[:, :, :3] = slope[np.round(np.clip(z, 0, 1) * 64).astype(int)][:, None, :]
        elif uses_vc and cc is not None:
            corner = cc[ids].copy(); corner[:, :, 3] = 1
        else: corner[:, :, :3] = colour
        image_key = tuple(sorted((k, im.name) for k, im in images.items()))
        key = (group, roblox, collide, cell, image_key, label if night else '', kind in ('cards', 'planting', 'cloth', 'glass', 'lamp'))
        vert_ids, faces = np.unique(tt[ids].ravel(), return_inverse=True)
        buckets[key].add(w[vert_ids], faces.reshape(-1, 3).astype(np.int64), uu[ids], corner, label.split(' / ')[0])


def flush():
    """Evaluate every queued decimation at once, then place each result where its object (or instances) stand."""
    if not pending: return
    deps = bpy.context.evaluated_depsgraph_get()
    for tmp, name in pending:
        ev = tmp.evaluated_get(deps); mesh = ev.to_mesh()
        cache[name] = mesh_arrays(mesh); ev.to_mesh_clear()
    for tmp, name in pending:
        data = tmp.data; bpy.data.objects.remove(tmp); bpy.data.meshes.remove(data)
        for matrix, group, label, cut in uses.pop(name): place(cache[name], matrix, group, label, cut)
    pending.clear()


uses = defaultdict(list)
queued_tris = 0


def realized_instance_mesh(o, collection):
    """Realize Geometry Nodes on an export-only copy; leave the source instanced."""
    temp = o.copy()
    temp.name = 'export realized ' + o.name
    collection.objects.link(temp)
    group = bpy.data.node_groups.new('Export only - realize instances', 'GeometryNodeTree')
    try:
        group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
        group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
        source = group.nodes.new('NodeGroupInput')
        realize = group.nodes.new('GeometryNodeRealizeInstances')
        output = group.nodes.new('NodeGroupOutput')
        group.links.new(source.outputs['Geometry'], realize.inputs['Geometry'])
        group.links.new(realize.outputs['Geometry'], output.inputs['Geometry'])
        temp.modifiers.new('Export only - realize instances', 'NODES').node_group = group
        deps = bpy.context.evaluated_depsgraph_get()
        return bpy.data.meshes.new_from_object(temp.evaluated_get(deps), preserve_all_data_layers=True, depsgraph=deps)
    finally:
        bpy.data.objects.remove(temp, do_unlink=True)
        bpy.data.node_groups.remove(group)


def request(o, deps, matrix, group, label, collection):
    """Cut an object down once (instances reuse the result) and place it at `matrix`."""
    global queued_tris, source_tris
    cut = cut_of(o, label)
    name = o.name
    if name in cache: return place(cache[name], matrix, group, label, cut)
    uses[name].append((matrix, group, label, cut))
    if len(uses[name]) > 1: return
    ev = o.evaluated_get(deps)
    mesh = (realized_instance_mesh(o, collection) if o.get('wp_grass_cards') or o.get('wp_instance_geometry') else
            bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=deps))
    count = sum(max(0, len(p.vertices) - 2) for p in mesh.polygons)
    source_tris += count
    if count == 0:
        bpy.data.meshes.remove(mesh); uses.pop(name); return
    if cut[0] == 'cards':
        cache[name] = mesh_arrays(mesh)
        bpy.data.meshes.remove(mesh)
        for args in uses.pop(name): place(cache[name], *args)
        return
    keep = cut[2]
    if cut[0] == 'planting':
        v, t, uv, col, mids, mats = mesh_arrays(mesh)
        tufts = len(np.unique(islands(t, len(v))[t[:, 0]]))
        if tufts > 200 and len(t) / tufts < 200:
            bpy.data.meshes.remove(mesh)
            v, kept = thin(v, t, keep, 1.7)
            cache[name] = (v, t[kept], uv[kept], None if col is None else col[kept], mids[kept], mats)
            for args in uses.pop(name): place(cache[name], *args)
            return
    bm = bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=.0005); bm.to_mesh(mesh); bm.free()
    tmp = bpy.data.objects.new('cut ' + name, mesh); collection.objects.link(tmp)
    ratio = min(1, max(keep, MIN_KEEP / count))
    if ratio < 1:
        mod = tmp.modifiers.new('Cut', 'DECIMATE'); mod.decimate_type = 'COLLAPSE'; mod.ratio = ratio
        mod.use_collapse_triangulate = True
    pending.append((tmp, name)); queued_tris += count
    if queued_tris > 2_500_000 or len(pending) > 250:
        flush(); queued_tris = 0


# The staff, the Mirror of Choosing and the Spellbook were copied into the interior by integrate_academy.py, which
# records where each one's feet stand. (The mirror's copy in WorldPlan was later turned about a stale transform and
# stands outside the building, so the record is the one to trust.)
integration = json.loads((SOURCE.parent / 'WorldPlan_Academy_Integration.json').read_text())
for row in integration['staff_and_props']:
    if row['source'] != 'SpellbookRig':
        manifest['props'][row['source']] = {'feet': list(AX @ Vector(row['feet_position']) + INSIDE)}


# The world, scene by scene. The interior is lifted to INSIDE, clear of the campus.
for scene in sources:
    inside = scene.name.startswith('Academy Interior')
    if scene.name not in ('Scene',) and not inside: continue
    bpy.context.window.scene = scene
    cutting = bpy.data.collections.new('Roblox cut'); scene.collection.children.link(cutting)
    offset = AX.inverted() @ INSIDE if inside else Vector()
    shift = Matrix.Translation(offset)
    deps = bpy.context.evaluated_depsgraph_get()   # also brings every matrix_world up to date
    for o in scene.objects:
        if o.name.startswith(('PORTAL_', 'SPAWN_')):
            m = AX @ shift @ o.matrix_world
            manifest['markers'][o.name] = {'position': list(m.translation), 'scale': list(o.matrix_world.to_scale()),
                                           'properties': {k: o[k] for k in o.keys() if isinstance(o[k], (str, int, float))}}
        if o.type == 'LIGHT' and o.data.type == 'POINT' and not o.hide_render:
            manifest['lights'].append({'name': o.name, 'position': list(AX @ (shift @ o.matrix_world).translation),
                                       'color': list(o.data.color), 'energy': o.data.energy})
    found = set(); visible(scene.collection, found)
    for o in sorted(found, key=lambda x: x.name):
        if o.name.startswith(EXCLUDED_NAMES):
            manifest['excluded'].append(o.name); continue
        world = shift @ o.matrix_world
        if o.instance_type == 'COLLECTION' and o.instance_collection:
            c = o.instance_collection
            if c.name.startswith('Oak_'):
                tree = AX @ world @ AX.inverted()
                manifest['trees'].append({'template': re.sub(r'LOD\d', 'Roblox', c.name), 'matrix': [list(r) for r in tree]})
                continue
            group = area(o, inside)
            if ONLY and group not in ONLY or PATCH and o.name not in PATCH_SOURCES: continue
            for child in c.all_objects:
                if child.type in {'MESH', 'FONT', 'CURVE'} and not child.hide_render:
                    request(child, deps, world @ Matrix.Translation(-c.instance_offset) @ child.matrix_world, group,
                            o.name + ' / ' + child.name, cutting)
        elif o.type in {'MESH', 'FONT', 'CURVE'}:
            group = area(o, inside)
            if ONLY and group not in ONLY or PATCH and o.name not in PATCH_SOURCES: continue
            request(o, deps, world, group, o.name, cutting)
    flush()
    bpy.data.collections.remove(cutting)
    log(f'{scene.name}: {source_tris:,} source triangles read, {time.time() - started:.0f} s')

# Three oak templates serve every tree. Bark keeps 12% of its triangles; one leaf in four stays, twice the size.
templates = [] if PATCH else sorted({t['template'] for t in manifest['trees']})
scene = bpy.data.scenes['Scene']; bpy.context.window.scene = scene
deps = bpy.context.evaluated_depsgraph_get()
for template in templates:
    c = bpy.data.collections[template.replace('Roblox', 'LOD2')]
    for o in c.all_objects:
        if o.type != 'MESH': continue
        v, t, uv, col, mids, mats = mesh_arrays(o.evaluated_get(deps).to_mesh()); o.evaluated_get(deps).to_mesh_clear()
        a = np.array(Matrix.Translation(-c.instance_offset) @ o.matrix_world)
        v = (v @ a[:3, :3].T + a[:3, 3]).astype(np.float32)
        if 'leaves' in o.name.lower():
            v, kept = thin(v, t, .25, 1.9, foot=False); t, uv, mids = t[kept], uv[kept], mids[kept]
            col = None if col is None else col[kept]
            cut = ('planting', (), 1, False, 100000)
        else:
            mesh = bpy.data.meshes.new('cut bark'); mesh.from_pydata(v.tolist(), [], t.tolist())
            for m in mats: mesh.materials.append(m)
            mesh.polygons.foreach_set('material_index', mids)
            mesh.uv_layers.new(name='UVMap').data.foreach_set('uv', uv.ravel())
            tmp = bpy.data.objects.new('cut bark', mesh); scene.collection.objects.link(tmp)
            mod = tmp.modifiers.new('Cut', 'DECIMATE'); mod.ratio = .12; mod.use_collapse_triangulate = True
            ev = tmp.evaluated_get(bpy.context.evaluated_depsgraph_get())
            v, t, uv, col, mids, mats = mesh_arrays(ev.to_mesh()); ev.to_mesh_clear()
            bpy.data.objects.remove(tmp); bpy.data.meshes.remove(mesh)
            cut = ('building', (), 1, False, 100000)
        place((v, t, uv, col, mids, mats), Matrix(), template, o.name, cut)

def pieces(ids, centres, cell):
    """Split triangles at the median of their longer side until each piece fits Roblox's limit and its cell. A piece
    under 3,000 triangles stays whole however far it spreads, so no mesh is a sliver cut off by a cell edge."""
    c = centres[ids]; extent = c.max(axis=0) - c.min(axis=0)
    if len(ids) <= LIMIT and (extent.max() <= cell or len(ids) < 3000): return [ids]
    axis = int(np.argmax(extent)); order = np.argsort(c[:, axis], kind='stable'); half = len(ids) // 2
    return pieces(ids[order[:half]], centres, cell) + pieces(ids[order[half:]], centres, cell)


# Buckets become meshes, in pieces Roblox accepts.
bpy.context.window.scene = export_scene
materials = {}
def fbx_material(roblox, image_key):
    key = (roblox, image_key)
    if key in materials: return materials[key]
    # Match the actual optimized card images; keep its authored scalar settings
    # while leaving the legacy shared-material export rules unchanged.
    expected_images = {socket: bpy.data.images[name] for socket, name in image_key}
    card_source = next((source for source in bpy.data.materials
                        if source.get('wp_grass_cards') and shade(source)[3] == expected_images), None)
    card_shader = (next(n for n in card_source.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
                   if card_source else None)
    m = bpy.data.materials.new(f'WP {roblox}' + (' ' + image_key[0][1] if image_key else '')); m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value = (1, 1, 1, 1)
    if card_shader:
        for socket in ('Roughness', 'Specular IOR Level'):
            p.inputs[socket].default_value = card_shader.inputs[socket].default_value
    if 'Base Color' not in dict(image_key):
        tint = m.node_tree.nodes.new('ShaderNodeVertexColor'); tint.layer_name = 'Color'
        m.node_tree.links.new(tint.outputs['Color'], p.inputs['Base Color'])
    for socket, image_name in image_key:
        tex = m.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images[image_name]
        if socket == 'Normal':
            nm = m.node_tree.nodes.new('ShaderNodeNormalMap'); m.node_tree.links.new(tex.outputs['Color'], nm.inputs['Color'])
            if card_shader:
                original_normal = next((n for n in feeders(card_shader.inputs['Normal']) if n.type == 'NORMAL_MAP'), None)
                if original_normal:
                    nm.inputs['Strength'].default_value = original_normal.inputs['Strength'].default_value
            m.node_tree.links.new(nm.outputs[0], p.inputs['Normal'])
        elif socket == 'Alpha':
            m.node_tree.links.new(tex.outputs['Alpha'], p.inputs['Alpha'])
            m.surface_render_method = 'DITHERED'
        else: m.node_tree.links.new(tex.outputs['Color'], p.inputs[socket])
    materials[key] = m; return m


serial = defaultdict(int); by_group = defaultdict(list)
for key in sorted(buckets, key=str):
    group, roblox, collide, cell, image_key, night, double = key
    b = buckets[key]
    v = np.concatenate(b.v); t = np.concatenate(b.t); uv = np.concatenate(b.uv); col = np.concatenate(b.col)
    centres = v[t].mean(axis=1)[:, :2]   # Blender X and Y: the map's plan
    for ids in pieces(np.arange(len(t)), centres, cell):
        vert_ids, faces = np.unique(t[ids].ravel(), return_inverse=True)
        coords = v[vert_ids]; lo, hi = coords.min(axis=0), coords.max(axis=0); centre = (lo + hi) / 2
        serial[group] += 1; name = f'WP_{group}_P{serial[group]:02d}' if PATCH else f'WP_{group}_{serial[group]:03d}'
        data = bpy.data.meshes.new(name)
        data.from_pydata((coords - centre).tolist(), [], faces.reshape(-1, 3).tolist())
        data.materials.append(fbx_material(roblox, image_key))
        data.uv_layers.new(name='UVMap').data.foreach_set('uv', uv[ids].ravel())
        data.color_attributes.new(name='Color', type='FLOAT_COLOR', domain='CORNER').data.foreach_set('color', col[ids].ravel())
        data.polygons.foreach_set('use_smooth', [True] * len(data.polygons))
        data.set_sharp_from_angle(angle=math.radians(35))
        obj = bpy.data.objects.new(name, data); export_scene.collection.objects.link(obj); obj.location = centre
        size = hi - lo
        sources = sorted(b.sources, key=lambda s: -b.sources[s])
        precise = collide and (size[2] > 3 or group.startswith('Academy') or group in
                               ('EmberClaw', 'Stoneroot', 'Skyquill', 'Nightfang'))
        row = {'name': name, 'group': group, 'triangles': len(ids), 'position': list(AX @ Vector(centre)),
               'size': [float(size[0]), float(size[2]), float(size[1])], 'material': roblox,
               'collision': ('precise' if precise else 'default') if collide else 'none',
               'double_sided': bool(double), 'images': [n for _, n in image_key], 'night': night.split(' / ')[-1].split('.')[0] if night else None,
               'sources': sources[:4]}
        if image_key:
            row['texture_maps'] = dict(image_key)
        if any(socket == 'Alpha' for socket, _ in image_key):
            row['alpha_mode'] = 'Transparency'
            row['transparency'] = 0
        manifest['meshes'].append(row); by_group[group].append(obj)
    buckets[key] = None

# Oak templates: their parts' offsets from the tree's root, for install_worldplan.lua to build each tree.
for template in templates:
    manifest['templates'][template] = [{'name': r['name'], 'offset': r['position'], 'size': r['size'],
                                        'leaves': r['material'] == 'LeafyGrass'} for r in manifest['meshes'] if r['group'] == template]

# One FBX per area (two when it is large); the three oaks share one.
files = defaultdict(list)
for group, objects in by_group.items():
    stem = 'Patch' if PATCH else 'Trees' if group.startswith('Oak_') else group
    files[stem] += objects
for old in OUT.glob('WP_*.fbx'):
    if not ONLY: old.unlink()
for stem, objects in sorted(files.items()):
    for index, start in enumerate(range(0, len(objects), PER_FILE), 1):
        chosen = objects[start:start + PER_FILE]
        filename = f'WP_{stem}.fbx' if len(objects) <= PER_FILE else f'WP_{stem}_{index}.fbx'
        bpy.ops.object.select_all(action='DESELECT')
        for o in chosen: o.select_set(True)
        bpy.context.view_layer.objects.active = chosen[0]
        bpy.ops.export_scene.fbx(filepath=str(OUT / filename), use_selection=True, object_types={'MESH'}, global_scale=1,
                                 apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS', axis_forward='Z', axis_up='Y',
                                 use_mesh_modifiers=False, use_triangles=True, colors_type='SRGB', add_leaf_bones=False,
                                 bake_anim=False, path_mode='COPY', embed_textures=True)
        manifest['files'].append({'file': filename, 'meshes': [o.name for o in chosen],
                                  'triangles': sum(len(o.data.polygons) for o in chosen),
                                  'megabytes': round((OUT / filename).stat().st_size / 1e6, 1)})
        log(f'{filename}: {len(chosen)} meshes, {manifest["files"][-1]["triangles"]:,} triangles')
if PATCH:
    # The patch's meshes take the patched ones' places in the full manifest; the patched names are recorded so
    # install_worldplan.lua's Patch stage can remove them from the place.
    new = manifest['meshes']; manifest = old_manifest
    manifest['meshes'] = [r for r in manifest['meshes'] if r['name'] not in PATCH] + new
    for file in manifest['files']: file['meshes'] = [n for n in file['meshes'] if n not in PATCH]
    manifest['files'] = [f for f in manifest['files'] if f['meshes'] and f['file'] != 'WP_Patch.fbx']
    manifest['files'].append({'file': 'WP_Patch.fbx', 'meshes': [r['name'] for r in new],
                              'triangles': sum(r['triangles'] for r in new), 'replaces': sorted(PATCH)})
    manifest.setdefault('patched', []).extend(sorted(PATCH))
    log('Patch: ' + ', '.join(f"{r['name']} ({r['collision']}, {r['sources'][0]})" for r in new))
name = 'manifest.json' if not ONLY or PATCH else 'manifest-partial.json'
(OUT / name).write_text(json.dumps(manifest, indent=1))
total = sum(r['triangles'] for r in manifest['meshes'] if not r['group'].startswith('Oak_'))
log(f'DONE in {time.time() - started:.0f} s: {source_tris:,} source triangles to {total:,} in '
    f'{sum(not r["group"].startswith("Oak_") for r in manifest["meshes"])} meshes, {len(manifest["files"])} files; '
    f'{len(manifest["trees"])} trees of {sum(r["triangles"] for r in manifest["meshes"] if r["group"].startswith("Oak_")):,} template triangles')

if PREVIEW:
    # Cycles pictures of the export from WorldPlan's cameras, to set beside the source's own renders
    # (exports/WorldPlan_*.png). They render on the CPU, as Workbench crashes on the house views. Each mesh shows its
    # vertex colours or its exported textures, including grass alpha. Trees stand as instances of the templates.
    trees = bpy.data.collections.new('Preview trees'); export_scene.collection.children.link(trees)
    kits = {}
    for template in templates:
        kit = bpy.data.collections.new('kit ' + template); kits[template] = kit
        for o in by_group[template]: kit.objects.link(o); export_scene.collection.objects.unlink(o)
    for i, tree in enumerate(manifest['trees']):
        e = bpy.data.objects.new(f'tree {i}', None); e.instance_type = 'COLLECTION'; e.instance_collection = kits[tree['template']]
        e.matrix_world = AX.inverted() @ Matrix(tree['matrix']) @ AX; trees.objects.link(e)
    sc = export_scene
    sc.world = bpy.data.worlds.new('Preview'); sc.world.use_nodes = True
    sc.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.55, .62, .72, 1)
    sun = bpy.data.objects.new('Preview sun', bpy.data.lights.new('Preview sun', 'SUN')); sun.data.energy = 3.5
    sun.rotation_euler = (math.radians(50), 0, math.radians(35)); sc.collection.objects.link(sun)
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 16; sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 3; sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.render.image_settings.file_format = 'PNG'
    views = sorted((o for o in bpy.data.scenes['Scene'].objects if o.type == 'CAMERA' and o.name[:2].isdigit()),
                   key=lambda o: o.name)
    for view in views:
        if view.name not in sc.objects: sc.collection.objects.link(view)
        sc.camera = view; stem = re.sub(r'\W+', '_', view.name).strip('_')
        sc.render.filepath = str(OUT / f'preview_{stem}.png'); bpy.ops.render.render(write_still=True)
        log('preview ' + stem)
