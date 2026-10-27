# Expanded Ravenmoor Academy

The academy is an editable, furnished Roblox model, integrated into the supplied game. The main campus foundation is 172 × 218 studs, about 2.2 times the old 144 × 120 courtyard footprint. The exterior is a realistic gothic castle school built only from parts and wedges:

- **Walls**: two-tone stone (Slate, with weathered blocks set just proud of the face), a cobblestone plinth, and limestone string courses and cornices on every outside wall.
- **Buttresses and windows**: stepped buttresses at most 16 studs apart, with limestone weathering caps. Pointed lancet windows in limestone surrounds pass through the wall, so they show inside and out.
- **Roofs**: steep 52° slate roofs whose eaves drop below the wall top, with stone gables at both ends and ridge caps. The Great Hall has an open timber roof, two iron chandeliers and a clerestory above the wing roofs.
- **Hall front**: oak gate doors in a limestone hood, a great window with mullions and transom, and a rose window in the gable.
- **Towers**: the copper-spired Rookery Tower (about 155 studs to the finial), the West Tower, two gate turrets, the North-west Tower, the Starwatch Tower with a glazed observatory lantern, and a square clock tower with belfry, dials and pinnacles. Round towers have octagonal spires.
- **Night**: about one window in three is a `Lit window`. WorldService switches those parts from Glass to Neon between 18:30 and 06:00.

![Academy exterior](academy-exterior.png)

![Floor plan](academy-floor-plan.png)

| Room | Design and purpose |
| --- | --- |
| Great Hall | Dining tables, benches, house banners and access to the existing Mirror of Choosing |
| Five classrooms | Hex, Ward, Charm, Restoration and Alteration; blackboards, teacher desks and clear lesson target lanes |
| Library & Archive | Bookshelves, reading table and the existing restricted-shelf interaction |
| Infirmary | Two beds and a treatment table, ready for future healing interactions |
| Potions Laboratory | Two brewing workstations, ready for future crafting interactions |
| Staff & Headmaster | Administrative office and meeting desks |
| Four house suites | Emberclaw, Stoneroot, Skyquill and Nightfang; four beds and a common-room table per house |

All 14 rooms occupy one accessible ground level. Ten-stud-wide open arches, two teaching corridors and an east passage connect the wings. Walls are 22 studs high in ordinary rooms and 32 in the hall; the roofs above them are open to the room. Beds and furniture are scenery; this change does not add sleeping, infirmary healing or laboratory crafting mechanics. Existing lessons, library actions and sorting continue at their original coordinates.

## Files and editing

- `Wandbound-Ravenmoor-Academy.rbxlx`: full game with the academy already installed.
- `world/RavenmoorAcademy.rbxmx`: reusable architecture and furniture model. Insert it into Workspace from a file in Studio. It does not include the game's NPCs, quest markers, Mirror prop or services; these remain in their existing map groups in the full game. Avoid inserting a second copy into the supplied place.
- `tools/academy.py`: room layouts and geometry generator.
- `tools/upgrade_academy.py`: rebuilds only the academy, exports the model, and prepares `world/Map.rbxmx` using surrounding geometry from the current place. Replaces the Academy, Classrooms and Library groups; preserve manual edits to those groups before running.

After closing the place in Studio:

```bash
python3 tools/upgrade_academy.py
python3 tools/sync_scripts.py --map
python3 tools/validate.py
```

The map sync creates a `.rbxlx.bak` backup. The normal `tools/build.py` full rebuild also uses the new academy design, but regenerates the entire world. The floor plan can be refreshed with `python3 tools/preview_academy.py` (optional Matplotlib dependency). That script draws only box parts, so its exterior view leaves out the wedge gables and spires; the exterior image above is a geometry render that includes them.

Gables, spires and window heads are triangles made from two WedgeParts each. They assume the same wedge orientation as the village roofs: `WEDGE_FLIP` in `tools/academy.py` must match `ROOF_FLIP` in `tools/build.py`. If Studio shows spires or gables as notched or inside-out shapes, flip both.

## Validation and remaining playtests

The model contains 1,132 parts (Parts and WedgeParts); the world contains 2,704. Limits of 1,300 academy parts and 2,900 total map parts keep it bounded. All exterior detail is non-colliding and ignored by raycasts, apart from walls, buttresses, gables, roof slabs and tower bodies. Geometry checks flood the floor with a 2.5-stud-wide, 5.5-stud-tall player envelope and verify routes to every room, the Mirror, library and all five professors. Existing classroom target clearance and gameplay tests also pass.

Roblox Studio checks remain necessary: look at the spires and gables from the courtyard, walk every doorway, test indoor camera behavior under the tall open roofs, check the lit windows and room lighting at night, finish a professor's lesson in each classroom, use the Mirror and library, and profile a mobile device. The previews are geometry renders, not screenshots from Roblox Studio.
