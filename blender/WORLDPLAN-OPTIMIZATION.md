# WorldPlan optimization

The authored world is **partly modular**. Trees already use collection instances;
most building shells are combined meshes with their repeated details baked into
the vertex data. This pass reuses matching data and repeated planting, without
rebuilding the architecture into a grid-snapping construction kit.

## Files

- `exports/WorldPlan.blend`: optimized world after the staged file passes review.
- `exports/WorldPlan.before-optimization.blend`: complete original backup (local only).
- `exports/WorldPlan.optimized.blend`: staged optimized copy (local only).
- `exports/WorldPlan_Optimization/report.json`: measured changes and affected objects.
- `exports/WorldPlan_Optimization/validation.json`: saved-file verification result.
- `exports/WorldPlan_Optimization/textures/`: portable textures, also packed in the blend.
- `exports/WorldPlan_Optimization/before_*.png` and `after_*.png`: review renders.

## What changed

| Item | Before | After |
| --- | ---: | ---: |
| Mesh datablocks | 536 | 526 |
| Stored triangles across all mesh datablocks | 9,513,258 | 7,793,774 |
| Materials | 383 | 174 |
| Meadow grass triangles when evaluated | 436,740 | 116,464 |
| Shallow ashlar triangles | 523,320 | 87,220 |
| Garden leaf geometry stored | 832,000 triangles | 160 triangles in two prototypes |
| Existing collection instances | 4,332 | 4,332 |
| Image footprint, RGBA8 estimate, no mipmaps | 126.00 MiB | 89.00 MiB |
| Compressed Blender file | 203.89 MB | 162.48 MB |

Stored triangles include hidden recovery objects and source tree LODs. They are
not a count of the visible frame. Instancing reduces duplicated mesh storage;
the 10,400 garden leaves still evaluate to 832,000 triangles when realized.
No frame-rate claim is made.

### Shared geometry

Fifteen identical meshes now share mesh data after comparing positions, topology,
UVs, colors, material assignments and smooth shading. The existing tree collection
instances remain in place. Garden groundcover now instances two leaf prototypes;
the recovered transforms match the original vertices within 0.000061 Blender units.
The two prototypes preserve the original two leaf colors.

### Grass cards

The meadow previously used explicit five-vertex blades, not a particle system.
Each of its 29,116 planted tufts now uses two crossed textured quads, instanced
through Geometry Nodes. Placement comes from the existing tuft footprints and
base heights. Shared 512-pixel color/alpha and tangent normal maps define the blade
silhouettes and ridges. No particles are added. Transparency is visible in Material
Preview or Rendered mode; Solid mode displays the card geometry.

### Trim sheet and normal detail

The six generated `Ashlar facade blocks` meshes use 43,610 shallow boxes over
structural walls. Each box is replaced by its validated outer face. A shared
512 x 2048 limestone trim sheet has 25 padded color bands, with base-color,
tangent-space normal and roughness maps. Bevel and grain are normal-map detail;
the original return faces and facade bevel modifiers are removed. This is a new
shared detail treatment, not an exact high-to-low bake of each original block.

True wall openings, roofs, spires, door transforms and major ornaments retain
their geometry. Other materials with different appearance or shader settings
remain separate. The whole world's surfaces have not been forced onto one atlas.

### Texture and material cleanup

Six byte-identical packed oak image copies are merged without reducing their
resolution. Equivalent material node graphs are consolidated; only unused data
are purged. Hidden recovery collections remain in the scene, and the complete
pre-optimization file remains separately available.

## Validation and rebuilding

The authored `WorldPlan.blend` is tracked with Git LFS. After cloning, run
`git lfs pull` to download the binary. Its textures are packed, and the new maps
are also supplied in the optimization package. Recovery backups stay local.

Run from the `Wandbound` repository root with Blender 5.2:

```powershell
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background blender/exports/WorldPlan.blend --python-exit-code 1 --python blender/optimize_worldplan.py
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background blender/exports/WorldPlan.optimized.blend --python-exit-code 1 --python blender/tests/verify_optimization.py
```

The optimizer expects an unoptimized `WorldPlan.blend`, writes the staged sibling,
and refuses to optimize an already marked scene. To rebuild, first preserve any
new edits, then explicitly restore the original backup as `WorldPlan.blend`.
Do not run the older world generator over this scene.

To verify the supplied optimized file directly, run:

```powershell
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background blender/exports/WorldPlan.blend --python-exit-code 1 --python blender/tests/verify_optimization.py
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background blender/exports/WorldPlan.blend --python-exit-code 1 --python blender/tests/test_optimization_export.py
```

Validation compares geometry and transforms outside the explicit optimization
allowlist, checks collection-instance targets, realizes temporary copies of the
saved Geometry Nodes planting, and checks texture packing and trim UVs. The
verification script never saves its temporary realized geometry.

The saved-file validation passed for 5,058 protected objects. Export helper tests
passed for realized counts, UVs, alpha, double-sided flags, noncollision grass,
normal/roughness channels and grass shader scalars. Before/after facade and grass
renders were inspected. `completion.json` records the backup and promoted file
SHA-256 hashes; the final file is byte-identical to the validated stage.

## Roblox export

This work modifies the Blender source. It does not reimport, upload or modify the
Roblox place. The exporter now realizes grass and garden instances on temporary
copies and carries card alpha and normal/roughness image channels. The installer
sets the imported grass ColorMap to `SurfaceAppearance.AlphaMode.Transparency`.

The existing exporter merges non-tree instances into spatial chunks. Only its oak
template path currently retains runtime reuse. Blender instancing does not imply
identical runtime instancing in Roblox. A fresh export/import and profiling in
Studio are still required to measure game performance and verify uploaded maps.

The installer targets the already integrated local game. Its academy portal setup
depends on that game's `WorldService.StartAcademyPortals` and `WorldPoints` wiring;
those separate gameplay edits are not part of this optimization commit. A checkout
of this commit supplies the Blender assets and exporter, not a complete new game
deployment. The pre-optimization Blender backup is local and cannot be regenerated
from the optimized binary alone.
