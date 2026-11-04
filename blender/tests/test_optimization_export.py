"""Run in an opened optimized WorldPlan; exercise exporter helpers without export/save.

blender -b WorldPlan.optimized.blend --python-exit-code 1 --python this_file.py
Only writes WorldPlan_Optimization/export_validation.json. No FBX or blend is saved.
"""
import ast
from collections import defaultdict
import json
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix


BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'exports' / 'WorldPlan_Optimization'
tree = ast.parse((BASE / 'export_worldplan_game.py').read_text(encoding='utf-8'))
functions = {'feeders', 'shade', 'cut_of', 'realized_instance_mesh', 'mesh_arrays', 'fbx_material', 'place'}
constants = {'ROBLOX', 'CUTS', 'LETTERING', 'NIGHT'}
nodes = [node for node in tree.body
         if (isinstance(node, ast.FunctionDef) and node.name in functions)
         or (isinstance(node, ast.ClassDef) and node.name == 'Bucket')
         or (isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in constants for t in node.targets))]
scope = {'bpy': bpy, 'np': np, 'math': math, 'defaultdict': defaultdict,
         'SHADES': {}, 'materials': {}, 'PATCH': None}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(BASE / 'export_worldplan_game.py'), 'exec'), scope)
scope['buckets'] = defaultdict(scope['Bucket'])
report = json.loads((OUT / 'report.json').read_text())
results = {'ok': False, 'source': bpy.data.filepath, 'realization': [], 'materials': []}


def shader(material):
    return next(n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')


def image_at(socket, output_name=None):
    assert socket.is_linked, socket.name + ' is unlinked'
    link = socket.links[0]
    if output_name:
        assert link.from_socket.name == output_name
    assert link.from_node.type == 'TEX_IMAGE'
    return link.from_node.image


def verify_material(source):
    roblox, _, _, maps, _ = scope['shade'](source)
    key = tuple(sorted((socket, im.name) for socket, im in maps.items()))
    output = scope['fbx_material'](roblox, key)
    out = shader(output)
    assert image_at(out.inputs['Base Color'], 'Color') == maps['Base Color']
    assert maps['Normal'].colorspace_settings.name == 'Non-Color'
    normal = out.inputs['Normal'].links[0].from_node
    assert normal.type == 'NORMAL_MAP'
    assert image_at(normal.inputs['Color'], 'Color') == maps['Normal']
    if source.get('wp_grass_cards'):
        assert maps['Alpha'] == maps['Base Color']
        assert image_at(out.inputs['Alpha'], 'Alpha') == maps['Base Color']
        assert output.surface_render_method == 'DITHERED'
        original = shader(source)
        for socket in ('Roughness', 'Specular IOR Level'):
            assert out.inputs[socket].default_value == original.inputs[socket].default_value
        old_normal = next(n for n in scope['feeders'](original.inputs['Normal']) if n.type == 'NORMAL_MAP')
        assert normal.inputs['Strength'].default_value == old_normal.inputs['Strength'].default_value
    if 'Roughness' in maps:
        assert image_at(out.inputs['Roughness'], 'Color') == maps['Roughness']
    results['materials'].append({'source': source.name, 'maps': dict(key),
                                 'roughness': out.inputs['Roughness'].default_value,
                                 'normal_strength': normal.inputs['Strength'].default_value})


emitters = [o for o in bpy.data.objects if o.get('wp_grass_cards') or o.get('wp_instance_geometry')]
assert any(o.get('wp_grass_cards') for o in emitters), 'No optimized grass emitter'
assert any(o.get('wp_instance_geometry') for o in emitters), 'No optimized groundcover emitter'
original_scene = bpy.context.window.scene
for obj in emitters:
    bpy.context.window.scene = next(s for s in bpy.data.scenes if obj.name in s.objects)
    collection = bpy.data.collections.new('Export verification temporary')
    bpy.context.scene.collection.children.link(collection)
    mesh = None
    source_data, modifier_count = obj.data, len(obj.modifiers)
    object_count, group_count = len(bpy.data.objects), len(bpy.data.node_groups)
    try:
        mesh = scope['realized_instance_mesh'](obj, collection)
        v, triangles, uv, colors, material_ids, mats = scope['mesh_arrays'](mesh)
        expected = (int(obj['wp_grass_realized_triangles']) if obj.get('wp_grass_cards')
                    else report['groundcover']['realized_triangles'])
        assert len(triangles) == expected, (obj.name, len(triangles), expected)
        assert np.isfinite(v).all()
        assert obj.data == source_data and len(obj.modifiers) == modifier_count
        assert len(bpy.data.objects) == object_count and len(bpy.data.node_groups) == group_count
        if obj.get('wp_grass_cards'):
            assert len(mesh.uv_layers) == 1 and np.isfinite(uv).all()
            assert np.allclose(uv.min(axis=(0, 1)), [0, 0])
            assert np.allclose(uv.max(axis=(0, 1)), [1, 1])
            assert len(mats) == 1 and mats[0].get('wp_grass_cards')
            normals = np.array([tuple(p.normal) for p in mesh.polygons])
            assert np.allclose(np.linalg.norm(normals, axis=1), 1, atol=1e-5)
            cut = scope['cut_of'](obj, obj.name)
            assert cut[0] == 'cards' and cut[2] == 1 and cut[3] is False
            scope['place']((v, triangles, uv, colors, material_ids, mats), Matrix(), 'Verification', obj.name, cut)
            keys = list(scope['buckets'])
            assert all(k[6] is True and k[2] is False for k in keys)
            assert all('Alpha' in dict(k[4]) for k in keys)
            assert sum(bucket.tris for bucket in scope['buckets'].values()) == len(triangles)
            scope['buckets'].clear()
        results['realization'].append({'object': obj.name, 'triangles': len(triangles),
                                       'uv_layers': len(mesh.uv_layers), 'materials': len(mats)})
    finally:
        if mesh:
            bpy.data.meshes.remove(mesh)
        bpy.data.collections.remove(collection)
bpy.context.window.scene = original_scene

source_materials = [m for m in bpy.data.materials if m.get('wp_grass_cards') or m.get('WorldPlan_Trim_Optimization')]
assert source_materials, 'No optimized materials'
for material in source_materials:
    verify_material(material)
for item in report['trims']['objects']:
    obj = bpy.data.objects[item['name']]
    assert obj.data.uv_layers.active.name == 'TrimUV'

results['ok'] = True
(OUT / 'export_validation.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
print('OPTIMIZATION_EXPORT_VALIDATION', json.dumps(results), flush=True)
