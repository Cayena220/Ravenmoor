"""The whole of Ravenmoor in one Blender scene: blender/exports/World.blend.

Open it to see every model where the game has it before you change one, or to block out a new model where it will
stand. The scene is assembled, not edited by hand: run this again after changing tools/build.py, tools/layout.py or
any model, and it is rebuilt from them. Each area is a collection:
  * the part-built map from tools/build.py, laid out by tools/layout.py (land, roads, lamps, the academy 300 studs
    north of Hollowmere, Whisperwood 300 west, the Castle Grounds and their landmarks, the duel arena, Mirrorlake,
    chests and the staff), rebuilt as meshes in the parts' colours, one object per model, so the scene always
    matches the map build.py makes;
  * the Blender models, appended from their own .blend files in exports/ and stood where the game has them, as
    listed in PLACED: Hollowmere over the map's part village, its road lamps, dock and ferry (keeping the map's
    ground), the three Waystones over the slate stones, and the mountain ranges and woods round everything;
  * the models the game builds in code, the interaction markers as labelled empties, and Config's zones and world
    bounds as frames over the map.

Build the models first: python tools/blender.py "blender/*/*.py" runs the scripts in folder order, so this one
(blender/world/) comes last. To add a model, write its script under blender/models/ and give it a line in PLACED.
Each model still exports to Studio on its own (blender/README.md).
"""
import ctypes
import ctypes.util
import heapq
import json
import math
import os
import re
import xml.etree.ElementTree as ET
import bmesh
import bpy
from mathutils import Matrix, Vector
import build
import layout
import rbx
import terrain

# Roblox (X right, Y up, Z back) to Blender (Z up, front -Y): Blender -X is Roblox +X.
AXES = Matrix(((-1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))


def bl(x, y, z): return Vector((-x, z, y))


def name_of(node): return node.findtext("Properties/string[@name='Name']")


def prop(node, kind, name): return node.find(f"Properties/{kind}[@name='{name}']")


NAME = 'World'


# What the Blender models replace on the part map.
VILLAGE_GROUND = {'Plaza tile', 'Plaza border', 'Shop lane', 'Garden path'}   # all Hollowmere keeps of the map's village
VILLAGE_LAMPS_FROM_Z = 60                                                     # road lamps from here south are Hollowmere's


def replaced(path, node):
    top = path[0] if path else ''
    if top == 'Hollowmere': return name_of(node) not in VILLAGE_GROUND
    if top == 'Lamps': return float(prop(node, 'CoordinateFrame', 'CFrame').findtext('Z')) >= VILLAGE_LAMPS_FROM_Z
    if top.endswith(' Waystone'): return True
    return False


class Parts(rbx.Mesh):
    """Roblox parts as one mesh: blocks, wedges, cylinders and balls, each through its CFrame and size."""

    def add(self, node):
        """A part from the map's XML."""
        size = [float(prop(node, 'Vector3', 'size').findtext(k)) for k in 'XYZ']
        cf = prop(node, 'CoordinateFrame', 'CFrame')
        frame = [float(cf.findtext(k)) for k in ('X', 'Y', 'Z', 'R00', 'R01', 'R02', 'R10', 'R11', 'R12', 'R20', 'R21', 'R22')]
        v = int(prop(node, 'Color3uint8', 'Color3uint8').text)
        shape = prop(node, 'token', 'shape')
        self.part(size, frame, ((v >> 16) & 255, (v >> 8) & 255, v & 255), int(shape.text) if shape is not None else 1,
                  node.get('class') == 'WedgePart')

    def part(self, size, frame, colour, shape=1, wedge=False):
        """A part from its size, its CFrame as (x, y, z, R00 ... R22), its colour and its shape (0 ball, 1 block,
        2 cylinder)."""
        x, y, z, *r = frame
        m = AXES @ Matrix(((r[0], r[1], r[2], x), (r[3], r[4], r[5], y), (r[6], r[7], r[8], z), (0, 0, 0, 1))) \
            @ Matrix.Diagonal((*size, 1))
        if wedge:
            # A ramp: low along the front (-Z), rising to a vertical back face (+Z).
            corners = [m @ Vector((sx, py, pz)) for sx in (-0.5, 0.5) for py, pz in ((-0.5, -0.5), (-0.5, 0.5), (0.5, 0.5))]
            v = [self.bm.verts.new(self.frame @ c) for c in corners]
            faces = [self.bm.faces.new(f) for f in ((v[0], v[1], v[2]), (v[3], v[5], v[4]), (v[0], v[3], v[4], v[1]),
                                                     (v[1], v[4], v[5], v[2]), (v[0], v[2], v[5], v[3]))]
            self._paint(faces, colour, None)
        elif shape == 0:
            self._made(bmesh.ops.create_uvsphere(self.bm, u_segments=12, v_segments=6, radius=0.5, matrix=self.frame @ m), colour, None)
        elif shape == 2:   # a Roblox cylinder runs along the part's X
            made = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=16, radius1=0.5, radius2=0.5,
                                         depth=1, matrix=self.frame @ m @ Matrix.Rotation(math.radians(90), 4, 'Y'))
            self._made(made, colour, None)
        else:
            self.block(m, colour)


def collection(name, parent=None):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in (parent or bpy.context.scene.collection).children: (parent or bpy.context.scene.collection).children.link(c)
    return c


def move(obj, target):
    for c in list(obj.users_collection): c.objects.unlink(obj)
    target.objects.link(obj)
    for child in obj.children: move(child, target)


rbx.scene('World')

# ---- The part map, from tools/build.py ------------------------------------------------------------------------
workspace = build.item(ET.Element('roblox'), 'Workspace', 'Workspace')
world, markers, spawns = build.make_world(workspace)
PARTS = ('Part', 'WedgePart', 'SpawnLocation')
GROUND = []    # (x0, x1, z0, z1, top) of level, collidable parts, for standing models on the map
counts = {}


def visible(node):
    t = prop(node, 'float', 'Transparency')
    return not (t is not None and float(t.text) >= 0.99)


def note_ground(node):
    cf, s = prop(node, 'CoordinateFrame', 'CFrame'), prop(node, 'Vector3', 'size')
    turn = abs(float(cf.findtext('R00')))   # the extents below hold for a part turned a whole number of quarter turns
    if prop(node, 'bool', 'CanCollide').text != 'true' or abs(float(cf.findtext('R11')) - 1) > 1e-6 \
            or min(turn, abs(turn - 1)) > 1e-6: return
    x, y, z = (float(cf.findtext(k)) for k in 'XYZ'); sx, sy, sz = (float(s.findtext(k)) for k in 'XYZ')
    GROUND.append((x - sx / 2, x + sx / 2, z - sz / 2, z + sz / 2, y + sy / 2))


SPOTS = []   # (group, kind, label, (x, z)) of every map part, monster and marker, for the zones report


def spot(path, node):
    """Note a map part for the zones report under its top model, the rune chests together. The ground under
    everything is left out."""
    top = path[0] if path else ''
    if top == 'Land': return
    cf = prop(node, 'CoordinateFrame', 'CFrame')
    SPOTS.append(('Rune chests' if top.startswith('RuneChest') else top, 'part', None, (float(cf.findtext('X')), float(cf.findtext('Z')))))


def mesh_of(name, nodes, area):
    mesh = Parts(name); n = 0
    for path, node in nodes:
        if node.get('class') in PARTS and visible(node):
            spot(path, node)   # the Blender models stand where the parts they replace did
            if replaced(path, node): continue
            mesh.add(node); note_ground(node); n += 1
    obj = mesh.finish(sharp=30)
    if obj: move(obj, area); counts[area.name] = counts.get(area.name, 0) + n


def walk(node, path):
    for child in node.findall('Item'):
        yield path, child
        yield from walk(child, path + [name_of(child)])


game = collection('Ravenmoor')
for top in world.findall('Item'):
    name = name_of(top)
    if name.endswith(' Waystone'): continue
    area = collection(name if not name.startswith('RuneChest') else 'Rune chests', game)
    loose = [([name], n) for n in top.findall('Item') if n.get('class') in PARTS]
    if top.get('class') in PARTS: loose.append(([name], top))
    mesh_of('Village ground' if name == 'Hollowmere' else name, loose, area)
    for sub in top.findall('Item'):
        if sub.get('class') not in PARTS:   # each model or folder inside an area is one object
            mesh_of(name_of(sub), list(walk(sub, [name, name_of(sub)])), area)
mesh_of('Hollowmere arrival', [(['Spawns'], n) for n in spawns.findall('Item')], collection('Spawns', game))

# The ground mist for the EEVEE pictures: a volume, drawn only by them, so hidden in the viewport and the previews.
mist_room = collection('Mist', game)
mist_room.hide_render = mist_room.hide_viewport = True
terrain.mist(mist_room, layout.MEADOW)


def ground_at(x, z, below):
    """The top of the highest level part under (x, z) that is no higher than `below`; the meadow is at 0."""
    tops = [t for x0, x1, z0, z1, t in GROUND if x0 <= x <= x1 and z0 <= z <= z1 and t <= below]
    return max(tops, default=0.0)


# The interaction markers, as labelled empties where the prompts and quest waypoints are.
marks = collection('Markers', game)
for node in markers.findall('Item'):
    cf = prop(node, 'CoordinateFrame', 'CFrame')
    e = bpy.data.objects.new(name_of(node), None)
    e.empty_display_type, e.empty_display_size, e.show_name = 'SPHERE', 0.6, True
    e.location = bl(*(float(cf.findtext(k)) for k in 'XYZ'))
    marks.objects.link(e)


# ---- The Blender models ----------------------------------------------------------------------------------------
def append(blend):
    """Every object in exports/<blend> except preview helpers (names starting with _), cameras and lights."""
    path = rbx.EXPORTS / blend
    if not path.exists():
        raise SystemExit(f'exports/{blend} is missing. Build the models first: python tools/blender.py "blender/*/*.py"')
    with bpy.data.libraries.load(str(path), link=False) as (source, target):
        target.objects = [n for n in source.objects if not n.startswith('_')]
    keep = []
    for obj in target.objects:
        if obj is None: continue
        if obj.type in ('CAMERA', 'LIGHT'): bpy.data.objects.remove(obj); continue
        keep.append(obj)
    return keep


def roots(objs): return [o for o in objs if o.parent is None or o.parent not in objs]


def place(objs, at, turn=0.0, area=None):
    """Stand the appended model's top objects at a Roblox point (or the origin, for a model built in place), turned
    `turn` radians about the vertical. The transform is set, not added to, so a stray move or scale saved into an
    exports/ .blend never reaches the world. Rigs stand in their rest pose."""
    for o in roots(objs):
        o.location = bl(*at) if at else Vector((0, 0, 0))
        o.rotation_euler, o.scale = (0, 0, turn), (1, 1, 1)
    for o in objs:
        area.objects.link(o)
        if o.type == 'ARMATURE':
            if o.animation_data: o.animation_data.action = None
            for pb in o.pose.bones: pb.matrix_basis = Matrix.Identity(4)
    return objs


def facing(frm, to):
    """The turn that points a model's front (Blender -Y, the part's LookVector) from one Roblox point toward another."""
    d = bl(*to) - bl(*frm)
    return math.atan2(d.x, -d.y)


config = (build.ROOT / 'src/shared/Config.lua').read_text(encoding='utf-8')
LANDINGS = {k: tuple(map(float, v.split(','))) for k, v in re.findall(r'(\w+) = \{([-\d., ]+)\}', config.split('Waystones =')[1].split('\n')[0])}
NUMBER = r'(-?[\d.]+)'
ZONES = [(id_, name, *map(float, box), safe == 'true') for id_, name, *box, safe in re.findall(   # id, name, x, z, w, d, safe
    rf'\{{Id = "(\w+)", Name = "([^"]+)", Center = \{{{NUMBER}, {NUMBER}\}}, Size = \{{{NUMBER}, {NUMBER}\}}, Safe = (\w+)\}}', config)]
BOUNDS = tuple(map(float, re.search(rf'WorldBounds = \{{MinX = {NUMBER}, MaxX = {NUMBER}, MinZ = {NUMBER}, MaxZ = {NUMBER}\}}',
                                    config).groups()))   # min x, max x, min z, max z


def zone_of(x, z):
    """The zone WorldService:Zone finds at (x, z): the first in Config.Zones that holds it, or None for its fallback,
    a safe Castle Grounds."""
    return next((zone for zone in ZONES if abs(x - zone[2]) <= zone[4] / 2 and abs(z - zone[3]) <= zone[5] / 2), None)


def in_bounds(x, z): return BOUNDS[0] <= x <= BOUNDS[1] and BOUNDS[2] <= z <= BOUNDS[3]


def outline(area, label, x0, x1, z0, z1, height, width, colour, label_z=None):
    """A frame over the ground from (x0, z0) to (x1, z1), Roblox studs: rails `height` up on a post at each corner,
    and the label lying on top, in the middle or at `label_z`, to read from above with north up."""
    mesh, level = Parts(label), (1, 0, 0, 0, 1, 0, 0, 0, 1)
    for z in (z0, z1): mesh.part((x1 - x0 + width, width, width), ((x0 + x1) / 2, height, z, *level), colour)
    for x in (x0, x1): mesh.part((width, width, z1 - z0 + width), (x, height, (z0 + z1) / 2, *level), colour)
    for x in (x0, x1):
        for z in (z0, z1): mesh.part((width, height, width), (x, height / 2, z, *level), colour)
    move(mesh.finish(sharp=30), area)
    text = bpy.data.curves.new(label, 'FONT')
    text.body, text.align_x, text.align_y = label, 'CENTER', 'CENTER'
    text.size = max(8, min(22, 1.5 * (x1 - x0) / len(label)))   # a letter is about 0.6 of the size wide
    obj = bpy.data.objects.new(label + ' label', text); area.objects.link(obj)
    at = bl((x0 + x1) / 2, height + 1, (z0 + z1) / 2 if label_z is None else label_z)
    obj.location, obj.rotation_euler.z = at, math.pi   # reads west to east


# Config's zones and world bounds as frames over the map, red where monsters attack, blue where they don't and gold
# round the world. Hidden from the previews but the zones one; switch the collection off in Blender to hide them there.
zones = collection('Config zones', game)
zones.hide_render = True
for i, (id_, name, x, z, w, d, safe) in enumerate(ZONES, 1):
    outline(zones, f'{i}. {name} ({"safe" if safe else "unsafe"})', x - w / 2, x + w / 2, z - d / 2, z + d / 2, 90, 3,
            (70, 150, 230) if safe else (225, 70, 60))
outline(zones, 'World bounds', *BOUNDS, 110, 4, (240, 200, 70), label_z=BOUNDS[2] + 25)


def waystones(area):
    """Three Waystones, each centred on its marker, on the ground under it, its sigil turned toward where
    Config.Waystones lands travellers (blender/place_waystones.lua does the same in Studio)."""
    model = append('Waystone.blend')
    meshes = [o for o in model if o.type == 'MESH']
    for key in ('Hollowmere', 'Castle', 'Whisperwood'):
        x, y, z = build.POINTS['Waystone_' + key]
        base = (x, ground_at(x, z, y) - 0.02, z)
        holder = bpy.data.objects.new(key + ' Waystone', None); area.objects.link(holder)
        holder.location = bl(*base); holder.rotation_euler.z = facing(base, LANDINGS[key])
        for m in meshes:
            c = m.copy(); c.parent = holder; area.objects.link(c)
    for o in model: bpy.data.objects.remove(o)


def append_actions(blend):
    """Every animation in exports/<blend>, kept in the world file so it can be played on its model there."""
    with bpy.data.libraries.load(str(rbx.EXPORTS / blend), link=False) as (source, target):
        names = list(source.actions)
        target.actions = [n for n in names if n not in bpy.data.actions]   # a rig's own clip came with the rig
    found = {n: bpy.data.actions.get(n) for n in names}
    for action in found.values():
        if action: action.use_fake_user = True
    return {n: a for n, a in found.items() if a}


ROOT_HEIGHT = 2.971   # a standing R15 avatar's HumanoidRootPart above the floor (blender/animations/character.py)
PAD = (90, 1.0, 184)  # the top of the Hollowmere arrival pad, where players spawn

PLACED = [   # (exports .blend, collection, where the game stands it in Roblox studs or None if built in place, facing)
    ('Hollowmere.blend', 'Hollowmere', None, None),
    ('Cauldron.blend', 'Hollowmere', (53.6, 0.45, 177.2), None),                              # by the Apothecary's door
    ('Spellbook.blend', 'Ravenmoor Academy', layout.moved((4, 43.4, -268), 'Academy'), None),  # floating in the Library
    ('Character.blend', 'Spawns', (PAD[0], PAD[1] + ROOT_HEIGHT, PAD[2]), None),               # on the arrival pad
    ('Ranges.blend', 'Scenery', None, None),                                                   # round everything
]
placed = {blend: place(append(blend), at, turn or 0.0, collection(area, game)) for blend, area, at, turn in PLACED}
waystones(collection('Waystones', game))
actions = {**append_actions('Character.blend'), **append_actions('Spellbook.blend')}


def dash(area, start, end):
    """The dash effect (blender/vfx/dash.py) frozen just after a dodge from `start` to `end`, Roblox points at root
    height, laid out as EffectsController:Dash lays it: the streak over the path, the shock ring blooming at the
    start, the speed lines trailing into the landing and the dust ring flat on the ground there. In game the
    meshes glow Neon in the arcane colour; here they keep their near-white."""
    model = append('DashVFX.blend')
    pieces = {o.name.split('.')[0]: o for o in model if o.type == 'MESH'}
    spin = Matrix.Rotation(facing(start, end), 4, 'Z')

    def put(name, label, at, tilt=Matrix.Identity(4), scale=1.0):
        o = pieces[name].copy(); o.parent = None; o.name = label; area.objects.link(o)
        o.matrix_world = Matrix.Translation(at) @ spin @ tilt @ Matrix.Diagonal((scale, scale, scale, 1))

    put('Streak', 'Dash streak', (bl(*start) + bl(*end)) / 2)
    put('Ring', 'Dash shock ring', bl(*start), scale=1.4)
    front = min(v.co.y for v in pieces['Speed lines'].data.vertices)   # the lines' front ends, at the landing
    put('Speed lines', 'Dash speed lines', bl(*end) - spin.to_3x3() @ Vector((0, front, 0)))
    floor = ground_at(end[0], end[2], end[1])
    put('Ring', 'Dash dust ring', bl(end[0], floor + 0.1, end[2]), Matrix.Rotation(math.radians(90), 4, 'X'), 1.3)
    for o in model: bpy.data.objects.remove(o)


def pose(area, rig, mesh, clip, frame, at, name):
    """A copy of the character frozen at one frame of a clip, facing north as players spawn."""
    r, m = rig.copy(), mesh.copy()
    r.name, m.name = name + ' rig', name
    area.objects.link(r); area.objects.link(m)
    m.parent = r
    for modifier in m.modifiers:
        if modifier.type == 'ARMATURE': modifier.object = r
    r.location, r.rotation_euler = bl(*at), (0, 0, 0)
    data = r.animation_data or r.animation_data_create()
    data.action = actions[clip]
    if getattr(actions[clip], 'slots', None) and hasattr(data, 'action_slot'): data.action_slot = actions[clip].slots[0]
    bpy.context.scene.frame_set(frame)
    held = {pb.name: pb.matrix_basis.copy() for pb in r.pose.bones}
    data.action = None
    for pb in r.pose.bones: pb.matrix_basis = held[pb.name]


# ---- The models the game builds in code ------------------------------------------------------------------------
WAND_GALLERY = (64, 3, 181)    # open meadow west of the arrival pad: woods along X, rarities south, named wands last
CODE_AREAS = {'Monsters': 'Whisperwood', 'Wands': 'Showcase', 'Training dummies': 'Castle Grounds',
              'Lesson targets': 'Ravenmoor Academy'}
SHAPES = {'Ball': 0, 'Block': 1, 'Cylinder': 2}


def lua():
    """Lua 5.4, found as tools/validate.py finds it, or None."""
    for candidate in (os.environ.get('WANDBOUND_LUA_LIBRARY'), ctypes.util.find_library('lua5.4'),
                      ctypes.util.find_library('lua54'), r'C:\xampp\apache\bin\lua54.dll'):   # where XAMPP puts it
        if candidate and (os.path.exists(candidate) or not os.path.isabs(candidate)):
            try: return ctypes.CDLL(candidate)
            except OSError: continue
    return None


def code_models():
    """Run blender/world/game_models.lua: the game's own builders for monsters, wands, dummies and lesson targets."""
    lib = lua()
    if lib is None:
        rbx.say('Skipped the code-built models: no Lua 5.4. Set WANDBOUND_LUA_LIBRARY as for tools/validate.py.')
        return []
    lib.luaL_newstate.restype = ctypes.c_void_p
    lib.luaL_openlibs.argtypes = [ctypes.c_void_p]
    lib.luaL_loadstring.argtypes = [ctypes.c_void_p, ctypes.c_char_p]; lib.luaL_loadstring.restype = ctypes.c_int
    lib.lua_pcallk.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_longlong, ctypes.c_void_p]
    lib.lua_pcallk.restype = ctypes.c_int
    lib.lua_tolstring.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]; lib.lua_tolstring.restype = ctypes.c_char_p
    lib.lua_close.argtypes = [ctypes.c_void_p]
    state = lib.luaL_newstate(); lib.luaL_openlibs(state)
    code = (f'ROOT={json.dumps(str(build.ROOT))}; GALLERY={{{",".join(map(str, WAND_GALLERY))}}}; '
            f'return dofile(ROOT.."/blender/world/game_models.lua")')
    assert lib.luaL_loadstring(state, code.encode()) == 0
    if lib.lua_pcallk(state, 0, 1, 0, 0, None):
        raise SystemExit('blender/world/game_models.lua failed: ' + lib.lua_tolstring(state, -1, None).decode())
    out = lib.lua_tolstring(state, -1, None).decode(); lib.lua_close(state)
    return json.loads(out)


built = {}
for model in code_models():
    mesh = Parts(model['name'])
    if model['group'] == 'Monsters':   # where it spawns, for the zones report: monsters only attack outside safe zones
        SPOTS.append(('Whisperwood', 'monster', None, tuple(sum(p['cframe'][k] for p in model['parts']) / len(model['parts'])
                                                            for k in (0, 2))))
    for p in model['parts']:
        mesh.part(p['size'], p['cframe'], tuple(min(255, round(c)) for c in p['color']), SHAPES.get(p['shape'], 1))
    obj = mesh.finish(sharp=30)
    if obj:
        move(obj, collection(CODE_AREAS[model['group']], game))
        built[model['group']] = built.get(model['group'], 0) + 1

showcase = collection('Showcase', game)
character = placed['Character.blend']
rig = next(o for o in character if o.type == 'ARMATURE'); body = next(o for o in character if o.type == 'MESH')
# A dodge east across the pad, landing where the mannequin stands, and the clips posed in a row beside it.
dash(showcase, (PAD[0] - 10, PAD[1] + ROOT_HEIGHT, PAD[2]), (PAD[0], PAD[1] + ROOT_HEIGHT, PAD[2]))
for i, (clip, frame, label) in enumerate((('CharacterWalk', 0, 'Walk'), ('CharacterSprint', 5, 'Sprint'),
                                          ('CharacterTumbleRight', 6, 'Tumble'))):
    x = PAD[0] + 8 + 5 * i
    pose(showcase, rig, body, clip, frame, (x, ground_at(x, PAD[2], PAD[1] + 1) + ROOT_HEIGHT, PAD[2]), 'Mannequin ' + label)
# The four brooms (blender/models/brooms.py) hovering in a row south of the pad, each seat at a rider's height and
# each tip to the north; the row runs west from Ashwind, the primary broom.
BROOMS_AT = (PAD[0] + 8, PAD[2] + 9)
seat = ground_at(*BROOMS_AT, PAD[1] + 1) + ROOT_HEIGHT
place(append('Brooms.blend'), (BROOMS_AT[0], seat, BROOMS_AT[1]), 0.0, showcase)
# A mannequin on each broom in that broom's own ride, its root 1.35 studs over the seat as FlightService welds it
# (BroomData's SeatDrop). brooms.py lays the brooms out 3.2 studs apart in this order.
for k, (broom, frame) in enumerate((('Ashwind', 18), ('Swiftquill', 0), ('Stoutbough', 0), ('Nightwing', 12))):
    pose(showcase, rig, body, 'CharacterBroomRide' + broom, frame, (BROOMS_AT[0] - 3.2 * k, seat + 1.35, BROOMS_AT[1]),
         'Mannequin ' + broom)
bpy.context.scene.frame_set(0)

rbx.viewport(bl(88, 0, 150), 240, turn=(55, 0, 153))
for obj in bpy.context.view_layer.objects: obj.select_set(False)   # open with nothing selected
rbx.EXPORTS.mkdir(exist_ok=True)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(rbx.EXPORTS / f'{NAME}.blend'), check_existing=False)
total = sum(counts.values())
rbx.say(f'exports/{NAME}.blend: {total:,} map parts in {len(counts)} areas, {len(PLACED) + 3} Blender models '
        f'(with the Waystone, the dash and the brooms), {len(actions)} animations, {len(markers.findall("Item"))} markers')
rbx.say(f'exports/{NAME}.blend: built in code by the game: ' + (', '.join(f'{n} {g.lower()}' for g, n in built.items()) or 'none'))


def walks(roads, places):
    """The studs walked between each pair of places (Roblox x, z) along roads given as (a, b) centrelines. Two roads
    join where one's end lies on the other, and a place off the roads walks straight to the nearest one."""
    def foot(p, a, b):   # the nearest point to p on the road from a to b, and how far along it, 0 to 1
        dx, dz = b[0] - a[0], b[1] - a[1]
        t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dz) / (dx * dx + dz * dz)))
        return (a[0] + t * dx, a[1] + t * dz), t
    stops = [[(0.0, a), (1.0, b)] for a, b in roads]
    for i, (a, b) in enumerate(roads):
        for j, other in enumerate(roads):
            for end in other if j != i else ():
                q, t = foot(end, a, b)
                if math.dist(q, end) < 0.5: stops[i].append((t, end))
    joins = []
    for p in places:
        (q, t), i = min(((foot(p, a, b), i) for i, (a, b) in enumerate(roads)), key=lambda f: math.dist(f[0][0], p))
        stops[i].append((t, q)); joins.append((q, math.dist(p, q)))
    key = lambda p: (round(p[0], 2), round(p[1], 2))
    graph = {}
    for line in stops:
        line.sort()
        for (_, p), (_, q) in zip(line, line[1:]):
            graph.setdefault(key(p), []).append((key(q), math.dist(p, q)))
            graph.setdefault(key(q), []).append((key(p), math.dist(p, q)))

    def from_(start):
        best, todo = {start: 0.0}, [(0.0, start)]
        while todo:
            d, n = heapq.heappop(todo)
            if d > best[n]: continue
            for m, w in graph.get(n, ()):
                if d + w < best.get(m, math.inf): best[m] = d + w; heapq.heappush(todo, (d + w, m))
        return best
    return [[from_(key(qa))[key(qb)] + ga + gb for qb, gb in joins] for qa, ga in joins]


# Walking times between the places players walk to, along the roads at 16 studs a second, as the crow flies in
# brackets: the gap is what leaving the roads saves. The Waystones stand at the square, the gate and the forest gate.
GATE = (85, layout.GATE_Z - 6 + layout.AZ)
PLACES = [('Square', (85, 114)), ('Gate', GATE), ('West wing', (10, -20 + layout.AZ)),
          ('Yard', build.POINTS['Training'][::2]), ('Tobb', build.POINTS['Tobb'][::2]), ('Forest gate', (-38 + layout.FX, 18))]
spots = [where for _, where in PLACES]
studs = walks([line for line, _ in layout.ROADS], spots)
rbx.say(f'exports/{NAME}.blend: walking times in seconds, by road and (as the crow flies):')
rbx.say(' ' * 12 + ''.join(f'{name:>12}' for name, _ in PLACES))
for i, (name, _) in enumerate(PLACES):
    cells = ['-' if i == j else f'{studs[i][j] / 16:.0f} ({math.dist(spots[i], spots[j]) / 16:.0f})' for j in range(len(PLACES))]
    rbx.say(f'{name:<12}' + ''.join(f'{c:>12}' for c in cells))

# What falls outside Config's world bounds and zones: none of the map's parts, monsters or markers should.
MARKER_GROUPS = {'Academy': 'Ravenmoor Academy', 'Forest': 'Whisperwood', 'City': 'Hollowmere'}
for key, (x, _, z) in build.POINTS.items():
    SPOTS.append((MARKER_GROUPS[layout.marker_area(key)], 'marker', key, (x, z)))


def report(title, pick):
    """A line per heading that `pick(group, (x, z))` gives a spot (None leaves it out), listing each group's parts
    and monsters there, counted out of the group's, and its markers by name. Returns whether anything was listed."""
    totals, found = {}, {}
    for group, kind, label, where in SPOTS:
        totals[group, kind] = totals.get((group, kind), 0) + 1
        heading = pick(group, where)
        if heading: found.setdefault(heading, {}).setdefault(group, []).append((kind, label))
    if not found: return False
    rbx.say(f'exports/{NAME}.blend: {title}:')
    for heading, groups in found.items():
        items = []
        for group, hits in groups.items():
            counts = [f'{n:,} of {totals[group, kind]:,} {kind}s' for kind in ('part', 'monster')
                      if (n := sum(k == kind for k, _ in hits))]
            listed = ', '.join(counts + [label for kind, label in hits if kind == 'marker'])
            items.append(listed if group == heading else f'{group} {listed}')
        rbx.say(f'  {heading}: ' + '; '.join(items))
    return True


listed = [report('outside Config.WorldBounds, where WorldService sends players back', lambda g, at: None if in_bounds(*at) else g),
          report('in no zone of Config.Zones, which WorldService takes for a safe Castle Grounds, where monsters never attack',
                 lambda g, at: g if in_bounds(*at) and zone_of(*at) is None else None),
          report('Castle Grounds landmarks in an unsafe zone, where monsters attack',
                 lambda g, at: g if g in layout.GROUNDS and zone_of(*at) and not zone_of(*at)[6] else None)]
far = []
for key, (x, _, z) in LANDINGS.items():
    sx, _, sz = build.POINTS['Waystone_' + key]
    if math.dist((x, z), (sx, sz)) > 15: far.append(f'{key} {math.dist((x, z), (sx, sz)):.0f} studs from its stone')
if far: rbx.say(f'exports/{NAME}.blend: Config.Waystones lands travellers far from the stones: ' + ', '.join(far))
if not any(listed) and not far:
    rbx.say(f'exports/{NAME}.blend: every map part, monster and marker is inside Config.WorldBounds and a zone, '
            'no landmark is in an unsafe zone, and each Waystone lands travellers by its stone')


def at(area, x, y, z): return bl(*layout.moved((x, y, z), area))   # a point as laid out with `area`, where it stands


def around(group):
    """The box round a map group's part centres, Roblox (x0, x1, z0, z1)."""
    xs, zs = zip(*(where for g, kind, _, where in SPOTS if g == group and kind == 'part'))
    return min(xs), max(xs), min(zs), max(zs)


if rbx.PREVIEW:
    rbx.shot(NAME, bl(260, 900, 520), bl(-150, 0, -330), lens=24, resolution=(1800, 1100))
    rbx.shot(f'{NAME}_academy_road', bl(85, 40, 150), bl(85, 0, -330), lens=30, resolution=(1800, 900))
    rbx.shot(f'{NAME}_forest_path', bl(110, 40, 30), bl(-330, 0, 18), lens=30, resolution=(1800, 900))
    road = layout.FOREST_ROAD   # from above the fork by the gate, down the forest road to Tobb and the forest
    (ex, ez), (tx, tz) = road.at(-25), road.at(road.length + 40)
    rbx.shot(f'{NAME}_forest_road', bl(ex, 55, ez), bl(tx, 0, tz), lens=30, resolution=(1800, 900))
    rbx.shot(f'{NAME}_village', bl(30, 70, 250), bl(88, 4, 140), lens=30)
    rbx.shot(f'{NAME}_academy', at('Academy', 85, 60, 30), at('Academy', 60, 25, -250), lens=28)
    rbx.shot(f'{NAME}_yard', at('Academy', 140, 25, 45), at('Academy', 170, 2, -4), lens=30)
    rbx.shot(f'{NAME}_showcase', bl(95, 8, 158), bl(95, 3, 184), lens=26, resolution=(1800, 900))
    rbx.shot(f'{NAME}_wands', bl(80, 9, 189), bl(67, 2.5, 189), lens=38, resolution=(1600, 900))
    rbx.shot(f'{NAME}_monsters', at('Forest', -58, 9, 48), at('Forest', -80, 2, 18), lens=34, resolution=(1600, 900))
    rbx.shot(f'{NAME}_boss', at('Forest', -138, 16, -158), at('Forest', -160, 4, -183), lens=34, resolution=(1600, 900))
    for name in layout.GROUNDS:   # each Castle Grounds landmark from above its south-east corner
        x0, x1, z0, z1 = around(name); span = max(x1 - x0, z1 - z0)
        rbx.shot(f'{NAME}_{re.sub(r"[^a-z]+", "_", name.lower())}', bl(x1 + span * 0.3, 12 + span * 0.45, z1 + span * 0.5),
                 bl((x0 + x1) / 2, 2, (z0 + z1) / 2), lens=30)
    # Pictures in EEVEE, misty, with the sun low behind the camera's shoulder.
    mist_room.hide_render = False
    rbx.beauty(f'{NAME}_vista_academy', bl(85, 55, 262), bl(85, 40, -520), lens=28)
    rbx.beauty(f'{NAME}_vista_west', bl(120, 42, 60), bl(-620, 70, -60), lens=30, sun=(22, 125))
    rbx.beauty(f'{NAME}_vista_aerial', bl(520, 420, 640), bl(100, 0, 30), lens=26, resolution=(1920, 1200))
    rbx.beauty(f'{NAME}_vista_ruins', bl(-105, 34, 34), bl(60, 12, -210), lens=28)
    rbx.beauty(f'{NAME}_vista_pitch', bl(330, 70, 70), bl(150, 6, -70), lens=28, sun=(22, 125))
    mist_room.hide_render = collection('Scenery', game).hide_render = True   # the zones map shows Config over the map
    # Last, straight down without perspective or shadows: Config's zones and world bounds over the whole map, north up.
    zones.hide_render = False
    x0, x1 = min(BOUNDS[0], layout.MEADOW[0]) - 20, max(BOUNDS[1], layout.MEADOW[1]) + 20
    z0, z1 = min(BOUNDS[2], layout.MEADOW[2]) - 20, max(BOUNDS[3], layout.MEADOW[3]) + 20
    rbx.shot(f'{NAME}_zones', bl((x0 + x1) / 2, 1500, (z0 + z1) / 2 + 0.01), bl((x0 + x1) / 2, 0, (z0 + z1) / 2),
             resolution=(round(1800 * (x1 - x0) / (z1 - z0)), 1800), ortho=max(x1 - x0, z1 - z0), shadows=False)
