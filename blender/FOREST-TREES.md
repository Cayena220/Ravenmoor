# Whisperwood forest trees

Three oak variants built in Blender: **Mature**, **Tall**, and **Young**. Each has
irregular tapered branching, flared roots, geometric lobed leaves, UVs and PBR
materials. The Blender foliage shader includes thin-leaf translucency and tint
variation. These are static scenery assets, without a wind rig.

## Files

Open `exports/ForestTrees/ForestTrees.blend`. It includes the three editable trees,
packed texture maps, hidden lower-detail collections, and a presentation scene.
The presentation ground, lights and camera are excluded from the FBX exports.

Each tree has independent `LOD0`, `LOD1`, and `LOD2` FBX files at the root origin.
`manifest.json` records exact triangle counts, mesh counts and dimensions for the
current build. Every mesh is checked against the project's 20,000-triangle limit,
with one material and one UV set per mesh.

- **LOD0:** detailed lobed leaves, suitable for close views and Blender renders.
- **LOD1:** simplified folded leaves and reduced branch topology.
- **LOD2:** distant/forest-fill version, fewer leaves and small twigs omitted.

These are separate files for choosing a performance budget, not automatic Roblox
distance switching. Profile the density and chosen version in the target game.
The low-detail models deliberately enlarge the remaining leaves to keep coverage.

## Roblox Studio import

1. Import one FBX with **Import 3D**, **Scale Unit = Studs**, and default axes.
   One Blender unit equals one stud; Blender Z becomes Studio Y.
2. Anchor the imported MeshParts and set their Color to white. Enable
   **DoubleSided** on the meshes whose names contain `_Leaves`.
3. Use the `Oak_Bark_*` maps for `_Bark` meshes and `Oak_Leaf_*` maps for `_Leaves`
   meshes. The FBX embeds the images, and the maps are also in `textures/`.
   If the importer does not retain a PBR channel, upload the matching PNG and set
   `SurfaceAppearance.ColorMap`, `NormalMap`, and `RoughnessMap`. Metallic is zero.
   Blender's translucent shader does not transfer through FBX; the image maps do.
4. Put the root pivot at ground level. The exposed roots extend slightly below
   zero so the tree meets the ground naturally.
5. Use simple trunk collision for gameplay; turn collision off for foliage.

The assets are prepared locally. This build does not upload anything to Roblox,
replace the existing forest, or change the place file.

## Rebuild

From the `Wandbound` directory:

```powershell
python tools/fetch_forest_textures.py
python tools/blender.py blender/models/forest_trees.py --preview
```

Blender 5.2.3 was used for the supplied files. No add-ons are required. Seeds and
dimensions are in `models/forest_trees.py`. `--quick` reduces preview samples.
If source bark maps are missing, the generator uses a procedural fallback;
run the fetch step for the supplied scanned-bark appearance.

## Texture credit

Bark: [Jolcham Oak Bark 01](https://polyhaven.com/a/jolcham_oak_bark_01),
Charlotte Baglioni / Poly Haven, [CC0](https://polyhaven.com/license).
Downloaded diffuse, OpenGL normal, and roughness maps; source checksums are
recorded in `tools/fetch_forest_textures.py`. Distribution PNGs are resized to 2K.
Leaf maps and all tree geometry were generated for this project.
