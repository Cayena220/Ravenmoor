"""Replace known generated grass blades with textured, instanced crossed cards.

Called by optimize_worldplan.py inside Blender; this module never saves a scene.
The original point locations are recovered from the generator's verified topology.
No particles, random re-scattering, or Realize Instances node is used in the source.
"""
from pathlib import Path
import math

import bpy
import numpy as np


VERSION = 1
PROTOTYPE = 'OPT | Grass crossed card prototype'
GROUP = 'OPT | Instanced grass cards'
SOURCE_COLLECTION = 'Optimization | Grass card sources'
MATERIAL = 'OPT | Meadow grass cards'


def _image(name, path, rgba, data=False):
    image = bpy.data.images.new(name, width=rgba.shape[1], height=rgba.shape[0], alpha=True)
    image.colorspace_settings.name = 'Non-Color' if data else 'sRGB'
    image.alpha_mode = 'STRAIGHT'
    image.pixels.foreach_set(np.asarray(rgba, dtype=np.float32).ravel())
    image.file_format = 'PNG'
    image.filepath_raw = str(path)
    image.save()
    image.pack()
    image['wp_optimization_asset'] = VERSION
    return image


def _grass_maps(output_dir):
    """A small original five-blade cutout; transparent margins carry green RGB."""
    output_dir.mkdir(parents=True, exist_ok=True)
    size = 512
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    x = (x + .5) / size
    y = (y + .5) / size
    color = np.zeros((size, size, 4), dtype=np.float32)
    color[:, :, :3] = (.37, .47, .19)
    normal = np.ones((size, size, 4), dtype=np.float32)
    normal[:, :, :2] = .5
    rough = np.ones((size, size, 4), dtype=np.float32)
    rough[:, :, :3] = .78
    # base X, tip X, height, width, colour variation
    blades = [(.27, .08, .66, .023, .90), (.40, .25, .89, .031, 1.06),
              (.50, .58, .98, .034, .96), (.59, .80, .81, .027, 1.12),
              (.72, .94, .61, .025, .87)]
    for base_x, tip_x, height, width, tint in blades:
        t = np.clip(y / height, 0, 1)
        center = base_x + (tip_x-base_x) * t * t
        half_width = width * np.power(np.maximum(1-t, 0), .65)
        distance = np.abs(x-center)
        alpha = np.clip((half_width-distance)*size+.5, 0, 1)
        alpha *= np.clip((height-y)*size+.5, 0, 1)
        u = np.clip((x-center)/np.maximum(half_width, 1e-6), -1, 1)
        # A narrow light ridge and mild longitudinal fibre variation.
        ridge = .92 + .16*np.exp(-u*u*45) - .12*np.abs(u)
        light = (.79+.23*t) * ridge * tint
        blade_color = np.stack((.39*light, .50*light, .19*light), axis=-1)
        use = alpha > color[:, :, 3]
        color[:, :, :3][use] = blade_color[use]
        color[:, :, 3] = np.maximum(color[:, :, 3], alpha)
        nx = .30*np.sin(u*math.pi*.5)
        ny = np.full_like(nx, -.06)
        nz = np.sqrt(1-nx*nx-ny*ny)
        blade_normal = np.stack((nx*.5+.5, ny*.5+.5, nz*.5+.5), axis=-1)
        normal[:, :, :3][use] = blade_normal[use]
    # Normal/roughness are opaque data maps; color alone supplies cutout alpha.
    return {
        'color': _image('OPT_GrassCards_Color', output_dir/'GrassCards_Color.png', color),
        'normal': _image('OPT_GrassCards_Normal', output_dir/'GrassCards_Normal.png', normal, True),
    }


def _material(images):
    material = bpy.data.materials.new(MATERIAL)
    material.use_nodes = True
    material.diffuse_color = (.105, .17, .036, 1)
    material.use_backface_culling = False
    if hasattr(material, 'surface_render_method'):
        material.surface_render_method = 'DITHERED'
    material['wp_grass_cards'] = True
    material['export_alpha_mode'] = 'Mask / cutout; double-sided'
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial'); out.location = (550, 0)
    p = nodes.new('ShaderNodeBsdfPrincipled'); p.location = (280, 0)
    p.inputs['Roughness'].default_value = .78
    p.inputs['Metallic'].default_value = 0
    p.inputs['Specular IOR Level'].default_value = .23
    color = nodes.new('ShaderNodeTexImage'); color.image = images['color']; color.location = (-300, 160)
    color.extension = 'EXTEND'
    normal = nodes.new('ShaderNodeTexImage'); normal.image = images['normal']; normal.location = (-300, -170)
    normal.extension = 'EXTEND'
    n = nodes.new('ShaderNodeNormalMap'); n.location = (0, -140)
    n.inputs['Strength'].default_value = .6
    links.new(color.outputs['Color'], p.inputs['Base Color'])
    links.new(color.outputs['Alpha'], p.inputs['Alpha'])
    links.new(normal.outputs['Color'], n.inputs['Color'])
    links.new(n.outputs['Normal'], p.inputs['Normal'])
    links.new(p.outputs['BSDF'], out.inputs['Surface'])
    return material


def _prototype(material, scenes):
    collection = bpy.data.collections.new(SOURCE_COLLECTION)
    collection.hide_render = True
    for scene in scenes:
        scene.collection.children.link(collection)
    mesh = bpy.data.meshes.new(PROTOTYPE)
    mesh.from_pydata([(-.5, 0, 0), (.5, 0, 0), (.5, 0, 1), (-.5, 0, 1),
                     (0, -.5, 0), (0, .5, 0), (0, .5, 1), (0, -.5, 1)],
                    [], [(0, 1, 2, 3), (4, 5, 6, 7)])
    mesh.materials.append(material)
    uv = mesh.uv_layers.new(name='UVMap')
    uv.data.foreach_set('uv', [0, 0, 1, 0, 1, 1, 0, 1]*2)
    mesh.update()
    obj = bpy.data.objects.new(PROTOTYPE, mesh)
    collection.objects.link(obj)
    obj.hide_render = True
    obj.hide_set(True)
    obj['wp_grass_card_prototype'] = True
    obj['triangles'] = 4
    return obj


def _node_group(prototype):
    group = bpy.data.node_groups.new(GROUP, 'GeometryNodeTree')
    group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    inp = group.nodes.new('NodeGroupInput'); inp.location = (-500, 150)
    out = group.nodes.new('NodeGroupOutput'); out.location = (300, 150)
    info = group.nodes.new('GeometryNodeObjectInfo'); info.location = (-500, -60)
    info.transform_space = 'ORIGINAL'
    info.inputs['Object'].default_value = prototype
    info.inputs['As Instance'].default_value = True
    scale = group.nodes.new('GeometryNodeInputNamedAttribute'); scale.location = (-260, -260)
    scale.data_type = 'FLOAT_VECTOR'; scale.inputs['Name'].default_value = 'card_scale'
    rotation = group.nodes.new('GeometryNodeInputNamedAttribute'); rotation.location = (-500, -300)
    rotation.data_type = 'FLOAT_VECTOR'; rotation.inputs['Name'].default_value = 'card_rotation'
    instances = group.nodes.new('GeometryNodeInstanceOnPoints'); instances.location = (0, 150)
    group.links.new(inp.outputs['Geometry'], instances.inputs['Points'])
    group.links.new(info.outputs['Geometry'], instances.inputs['Instance'])
    group.links.new(scale.outputs['Attribute'], instances.inputs['Scale'])
    group.links.new(rotation.outputs['Attribute'], instances.inputs['Rotation'])
    group.links.new(instances.outputs['Instances'], out.inputs['Geometry'])
    group['wp_optimization_version'] = VERSION
    return group


def _recover_tufts(obj, kind):
    """Validate exact known blade connectivity before interpreting vertex order."""
    mesh = obj.data
    per_blade, blades, faces_per_blade = (5, 5, 2) if kind == 'meadow' else (3, 4, 1)
    count = len(mesh.vertices)
    if count % (per_blade*blades) or len(mesh.polygons) != count//per_blade*faces_per_blade:
        raise ValueError(f'{obj.name}: expected generated {kind} blade topology; left untouched')
    sizes = np.empty(len(mesh.polygons), dtype=np.int32)
    mesh.polygons.foreach_get('loop_total', sizes)
    loops = np.empty(len(mesh.loops), dtype=np.int32)
    mesh.loops.foreach_get('vertex_index', loops)
    starts = np.arange(count//per_blade, dtype=np.int32)*per_blade
    pattern = [0, 1, 2, 3, 3, 2, 4] if kind == 'meadow' else [0, 1, 2]
    expected = (starts[:, None] + np.array(pattern, dtype=np.int32)).ravel()
    expected_sizes = np.tile([4, 3], count//per_blade) if kind == 'meadow' else np.full(len(sizes), 3)
    if not np.array_equal(loops, expected) or not np.array_equal(sizes, expected_sizes):
        raise ValueError(f'{obj.name}: blade connectivity changed; left untouched')
    coords = np.empty(count*3, dtype=np.float32)
    mesh.vertices.foreach_get('co', coords)
    coords = coords.reshape((-1, blades, per_blade, 3))
    # A tuft must still share one planted base height. Protect edited geometry.
    bases = coords[:, :, :2, :]
    if np.max(np.ptp(bases[:, :, :, 2].reshape((-1, blades*2)), axis=1)) > .002:
        raise ValueError(f'{obj.name}: blades no longer have a shared planted base')
    lo = coords.min(axis=(1, 2)); hi = coords.max(axis=(1, 2))
    points = (lo+hi)*.5
    points[:, 2] = bases[:, :, :, 2].mean(axis=(1, 2))
    extent = np.maximum(hi[:, 0]-lo[:, 0], hi[:, 1]-lo[:, 1])
    # Visible mask spans 86% of texture width; compensate for transparent margins.
    width = np.maximum(extent/.86, .45)
    scale = np.column_stack((width, width, hi[:, 2]-points[:, 2]))
    rotations = np.zeros_like(points)
    rotations[:, 2] = (np.arange(len(points))*2.399963229728653) % math.tau
    return points, scale, rotations


def optimize_grass(output_dir):
    """Replace supported grass-only meshes, returning serializable audit statistics.

    Unsupported or edited topology is reported and left unchanged. Existing card
    emitters are skipped, so applying this module twice never doubles planting.
    """
    report = {'version': VERSION, 'converted': [], 'skipped': [], 'textures': [],
              'method': 'Geometry Nodes instances; two crossed cards per planted tuft',
              'particle_systems_added': 0}
    candidates = []
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        if obj.get('wp_grass_cards'):
            report['skipped'].append({'name': obj.name, 'reason': 'already optimized'})
            continue
        kind = ('meadow' if 'Individual mixed meadow grass blades' in obj.name else
                'formal' if 'Fine grass around the formal gardens' in obj.name else None)
        if kind:
            if obj.modifiers or obj.data.shape_keys:
                report['skipped'].append({'name': obj.name, 'reason': 'modifiers or shape keys require manual review'})
                continue
            try:
                candidates.append((obj, _recover_tufts(obj, kind)))
            except ValueError as exc:
                report['skipped'].append({'name': obj.name, 'reason': str(exc)})
    if not candidates:
        return report
    textures = Path(output_dir)/'textures'
    images = _grass_maps(textures)
    report['textures'] = [{'name': im.name, 'path': im.filepath, 'size': list(im.size), 'packed': bool(im.packed_file)} for im in images.values()]
    material = _material(images)
    scenes = [s for s in bpy.data.scenes if any(o.name in s.objects for o, _ in candidates)]
    prototype = _prototype(material, scenes)
    nodes = _node_group(prototype)
    report['prototype'] = prototype.name
    for obj, (points, scales, rotations) in candidates:
        old = obj.data
        triangles_before = sum(len(p.vertices)-2 for p in old.polygons)
        mesh = bpy.data.meshes.new(obj.name+' | planted tuft points')
        mesh.vertices.add(len(points)); mesh.vertices.foreach_set('co', points.ravel())
        mesh.attributes.new('card_scale', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', scales.ravel())
        mesh.attributes.new('card_rotation', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', rotations.ravel())
        mesh.update()
        obj.data = mesh
        modifier = obj.modifiers.new('Shared grass card instances', 'NODES'); modifier.node_group = nodes
        obj['wp_grass_cards'] = True
        obj['wp_grass_optimization_version'] = VERSION
        obj['wp_grass_tuft_count'] = len(points)
        obj['wp_grass_source_triangles'] = triangles_before
        obj['wp_grass_realized_triangles'] = len(points)*4
        obj['wp_grass_export_note'] = 'Realize Instances on export only; keep double-sided alpha cutouts and UVMap.'
        report['converted'].append({'name': obj.name, 'tufts': len(points),
                                    'triangles_before': triangles_before, 'triangles_after_realization': len(points)*4,
                                    'source_vertices_before': len(old.vertices), 'source_points_after': len(points),
                                    'prototype_triangles_shared': 4,
                                    'positions': 'existing tuft footprint centers and original base heights'})
        if old.users == 0:
            bpy.data.meshes.remove(old)
    bpy.context.view_layer.update()
    return report
