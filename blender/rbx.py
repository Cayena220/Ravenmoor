"""Helpers for Blender scripts that build Roblox meshes, rigs and animations.

Run scripts through tools/blender.py, which starts Blender in the background with this folder and tools/ on
the import path, so a script can `import rbx` and `from palette import *`. One Blender unit is one stud. Z is
up and a model's front faces -Y, which is Blender's Front view. Export settings follow Roblox's Blender guide
(create.roblox.com/docs/art/blender): FBX Unit Scale, Y up, no leaf bones and embedded media.

Colour comes from per-face vertex colours, so a model needs no textures or UVs. Each Mesh becomes one
MeshPart, with one material, at most 20,000 triangles and at most 4 bones moving any vertex.
"""
import math
import sys
from pathlib import Path
import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

EXPORTS = Path(__file__).resolve().parent / 'exports'
MAX_TRIANGLES = 20000; MAX_INFLUENCES = 4; FPS = 30
_args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PREVIEW = '--preview' in _args
_scene_name = 'Untitled'


def say(message): print('[rbx] ' + message, flush=True)


def scene(name, frames=(0, 0)):
    """Clear the startup scene. `frames` is the animation's first and last frame, at 30 fps."""
    global _scene_name
    _scene_name = name
    for block in (bpy.data.objects, bpy.data.meshes, bpy.data.armatures, bpy.data.materials, bpy.data.cameras,
                  bpy.data.lights, bpy.data.actions, bpy.data.curves):
        for item in list(block): block.remove(item)
    sc = bpy.context.scene
    sc.unit_settings.system = 'NONE'
    sc.render.fps = FPS; sc.frame_start, sc.frame_end = frames
    return sc


def _matrix(at, turn=(0, 0, 0), scale=(1, 1, 1)):
    """Place, then turn (degrees about X, Y, Z), then scale."""
    return Matrix.Translation(at) @ Euler([math.radians(a) for a in turn]).to_matrix().to_4x4() @ Matrix.Diagonal((*scale, 1))


class Mesh:
    """One Roblox MeshPart. Every piece added shares one mesh, one material and one vertex-colour layer.
    A piece given a `bone` is moved entirely by that bone of the Rig passed to finish(). `frame` places every
    piece added after it is set, so a building can be modelled around its own centre and then set on the map."""

    def __init__(self, name, frame=None):
        self.name = name; self.bones = []
        self.frame = frame or Matrix.Identity(4)
        self.bm = bmesh.new()
        self.colour = self.bm.loops.layers.color.new('Col')
        self.deform = self.bm.verts.layers.deform.verify()

    def _paint(self, faces, colour, bone):
        rgba = (*(c / 255 for c in colour), 1.0)
        for face in faces:
            for loop in face.loops: loop[self.colour] = rgba
        bmesh.ops.recalc_face_normals(self.bm, faces=faces)
        if bone:
            if bone not in self.bones: self.bones.append(bone)
            group = self.bones.index(bone)
            for v in {v for f in faces for v in f.verts}: v[self.deform][group] = 1.0
        return faces

    def _made(self, result, colour, bone):
        return self._paint(list({f for v in result['verts'] for f in v.link_faces}), colour, bone)

    def box(self, size, at, colour, turn=(0, 0, 0), bone=None):
        return self.block(_matrix(at, turn, size), colour, bone)

    def block(self, matrix, colour, bone=None):
        """A unit cube through `matrix`, whose first three columns are the box's edges and the fourth its centre."""
        return self._made(bmesh.ops.create_cube(self.bm, size=1, matrix=self.frame @ matrix), colour, bone)

    def cylinder(self, radius, height, at, colour, top=None, turn=(0, 0, 0), segments=16, bone=None):
        """Upright along Z; `top` tapers the upper end to another radius."""
        made = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=segments, radius1=radius,
                                     radius2=radius if top is None else top, depth=height,
                                     matrix=self.frame @ _matrix(at, turn))
        return self._made(made, colour, bone)

    def sphere(self, radius, at, colour, segments=12, scale=(1, 1, 1), bone=None):
        made = bmesh.ops.create_uvsphere(self.bm, u_segments=segments, v_segments=max(3, segments // 2), radius=radius,
                                         matrix=self.frame @ _matrix(at, scale=scale))
        return self._made(made, colour, bone)

    def prism(self, outline, depth, at, colour, turn=(0, 0, 0), bone=None):
        """Extrude an outline of (x, z) points `depth` studs along Y, centred on `at`. Any simple outline works."""
        m = self.frame @ _matrix(at, turn); n = len(outline)
        front = [self.bm.verts.new(m @ Vector((x, -depth / 2, z))) for x, z in outline]
        back = [self.bm.verts.new(m @ Vector((x, depth / 2, z))) for x, z in outline]
        faces = [self.bm.faces.new(front), self.bm.faces.new(back[::-1])]
        faces += [self.bm.faces.new((front[i], back[i], back[(i + 1) % n], front[(i + 1) % n])) for i in range(n)]
        return self._paint(faces, colour, bone)

    def loft(self, sections, colour, at=(0, 0, 0), colours=None, bone=None):
        """Skin outlines of (x, z) points set along Y: `sections` lists (y, outline), every outline the same length.
        Both ends are capped. `colours` gives each outline edge its own colour, for planking or trim."""
        m = self.frame @ _matrix(at)
        rings = [[self.bm.verts.new(m @ Vector((x, y, z))) for x, z in outline] for y, outline in sections]
        n, faces = len(rings[0]), []
        for edge in range(n):
            band = [self.bm.faces.new((lo[edge], lo[(edge + 1) % n], hi[(edge + 1) % n], hi[edge]))
                    for lo, hi in zip(rings, rings[1:])]
            faces += self._paint(band, colours[edge] if colours else colour, bone)
        faces += self._paint([self.bm.faces.new(rings[0]), self.bm.faces.new(rings[-1][::-1])], colour, bone)
        bmesh.ops.recalc_face_normals(self.bm, faces=faces)
        return faces

    def text(self, body, at, colour, height, width=None, depth=0.05, turn=(0, 0, 0), bone=None):
        """Raised lettering facing -Y and centred on `at`: `height` studs tall, or smaller to fit `width`."""
        curve = bpy.data.curves.new('Lettering', 'FONT')
        curve.body, curve.align_x, curve.align_y, curve.extrude, curve.resolution_u = body, 'CENTER', 'CENTER', 0.5, 3
        obj = bpy.data.objects.new('Lettering', curve); bpy.context.scene.collection.objects.link(obj)
        evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = evaluated.to_mesh()
        xs, ys = [v.co.x for v in me.vertices], [v.co.y for v in me.vertices]
        scale = height / (max(ys) - min(ys))
        if width: scale = min(scale, width / (max(xs) - min(xs)))
        cx, cy, m = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, self.frame @ _matrix(at, turn)
        # The font lies in XY facing +Z; stand it up in XZ facing -Y.
        verts = [self.bm.verts.new(m @ Vector(((v.co.x - cx) * scale, -v.co.z * depth, (v.co.y - cy) * scale)))
                 for v in me.vertices]
        faces = [self.bm.faces.new([verts[i] for i in p.vertices]) for p in me.polygons]
        evaluated.to_mesh_clear(); bpy.data.objects.remove(obj); bpy.data.curves.remove(curve)
        return self._paint(faces, colour, bone)

    def lathe(self, profile, colour, at=(0, 0, 0), segments=32, bone=None):
        """Spin (radius, height) points around the Z axis. Start and end on the axis (radius 0) for a closed solid."""
        bm, (ox, oy, oz), f = self.bm, at, self.frame
        angles = [2 * math.pi * i / segments for i in range(segments)]
        rings = [[bm.verts.new(f @ Vector((ox, oy, oz + z)))] if r < 1e-6 else
                 [bm.verts.new(f @ Vector((ox + r * math.cos(a), oy + r * math.sin(a), oz + z))) for a in angles]
                 for r, z in profile]
        faces = []
        for lo, hi in zip(rings, rings[1:]):
            for i in range(segments):
                j = (i + 1) % segments
                # A pole repeats one vertex, which turns that quad into a triangle.
                corners = dict.fromkeys((lo[i % len(lo)], lo[j % len(lo)], hi[j % len(hi)], hi[i % len(hi)]))
                faces.append(bm.faces.new(list(corners)))
        return self._paint(faces, colour, bone)

    def torus(self, radius, thickness, at, colour, turn=(0, 0, 0), segments=24, sides=8, arc=360, bone=None):
        """A ring lying in the XY plane before `turn`, starting on +X. An `arc` under 360 degrees is a capped bend."""
        m, closed = self.frame @ _matrix(at, turn), arc >= 360
        rings = segments if closed else segments + 1
        grid = [[self.bm.verts.new(m @ Vector(((radius + thickness * math.cos(v)) * math.cos(u),
                                               (radius + thickness * math.cos(v)) * math.sin(u), thickness * math.sin(v))))
                 for v in (2 * math.pi * k / sides for k in range(sides))]
                for u in (math.radians(arc) * i / segments for i in range(rings))]
        faces = [self.bm.faces.new((grid[i][k], grid[(i + 1) % rings][k], grid[(i + 1) % rings][(k + 1) % sides],
                                    grid[i][(k + 1) % sides])) for i in range(segments) for k in range(sides)]
        if not closed: faces += [self.bm.faces.new(grid[0][::-1]), self.bm.faces.new(grid[-1])]
        return self._paint(faces, colour, bone)

    def finish(self, sharp=30, rig=None):
        """Make the Blender object, or return None if nothing was added. Edges sharper than `sharp` degrees stay
        hard; the rest shade smooth."""
        if not self.bm.faces: self.bm.free(); return None
        me = bpy.data.meshes.new(self.name); self.bm.to_mesh(me); self.bm.free()
        obj = bpy.data.objects.new(self.name, me); bpy.context.scene.collection.objects.link(obj)
        me.shade_smooth(); me.set_sharp_from_angle(angle=math.radians(sharp))
        me.color_attributes.active_color_name = me.color_attributes.default_color_name = 'Col'
        me.materials.append(_material(self.name))
        for bone in self.bones: obj.vertex_groups.new(name=bone)
        if rig:
            missing = set(self.bones) - set(rig.obj.data.bones.keys())
            assert not missing, f'{self.name} uses bones the rig lacks: {sorted(missing)}'
            obj.parent = rig.obj; obj.modifiers.new('Armature', 'ARMATURE').object = rig.obj
        return obj


def _material(name):
    """A white material that shows the vertex colours in Blender. Roblox takes the colours from the mesh."""
    mat = bpy.data.materials.new(name)
    if not mat.node_tree: mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is None:
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        links.new(bsdf.outputs['BSDF'], nodes.new('ShaderNodeOutputMaterial').inputs['Surface'])
    bsdf.inputs['Base Color'].default_value = (1, 1, 1, 1); bsdf.inputs['Roughness'].default_value = 0.8
    tint = nodes.new('ShaderNodeVertexColor'); tint.layer_name = 'Col'
    links.new(tint.outputs['Color'], bsdf.inputs['Base Color'])
    return mat


def group(name, children):
    """An empty holding `children` (objects or None). Studio's importer makes it a Model of that name."""
    empty = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(empty)
    for child in children:
        if child: child.parent = empty
    return empty


class Rig:
    """An armature. `bones` lists (name, parent, head, tail). A bone's Y axis runs from head to tail; a bone laid
    along +Y has its X, Y and Z axes along the world's, which keeps key() values easy to read."""

    def __init__(self, name, bones):
        arm = bpy.data.armatures.new(name)
        self.obj = bpy.data.objects.new(name, arm); bpy.context.scene.collection.objects.link(self.obj)
        bpy.context.view_layer.objects.active = self.obj
        bpy.ops.object.mode_set(mode='EDIT')
        for bone, parent, head, tail in bones:
            b = arm.edit_bones.new(bone); b.head, b.tail = head, tail
            if parent: b.parent = arm.edit_bones[parent]
        bpy.ops.object.mode_set(mode='OBJECT')
        for pb in self.obj.pose.bones: pb.rotation_mode = 'XYZ'

    def key(self, frame, bone, move=None, turn=None):
        """Key `bone` at `frame`: `move` in studs and `turn` in degrees, both along the bone's own axes."""
        pb = self.obj.pose.bones[bone]
        if move is not None: pb.location = move; pb.keyframe_insert('location', frame=frame)
        if turn is not None:
            pb.rotation_euler = [math.radians(a) for a in turn]; pb.keyframe_insert('rotation_euler', frame=frame)


def _check(obj):
    me = obj.data; me.calc_loop_triangles(); tris = len(me.loop_triangles)
    assert tris <= MAX_TRIANGLES, f'{obj.name} has {tris:,} triangles; Roblox allows {MAX_TRIANGLES:,} per mesh'
    assert len(me.materials) <= 1, f'{obj.name} has {len(me.materials)} materials; Roblox uses one per mesh'
    assert len(me.uv_layers) <= 1, f'{obj.name} has {len(me.uv_layers)} UV maps; Roblox reads one'
    worst = max((sum(g.weight > 0 for g in v.groups) for v in me.vertices), default=0)
    assert worst <= MAX_INFLUENCES, f'{obj.name} has a vertex moved by {worst} bones; Roblox allows {MAX_INFLUENCES}'
    return tris


def export(name, objects, animation=False, preview_frames=None, auto_preview=True):
    """Check Roblox's limits, then write exports/<name>.fbx and save the scene as exports/<scene>.blend.
    A model exports in its rest pose (the first frame). `animation=True` bakes the rig's keys into the file.
    With --preview, also render exports/<name>.png: a still, or a strip of frames for an animation. Pass
    auto_preview=False when the script frames its own shots instead."""
    EXPORTS.mkdir(exist_ok=True)
    sc = bpy.context.scene; sc.frame_set(sc.frame_start)
    meshes = [o for o in objects if o.type == 'MESH']; rigs = [o for o in objects if o.type == 'ARMATURE']
    counts = [_check(o) for o in meshes]; tris = sum(counts)
    for o in bpy.context.view_layer.objects: o.select_set(o in objects)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.fbx(
        filepath=str(EXPORTS / f'{name}.fbx'), use_selection=True, object_types={'MESH', 'ARMATURE', 'EMPTY'},
        global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS', axis_forward='Z', axis_up='Y',
        use_mesh_modifiers=True, use_triangles=True, colors_type='SRGB', add_leaf_bones=False,
        bake_anim=animation, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=False, bake_anim_force_startend_keying=False, bake_anim_step=1.0,
        bake_anim_simplify_factor=0.0, path_mode='COPY', embed_textures=True)
    bones = sum(len(r.data.bones) for r in rigs)
    detail = f'{len(meshes)} mesh, {tris:,} triangles' if len(meshes) == 1 else \
        f'{len(meshes)} meshes, {tris:,} triangles (largest {max(counts):,})'
    detail += f', {bones} bones' if bones else ''
    if animation:
        count = sc.frame_end - sc.frame_start + 1
        detail += f', {count} frames ({(count - 1) / FPS:.1f} s at {FPS} fps)'
    say(f'exports/{name}.fbx: {detail}')
    bpy.context.preferences.filepaths.save_version = 0   # no .blend1 backups beside the export
    bpy.ops.wm.save_as_mainfile(filepath=str(EXPORTS / f'{_scene_name}.blend'), check_existing=False)
    if PREVIEW and auto_preview:
        if preview_frames is None:
            preview_frames = [sc.frame_start + round(k * (sc.frame_end - sc.frame_start) / 4) for k in range(4)] \
                if animation else [sc.frame_start]
        preview(name, meshes, preview_frames)
        sc.frame_set(sc.frame_start)


def preview(name, meshes, frames):
    """Render exports/<name>.png from the front right, framed around the meshes across `frames`."""
    import numpy as np
    sc = bpy.context.scene; pts = []
    for f in frames:
        sc.frame_set(f); depsgraph = bpy.context.evaluated_depsgraph_get()
        for o in meshes:
            e = o.evaluated_get(depsgraph); pts += [e.matrix_world @ Vector(c) for c in e.bound_box]
    lo, hi = Vector(map(min, zip(*pts))), Vector(map(max, zip(*pts)))
    centre, radius = (lo + hi) / 2, max((hi - lo).length / 2, 0.5)
    view = Vector((0.7, -1.0, 0.65)).normalized()   # from the front right and above; the front faces -Y
    _camera(centre + view * radius * 3.0, centre)   # 3 radii fits the bounding sphere in a 50 mm lens
    _look((640, 640) if len(frames) == 1 else (480, 480))
    out = EXPORTS / f'{name}.png'; shots = []
    try:
        for f in frames:
            sc.frame_set(f); sc.render.filepath = str(out if len(frames) == 1 else EXPORTS / f'{name}_{f}.png')
            bpy.ops.render.render(write_still=True); shots.append(Path(sc.render.filepath))
    except RuntimeError as error:
        say(f'Preview skipped for {name}: {error}'); return
    if len(shots) > 1:
        # Put the frames side by side in one image, left to right.
        strips = []
        for shot in shots:
            image = bpy.data.images.load(str(shot)); w, h = image.size
            pixels = np.empty(w * h * 4, np.float32); image.pixels.foreach_get(pixels)
            strips.append(pixels.reshape(h, w, 4)); bpy.data.images.remove(image); shot.unlink()
        sheet = np.concatenate(strips, axis=1); h, w = sheet.shape[:2]
        image = bpy.data.images.new(name, w, h); image.pixels.foreach_set(sheet.ravel())
        image.filepath_raw = str(out); image.file_format = 'PNG'; image.save(); bpy.data.images.remove(image)
    say(f'exports/{name}.png: preview' + (f' of frames {", ".join(map(str, frames))}' if len(frames) > 1 else ''))


def shot(name, eye, target, lens=35, resolution=(1600, 900), ortho=0, shadows=True):
    """With --preview, render exports/<name>.png from `eye` looking at `target`, in Blender coordinates. Given
    `ortho`, the view is orthographic, `ortho` units across its longer side. shadows=False leaves out the light's
    shadows."""
    if not PREVIEW: return
    _camera(eye, target, lens, ortho); _look(resolution, shadows)
    sc = bpy.context.scene; sc.render.filepath = str(EXPORTS / f'{name}.png')
    try: bpy.ops.render.render(write_still=True)
    except RuntimeError as error: say(f'Preview skipped for {name}: {error}'); return
    say(f'exports/{name}.png: preview')


def beauty(name, eye, target, lens=35, resolution=(1920, 1080), sun=(18, 230)):
    """With --preview, render exports/<name>.png in EEVEE, as a picture rather than a check: daylight from a sun
    `sun` = (elevation, heading) degrees, the heading clockwise from north (-Y) through east (-X) as Roblox has
    them, and a sky to match. Haze or mist are volume objects in the scene: EEVEE takes a world volume to be
    endless, and it would swallow the sun. Workbench previews from shot() stay as they are."""
    if not PREVIEW: return
    sc = bpy.context.scene
    _camera(eye, target, lens)
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = resolution
    sc.render.image_settings.file_format = 'PNG'
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.eevee.volumetric_end = max(2000.0, (Vector(target) - Vector(eye)).length * 6)
    elevation, heading = (math.radians(a) for a in sun)
    to_sun = Vector((-math.sin(heading) * math.cos(elevation), -math.cos(heading) * math.cos(elevation), math.sin(elevation)))
    lamp = bpy.data.objects.get('Beauty sun')
    if lamp is None:
        lamp = bpy.data.objects.new('Beauty sun', bpy.data.lights.new('Beauty sun', 'SUN')); sc.collection.objects.link(lamp)
    lamp.data.energy, lamp.data.angle, lamp.data.color = 6.5, math.radians(2), (1.0, 0.84, 0.66)
    lamp.rotation_euler = (-to_sun).to_track_quat('-Z', 'Y').to_euler()
    sc.world = _daylight(elevation, math.pi - heading)   # the sky turns its sun from south (+Y) through east
    sc.render.filepath = str(EXPORTS / f'{name}.png')
    try: bpy.ops.render.render(write_still=True)
    except RuntimeError as error: say(f'Picture skipped for {name}: {error}'); return
    say(f'exports/{name}.png: picture')


def _daylight(elevation, rotation):
    """A world of open sky with its sun at `elevation` and `rotation` (radians)."""
    world = bpy.data.worlds.get('Daylight') or bpy.data.worlds.new('Daylight')
    if not world.node_tree: world.use_nodes = True
    nodes, links = world.node_tree.nodes, world.node_tree.links
    nodes.clear()
    sky, back, out = nodes.new('ShaderNodeTexSky'), nodes.new('ShaderNodeBackground'), nodes.new('ShaderNodeOutputWorld')
    sky.sky_type = 'MULTIPLE_SCATTERING'
    sky.sun_elevation, sky.sun_rotation, sky.sun_disc = elevation, rotation, False
    back.inputs['Strength'].default_value = 0.28
    links.new(sky.outputs['Color'], back.inputs['Color']); links.new(back.outputs['Background'], out.inputs['Surface'])
    return world


def viewport(target, distance, turn=(55, 0, 0)):
    """Aim the 3D views of the saved .blend at `target` from `distance` studs (Euler `turn` in degrees), in Solid
    shading with vertex colours, so the model is in view and in colour when the file is opened in Blender."""
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type != 'VIEW_3D': continue
            space = area.spaces.active
            space.shading.color_type = 'VERTEX'; space.clip_end = max(space.clip_end, distance * 20)
            view = space.region_3d
            if view is None: continue
            view.view_location, view.view_distance = target, distance
            view.view_rotation = Euler([math.radians(a) for a in turn]).to_quaternion()


def _camera(eye, target, lens=50, ortho=0):
    sc = bpy.context.scene
    cam = sc.camera or bpy.data.objects.new('PreviewCamera', bpy.data.cameras.new('PreviewCamera'))
    if not sc.camera: sc.collection.objects.link(cam); sc.camera = cam
    eye, target = Vector(eye), Vector(target)
    cam.data.lens, cam.data.clip_end = lens, max(1000, (target - eye).length * 10)
    cam.data.type = 'ORTHO' if ortho else 'PERSP'
    if ortho: cam.data.ortho_scale = ortho
    cam.location, cam.rotation_euler = eye, (target - eye).to_track_quat('-Z', 'Y').to_euler()


def _look(resolution, shadows=True):
    sc = bpy.context.scene
    sc.world = sc.world or bpy.data.worlds.new('Preview'); sc.world.color = (0.32, 0.34, 0.37)
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.view_settings.view_transform = 'Standard'
    shading = sc.display.shading
    shading.light, shading.color_type, shading.show_shadows, shading.show_cavity = 'STUDIO', 'VERTEX', shadows, True
    sc.render.resolution_x, sc.render.resolution_y = resolution
    sc.render.image_settings.file_format = 'PNG'
