"""Replace shallow WorldPlan ashlar boxes with a shared limestone trim sheet.

This deliberately targets only the generated ``Ashlar facade blocks`` meshes.
Their substrate walls, true openings, roof tiles and structural trim stay intact.
Batch.box's known outward -Y face survives arbitrary baked rigid transforms.
The .16-stud return faces and bevel modifiers become subtle tangent-space relief.
No scene is opened or saved by this module. Call optimize_trims(texture_folder).
"""
from pathlib import Path
import json
import math

import bpy
import numpy as np


TAG = 'WorldPlan_Trim_Optimization'
BOX_FACES = ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7))
WIDTH, BAND_HEIGHT, GUTTER = 512, 64, 6


def _triangles(mesh):
    return sum(len(p.vertices) - 2 for p in mesh.polygons)


def _material_key(material):
    p = next((n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    roughness = p.inputs['Roughness'].default_value if p else .75
    return tuple(round(float(x), 6) for x in (*material.diffuse_color[:3], roughness))


def _validate(mesh):
    """Reject edited/non-box geometry rather than guessing an outward surface."""
    count = len(mesh.vertices) // 8
    if not count or len(mesh.vertices) != count * 8 or len(mesh.polygons) != count * 6:
        return None, 'not consecutive eight-vertex/six-quad Batch.box geometry'
    if mesh.shape_keys or mesh.color_attributes or mesh.uv_layers:
        return None, 'has authored shape keys, vertex colors or UVs'
    if any(not m or 'warm limestone' not in m.name.lower() for m in mesh.materials):
        return None, 'not the generated limestone facade material set'
    co = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get('co', co)
    co = co.reshape((-1, 8, 3))
    widths = np.linalg.norm(co[:, 1] - co[:, 0], axis=1)
    depths = np.linalg.norm(co[:, 3] - co[:, 0], axis=1)
    heights = np.linalg.norm(co[:, 4] - co[:, 0], axis=1)
    # Source blocks are 1.085 high and .16 deep. Integration can uniformly scale.
    if np.any(widths <= 0) or np.any(heights <= 0) or not np.allclose(depths / heights, .16 / 1.085, atol=.003):
        return None, 'unexpected block proportions; might contain structural geometry'
    for block in range(count):
        material_index = mesh.polygons[block * 6].material_index
        for face, expected in enumerate(BOX_FACES):
            p = mesh.polygons[block * 6 + face]
            if tuple(int(v) - block * 8 for v in p.vertices) != expected or p.material_index != material_index:
                return None, 'unexpected box topology or per-face material edits'
    return co, None


def _save_image(name, pixels, folder, non_color=False):
    height, width, _ = pixels.shape
    image = bpy.data.images.new(name, width=width, height=height, alpha=True, float_buffer=True)
    image.colorspace_settings.name = 'Non-Color' if non_color else 'sRGB'
    pixels = np.asarray(pixels, dtype=np.float32)
    if not non_color:
        # Generated image buffers save numerical RGB values directly. Encode the
        # source shader's linear RGB for an sRGB PNG before packing/reloading it.
        pixels = pixels.copy()
        rgb = np.clip(pixels[:, :, :3], 0, 1)
        pixels[:, :, :3] = np.where(rgb <= .0031308, rgb * 12.92,
                                    1.055 * np.power(rgb, 1 / 2.4) - .055)
    image.pixels.foreach_set(pixels.ravel())
    image.file_format = 'PNG'
    image.filepath_raw = str(folder / (name + '.png'))
    image.save()
    # Reload the external PNG so the packed version and game-export texture agree.
    image.reload()
    image.pack()
    return image


def _atlas(keys, folder):
    height = 2 ** math.ceil(math.log2(max(BAND_HEIGHT, len(keys) * BAND_HEIGHT)))
    base = np.zeros((height, WIDTH, 4), dtype=np.float32)
    normal = np.ones_like(base)
    normal[:, :, :3] = (.5, .5, 1)
    rough = np.ones_like(base)
    base[:, :, 3] = 1
    coordinates = {}
    inner_w, inner_h = WIDTH - 2 * GUTTER, BAND_HEIGHT - 2 * GUTTER
    yy, xx = np.mgrid[0:inner_h, 0:inner_w].astype(np.float32)
    u, v = xx / (inner_w - 1), yy / (inner_h - 1)
    # Physical dimensions match a typical source block, so the normal is restrained.
    edge = np.minimum(np.minimum(u, 1 - u) * 3.1, np.minimum(v, 1 - v) * 1.085)
    t = np.clip(edge / .035, 0, 1)
    bevel = .018 * t * t * (3 - 2 * t)
    rng = np.random.default_rng(6191)
    grain = rng.uniform(-1, 1, (inner_h, inner_w)).astype(np.float32)
    grain = (grain + np.roll(grain, 1, 0) + np.roll(grain, -1, 0)
             + np.roll(grain, 1, 1) + np.roll(grain, -1, 1)) / 5
    height_map = bevel + grain * .0012
    dy, dx = np.gradient(height_map, 1.085 / (inner_h - 1), 3.1 / (inner_w - 1))
    xyz = np.stack((-dx, -dy, np.ones_like(dx)), axis=2)
    xyz /= np.linalg.norm(xyz, axis=2, keepdims=True)
    nrgba = np.ones((inner_h, inner_w, 4), dtype=np.float32)
    nrgba[:, :, :3] = xyz * .5 + .5
    low_noise = .018 * np.sin(u * 17.9 + np.sin(v * 9.2)) + grain * .028
    edge_tone = 1 - .045 * (1 - t)
    for band, key in enumerate(keys):
        y0 = band * BAND_HEIGHT
        rgba = np.ones_like(nrgba)
        rgba[:, :, :3] = np.array(key[:3], dtype=np.float32) * (edge_tone * (1 + low_noise))[:, :, None]
        rr = np.ones_like(nrgba)
        rr[:, :, :3] = np.clip(key[3] + grain[:, :, None] * .035, 0, 1)
        for destination, source in ((base, rgba), (normal, nrgba), (rough, rr)):
            destination[y0:y0 + BAND_HEIGHT] = np.pad(source, ((GUTTER, GUTTER), (GUTTER, GUTTER), (0, 0)), mode='edge')
        # Pixel centers stay inside a padded band even with bilinear filtering.
        coordinates[key] = ((GUTTER + .5) / WIDTH, (y0 + GUTTER + .5) / height,
                            (WIDTH - GUTTER - .5) / WIDTH, (y0 + BAND_HEIGHT - GUTTER - .5) / height)
    images = {
        'base_color': _save_image('WP_Limestone_Trim_BaseColor', base, folder),
        'normal': _save_image('WP_Limestone_Trim_Normal', normal, folder, True),
        'roughness': _save_image('WP_Limestone_Trim_Roughness', rough, folder, True),
    }
    return images, coordinates, (WIDTH, height)


def _shared_material(images):
    mat = bpy.data.materials.new('OPT / shared limestone trim sheet')
    mat.use_nodes = True
    mat.diffuse_color = (.36, .32, .26, 1)
    mat[TAG] = 1
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (680, 60)
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = (380, 60)
    links.new(principled.outputs['BSDF'], out.inputs['Surface'])
    uv = nodes.new('ShaderNodeUVMap')
    uv.uv_map = 'TrimUV'
    uv.location = (-600, 100)
    for kind, y in (('base_color', 300), ('roughness', 30), ('normal', -250)):
        tex = nodes.new('ShaderNodeTexImage')
        tex.image = images[kind]
        tex.interpolation = 'Linear'
        tex.extension = 'EXTEND'
        tex.location = (-350, y)
        links.new(uv.outputs['UV'], tex.inputs['Vector'])
        if kind == 'normal':
            nm = nodes.new('ShaderNodeNormalMap')
            nm.space = 'TANGENT'
            nm.uv_map = 'TrimUV'
            nm.location = (0, -250)
            links.new(tex.outputs['Color'], nm.inputs['Color'])
            links.new(nm.outputs['Normal'], principled.inputs['Normal'])
        else:
            links.new(tex.outputs['Color'], principled.inputs['Base Color' if kind == 'base_color' else 'Roughness'])
    return mat


def optimize_trims(output_dir):
    """Optimize validated facade overlays; return JSON-serializable change stats."""
    folder = Path(output_dir).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    candidates = sorted((o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Ashlar facade blocks')), key=lambda o: o.name)
    valid, skipped, keys = [], [], set()
    for obj in candidates:
        if obj.get(TAG):
            skipped.append({'name': obj.name, 'reason': 'already optimized'})
            continue
        if any(m.type != 'BEVEL' for m in obj.modifiers):
            skipped.append({'name': obj.name, 'reason': 'unsupported non-bevel modifier'})
            continue
        coords, reason = _validate(obj.data)
        if reason:
            skipped.append({'name': obj.name, 'reason': reason})
            continue
        valid.append((obj, coords))
        keys.update(_material_key(m) for m in obj.data.materials)
    report = {'objects': [], 'skipped': skipped, 'triangles_before': 0, 'triangles_after': 0,
              'method': 'Validated outer face per shallow ashlar block; border bevel and grain use tangent normal trim sheet. Structural walls remain unchanged.'}
    if not valid:
        return report
    keys = sorted(keys)
    images, coordinates, size = _atlas(keys, folder)
    shared = _shared_material(images)
    original_materials = set()
    for obj, coords in valid:
        old = obj.data
        before = _triangles(old)
        block_count = len(coords)
        original_materials.update(m.name for m in old.materials)
        # The generated outer face is -Y in each block's own frame, including towers.
        positions = coords[:, (0, 1, 5, 4), :].reshape((-1, 3))
        faces = np.arange(block_count * 4).reshape((-1, 4))
        new = bpy.data.meshes.new(old.name + ' | trim skin')
        new.from_pydata(positions.tolist(), [], faces.tolist())
        new.materials.append(shared)
        uvs = np.empty((block_count, 4, 2), dtype=np.float32)
        for block in range(block_count):
            source_mat = old.materials[old.polygons[block * 6 + 2].material_index]
            u0, v0, u1, v1 = coordinates[_material_key(source_mat)]
            uvs[block] = ((u0, v0), (u1, v0), (u1, v1), (u0, v1))
        new.uv_layers.new(name='TrimUV').data.foreach_set('uv', uvs.ravel())
        new.update()
        obj.data = new
        removed_modifiers = [m.name for m in obj.modifiers]
        for mod in list(obj.modifiers):
            obj.modifiers.remove(mod)
        obj[TAG] = 1
        obj['Optimization detail'] = 'Shallow ashlar return faces and bevel moved to shared normal trim. Structural wall behind retained.'
        obj['Optimization source triangles'] = before
        if old.users == 0:
            bpy.data.meshes.remove(old)
        after = _triangles(new)
        report['objects'].append({'name': obj.name, 'blocks': block_count, 'triangles_before': before,
                                  'triangles_after': after, 'bevel_modifiers_removed': removed_modifiers})
        report['triangles_before'] += before
        report['triangles_after'] += after
    report.update({'texture_size': list(size), 'shared_material': shared.name,
                   'source_material_count': len(original_materials), 'unique_color_bands': len(keys),
                   'texture_paths': {k: str(Path(v.filepath).resolve()) for k, v in images.items()}})
    (folder / 'WP_Limestone_Trim_Bands.json').write_text(json.dumps({
        'color_space': 'BaseColor sRGB; Normal OpenGL tangent-space Non-Color; Roughness Non-Color',
        'size': list(size), 'gutter_pixels': GUTTER,
        'bands': [{'base_color_linear': list(k[:3]), 'roughness': k[3], 'uv_bounds': list(coordinates[k])} for k in keys],
    }, indent=2))
    return report
