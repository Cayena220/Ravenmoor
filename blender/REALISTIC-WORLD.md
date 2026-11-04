# WorldPlan realistic environment

The edited scene is `exports/WorldPlan.blend`. Its complete pre-edit backup is
`exports/WorldPlan.before-realistic-world.blend`.

The academy architecture, staff, duel area and choosing mirror are protected:
44 objects have matching geometry, transforms, vertex colours and material-node
fingerprints before the edit and after reopening the saved file.

The environment includes textured oak woodland, meadow grass and ferns,
eroded mountains and grounded rocky outcrops, an irregular reflective lake with
reeds, detailed masonry ruins, glazed herbology houses with planted interiors,
timber pitch stands with cloth banners, cobbled roads, village surface materials,
gutters, ivy, barrels and small market stalls. The original world layout is retained.

`REALISTIC WORLD` contains the new editable meshes, linked vegetation instances,
procedural materials and six named cameras. Replaced objects remain in the hidden
`Original environment - hidden recovery` collection. Trees share mesh data to
reduce storage; their existing bark and leaf textures are packed in the blend.

The file opens in Solid material-colour mode for responsiveness. Use Rendered
mode or render one of the six cameras for the final materials and atmosphere.
The reviewed PNGs are named `exports/WorldPlan_Realistic_*.png`.

This edit is to the Blender scene. It does not alter the Roblox place or export
new game meshes. The protected academy retains its existing artistic style.

The deterministic authoring source is `rebuild_worldplan_realistic.py`. It expects
the pre-rebuild WorldPlan scene and refuses to apply a second rebuild. Do not run
the older world-assembly generator over this file: it would replace these edits.
Validation results are in `exports/WorldPlan.realistic-world-validation.json`.
