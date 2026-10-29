# Blender models and animations

Python scripts in this folder build meshes, rigs and animations in Blender and export them as FBX files for Roblox Studio. Blender runs in the background, so you never need to open it, and no add-ons are involved. You can still open any result in Blender to look at it or tweak it.

```text
blender/rbx.py            Helpers: shapes, vertex colours, rigs, keyframes, Roblox-checked FBX export, previews, EEVEE pictures
blender/terrain.py        Mountain ranges, woods and ground mist, as Roblox meshes
blender/models/           One script per static model (cauldron.py, waystone.py, the whole village in hollowmere.py, and
                          the mountain ranges and woods round the world in ranges.py)
blender/animations/       One script per rigged model and its animations (spellbook.py, character.py)
blender/vfx/              One script per effect: plain meshes that the game tints and animates in code (dash.py)
blender/world/            world.py: assembles the whole game in one scene, exports/World.blend
blender/exports/          Generated .fbx, .blend and .png files (ignored by git; rebuild any time)
blender/after_import.lua  Studio fix-up to run once the models are imported (step 5)
blender/place_waystones.lua  Studio script that stands the Waystone meshes at the map's three Waystones
blender/place_ranges.lua  Studio script that sets up the imported mountain ranges and woods
blender/place_hollowmere.lua  Studio script that sets up the imported village over the part one
blender/place_dash.lua    Studio script that puts the imported dash effect in ReplicatedStorage.VFX
tools/blender.py          Finds Blender and runs scripts
```

## 1. Install Blender

Install Blender 4.2 or newer from [blender.org](https://www.blender.org/download/), or with winget:

```bash
winget install --id BlenderFoundation.Blender -e
```

Then check that the runner finds it. This prints the path and version:

```bash
python tools/blender.py
```

If Blender is somewhere unusual, such as a portable copy, set `WANDBOUND_BLENDER` to the full path of `blender.exe`, for example `$env:WANDBOUND_BLENDER = 'D:\Blender\blender.exe'` in PowerShell.

## 2. Build

From the `Wandbound` folder:

```bash
python tools/blender.py blender/models/cauldron.py --preview
```

```bash
python tools/blender.py "blender/*/*.py" --preview
```

Each script writes `blender/exports/<Name>.fbx` and saves its scene as `<Name>.blend`. `--preview` also renders `<Name>.png`. A still is rendered for a model, and a strip of four frames for an animation. Before exporting, every mesh is checked against Roblox's limits. A script fails with a clear message if a mesh has more than 20,000 triangles, more than one material or UV map, or a vertex moved by more than 4 bones.

## 3. Import a model into Studio

1. In Studio, choose **File → Import 3D** (also on the Home and Avatar tabs) and pick the `.fbx` from `blender/exports/`.
2. Under **File Geometry**, set **Scale Unit** to **Studs**. Under **File Transform**, keep **World Forward = Front** and **World Up = Top**. These are Studio's defaults.
3. Keep **Upload to Roblox** on. Studio uploads the mesh to your account, which every MeshPart needs to work in a published game. Turn on **Insert Using Scene Position** if the script placed the model where it belongs.
4. Rigged files such as `Spellbook.fbx` are detected as **Rig Type: Custom**. They import as a model with an AnimationController, whose MeshPart contains the Bones.
5. Run the after-import fix-up (step 5) to bring out the true colours. Studio multiplies the mesh's vertex colours by the part's Color, and the importer's default grey (163, 162, 165) dims every colour by about a third.
6. Imported parts are unanchored. Anchor them before playing unless they should fall.

The first import (October 2026, Studio 0.745) confirmed sizes in studs and orientation. The cauldron came in at 4.08 × 3.10 × 3.80 studs, matching Blender's X × Z × Y. What faces Blender's Front view faces the part's front (LookVector, −Z).

Imported meshes are uploaded assets. Once one is in the place, its asset ID is in the place too. The top-level README's "no asset IDs" note then no longer applies.

## 4. Import an animation

Import the animation file itself with the 3D Importer (step 3), for example `Spellbook_Open.fbx`. It contains the mesh and rig too. The importer reads the keys by itself:

- It makes a KeyframeSequence at `ServerStorage.RBX_ANIMSAVES.<file>.Scene`, one keyframe per frame, looping, priority Action, with the last keyframe named `End`.
- The model's `AnimSaves` value points to it, so the Animation Editor lists it when you select the model.

**Rename the root pose before playing it.** Each keyframe's top Pose is named after the Blender armature, such as `SpellbookRig`. Studio's Animator only drives the bones under it if that Pose has the same name as the MeshPart holding the bones, such as `Spellbook`. Otherwise the root bone ignores its keys: the spellbook's cover still opened, but the book never rose. Blender can't give the armature and the mesh the same name, so the after-import fix-up (step 5) renames the Pose in every keyframe.

To use it in the game, open the model in the **Animation Editor** (Avatar tab), load the animation from its saves and choose **⋯ → Publish to Roblox**. That gives an animation ID for scripts. The AnimationController needs an Animator child to play it.

## 5. Run the after-import fix-up

[after_import.lua](after_import.lua) fixes both import quirks at once:

1. In Explorer, select the imported models. Selecting a part inside a model works too.
2. Open **View → Command Bar**, paste the whole of `blender/after_import.lua` and press Enter.
3. The Output window lists what changed in each model, for example `Spellbook_Open: 1 MeshParts set to white, 61 root poses renamed in 1 animations`.

It turns every MeshPart still in the importer's grey to white. It also renames each imported animation's root Poses to the MeshPart that holds the bones (step 4). Running it again changes nothing. Parts you have recoloured are left alone, and so are animations saved from the Animation Editor, which already use the right name. Claude can run it for you over the Studio connection.

## Hollowmere, remodelled

`models/hollowmere.py` rebuilds the village's four shops, six cottages, square furniture, village road lamps, ferry dock and sky ferry. It replays `tools/build.py` to get every footprint, wall, door, window, colour and night-light pane, so the Blender village fits the map exactly and every door still meets its NPC prompt. What changes is the detail:

- windows set into real openings with timber reveals, mullions, sills, shutters and flower boxes;
- half-timbering that stands proud of the plaster, jetties on carved corbels;
- tiled roofs over framed gables, with brick chimneys and pots;
- coursed stone plinths, ashlar on the bank, plank doors with iron straps, and lettered shop signs.

The ground, square paving and lanes stay as the map's parts. They appear only in the previews and the `.blend`, as `_Preview ground`.

```bash
python tools/blender.py blender/models/hollowmere.py --preview
```

`Hollowmere.fbx` has 39 meshes and about 95,000 triangles. The largest mesh has about 16,400, under the 20,000 limit. Each building is a Model holding a `Building` mesh, plus `Lit window` and `Window glass` meshes named as WorldService's night lights expect. Oakhart's also has `Display glass`, which needs Transparency 0.45 to match the map. Import it with **Insert Using Scene Position** on; the importer uploads every mesh to your account. Then paste [place_hollowmere.lua](place_hollowmere.lua) into **View → Command Bar** and press Enter. It does the following:

- It stands the village exactly over the part one, even if it was imported without scene position, and moves it into `Workspace.Scenery`, out of `Workspace.Map`, so a map sync leaves it alone.
- It hides the map's part houses, street furniture, dock, ferry and village road lamps under it. They keep their collision, doorways and lights, so players walk into the shops as before, the lamps still shine at night, and `tools/validate.py` still finds the walls.
- It drops Blender's `.001` name suffixes, anchors the meshes, leaves them uncollidable and turns them white. It makes the windows glass: `Lit window` in lamplight colour, `Window glass`, and `Display glass` at Transparency 0.45. `WorldService` turns every `Lit window` in `Workspace.Scenery` to Neon after dark, as on the map.

Run it again after every `tools/sync_scripts.py --map`, which brings the part village back into view.

## Waystone, remodelled

`models/waystone.py` replaces the map's 3 × 7 × 3 slate block and neon ball with a dressed runestone monolith. The stone stands on a three-step octagonal dais, 7.9 studs across, and has two riveted bronze bands. On top, an iron cradle of four talons holds a floating crystal 9.5 studs up. Glowing runes run down the front under a ringed raven sigil and up the back. A ley line climbs each side, and eight more runes and a lit ring lie on the steps.

```bash
python tools/blender.py blender/models/waystone.py --preview
```

`Waystone.fbx` is one Model with four meshes and about 6,400 triangles. It is centred on its origin, with the sigil facing the front. Each mesh is set as below, which `place_waystones.lua` does for you. Neon glows in the part's Color and ignores the vertex colours, so the two Neon meshes need the old rune's teal, 130, 228, 226, instead of the fix-up's white.

| Mesh | Material | Color | CanCollide | Holds |
|---|---|---|---|---|
| `Stone` | Slate | white | on | Dais, foot, monolith, moss |
| `Ironwork` | Metal | white | off | Bands, rivets, crown and talons |
| `Runes` | Neon | 130, 228, 226 | off | Every glowing inlay |
| `Crystal` | Neon | 130, 228, 226 | off | The floating crystal and its two shards. It is a separate mesh so that a script can spin and bob it. |

The previews show a 5.5-stud stand-in player for scale; it is not exported.

Import it once, which uploads the meshes, then paste [place_waystones.lua](place_waystones.lua) into **View → Command Bar** and press Enter. It builds the meshes from their asset IDs and sets them as in the table, in each of the map's `Map.<name> Waystone` models:

- Each stone is centred on its marker and stands on the lowest ground under its dais.
- Each sigil turns toward where `Config.Waystones` lands travellers: Hollowmere +Z, Castle −Z and Whisperwood +X.
- The slate Stone's nameplate moves onto the new Stone, at StudsOffset 0, 7.6, 0. The slate Stone and the neon Rune are removed.

The script prints a line for each Waystone. It warns if anything stands inside a stone's volume, or if the ground under a dais is uneven enough to bury one side. Running it again changes nothing.

`tools/sync_scripts.py --map` brings back the generated map's slate blocks, so run the script again after a map sync. If you import `Waystone.fbx` again, copy the new MeshIds into the script's `MESHES`.

## Dash effect

`vfx/dash.py` builds `DashVFX.fbx`: one Model, DashVFX, holding three near-white meshes. `Streak` is two wind ribbons twisting round the dash path. `Speed lines` is ten tapered needles. `Ring` is a shock ring with a fainter ripple inside it. Nothing is animated in Blender. When a character dodges, `EffectsController:Dash` clones the meshes, tints them, makes them Neon and tweens them. It stretches the streak over the dash, blooms the ring where the dash began, and trails the speed lines and a flat dust ring behind the landing. With Reduced effects on, it plays only the streak and the ring.

Import it like any model (step 3), then paste [place_dash.lua](place_dash.lua) into **View → Command Bar** and press Enter. It moves the DashVFX model into `ReplicatedStorage.VFX`, so every client can clone it, drops Blender's `.001` name suffixes and turns the meshes white. Until it is there, a dodge shows the old plain burst.

## Character animations

`animations/character.py` animates R15 avatars: `Walk` (1 s loop), `Sprint` (0.6 s loop) and a roll each way, 0.5 s: sideways (`TumbleRight` and `TumbleLeft`), a somersault (`TumbleForward`) and a back roll (`TumbleBack`). The rig's bones are the R15 joints, named after the part each one moves and placed at a Studio avatar's rest pose. Each bone's axes are turned to Roblox's (X right, Y up, Z back). R15 joint frames are axis-aligned, so a keyed rotation is the joint's Transform in game. The script exports `Character<Name>.fbx` with preview strips, plus `CharacterAnimations.json`, which holds every key pose as Roblox CFrames.

These clips are not imported with the 3D Importer. Claude builds them over the Studio connection from the JSON, as KeyframeSequences inside the Animations in `ReplicatedStorage.Animations`. `EffectsController` then works as follows:

- When your character spawns, it puts Walk and Sprint into the default Animate script's `walk` and `run` slots. Animate plays walk up to 8 studs a second and run at full speed.
- On your own dodge, it turns you to face where the camera looks and plays the Tumble the way you went: Right or Left across the camera's view, Forward into it, Back toward it. Shift dodges the way you are moving; tapping W, A, S or D twice within 0.3 s dodges that way. Without the clip, a dodge turns you to face the way you went.

Until a clip is published, Studio playtests play it from its KeyframeSequence, and a live game keeps Roblox's defaults. To publish one, right-click its KeyframeSequence and choose **Save to Roblox**. Then paste the new ID into that Animation's `AnimationId`. Publish under the account or group that owns the experience.

## Mountains and woods

`models/ranges.py` builds the mountain ranges and woods round Ravenmoor (`terrain.py`) and exports `Ranges.fbx`. Knife-edged ridges and needle spires rise from 18 studs off every road and every area players walk: the village, the campus, the yard, the arena, the lake, the forest and each Castle Grounds landmark. They reach full height about 140 studs further on, and the tallest stand past the meadow's edge with snow on their peaks, closing the world in. The faces are coloured by height and slope: grass, moor and heather, scree, banded crags and snow. About 4,500 round-canopy trees crowd the foot of the slopes and stand in woods across the meadow, never within 8 studs of a road or an area.

The script rebuilds the map with `tools/build.py` and `tools/layout.py`, so the ranges always fit it. Rebuild them after the layout or an area changes:

```bash
python tools/blender.py blender/models/ranges.py --preview
```

`Ranges.fbx` is one model, Ranges, holding Mountains (16 tiles) and Woods (25 meshes of up to 300 trees). That is 41 meshes and about 483,000 triangles, the largest 19,200, under Roblox's 20,000. Everything has vertex colours and stands where the game has it. To put it in the game:

1. Import `Ranges.fbx` as in step 3, with **Insert Using Scene Position** on. The importer uploads all 41 meshes to your account. If it lands in the wrong place, the script below puts it back.
2. Paste [place_ranges.lua](place_ranges.lua) into **View → Command Bar** and press Enter. It moves the model into `Workspace.Scenery`, out of `Workspace.Map`, so `tools/sync_scripts.py --map` leaves it alone. It also streams Scenery persistently, so the far ranges never vanish past the streaming radius.
3. The script also remakes each mountain tile with PreciseConvexDecomposition collision, so players walk up the slopes and are stopped by the crags. This takes about 15 seconds a tile, four minutes in all. It anchors every mesh and turns it white, so the vertex colours show true. The trees are scenery: players and spells pass through them.

Running the script again changes nothing. After rebuilding the ranges, delete `Workspace.Scenery.Ranges` and import the new file.

## The whole world

`world/world.py` puts the whole game in one Blender scene, `exports/World.blend`. Open it to see every model where the game has it before you change one, or to block out a new model where it will stand. Each area is a collection under `Ravenmoor`:

- **The part-built map.** The script calls `tools/build.py` itself, so the scene always matches the map it makes, laid out by `tools/layout.py` (see "The layout" below). That covers the land, roads, lamps, the academy, Whisperwood, Castle Grounds with the training yard and the four landmarks, the duel arena, Mirrorlake, the chests and the staff. Every part becomes a mesh in its colour, one object per model.
- **The Blender models**, appended from their own `.blend` files and stood where the game has them (`PLACED` in the script).
  - Hollowmere replaces the map's part village, its road lamps, dock and ferry, and keeps the map's square, lanes and paths.
  - The three Waystones replace the slate stones, turned as `place_waystones.lua` turns them.
  - The Cauldron stands at the Apothecary and the Spellbook in the Library.
  - The character mannequin stands on the arrival pad for scale.
  - The mountain ranges and woods (`Ranges.blend`) fill the Scenery collection.
- **The models the game builds in code.** `world/game_models.lua` runs the game's own builders outside Roblox and records the parts they make, so these always match what the game spawns:
  - every monster at its spawn point, in Whisperwood (`MonsterService`);
  - the training dummies, in Castle Grounds (`InteractionService`);
  - the five lesson targets in front of each teacher, in the academy (`ClassService`);
  - a wand gallery west of the arrival pad: every wood at every rarity, and the three named wands (`WandModel`).

  This needs Lua 5.4, found as `tools/validate.py` finds it (`WANDBOUND_LUA_LIBRARY`). Without it, the world builds without these models and says so.
- **Showcase** (its own collection, beside the arrival pad):
  - A dodge across the pad, frozen just after it lands on the mannequin, laid out as `EffectsController:Dash` draws it (`vfx/dash.py`).
  - Three more mannequins, posed mid-walk, mid-sprint and mid-tumble.
- **Animations.** Every clip (Walk, Sprint, the four Tumbles and the Spellbook's opening) is kept in the file. To play one, select a rig and pick the clip in Blender's Action editor.
- **Markers.** Every interaction and quest point is a labelled empty.
- **Config zones.** `Config.Zones` and `Config.WorldBounds` are frames over the map. They are red where monsters attack, blue where they don't, and gold for the bounds. Switch the collection off to hide them.
- **Mist.** A ground mist and a thin air that blues the far ranges: two volumes, Mist and Air, used only by the EEVEE pictures, so the collection is hidden in the viewport. Switch it on and use Rendered shading to see them. EEVEE takes a world volume to be endless and blacks out the sun, so haze must be an object like these.

Each build checks the map against Config by `WorldService`'s own rules. A point outside the bounds sends players back, and a point in no zone counts as a safe Castle Grounds, where monsters never attack. The build lists any map part, monster or marker that falls outside the bounds or every zone, any Castle Grounds landmark in an unsafe zone, and any Waystone landing far from its stone; today there are none. It also prints walking times between the square, the academy gate, the west wing stair, the training yard, Tobb and the forest gate. The times are by road at 16 studs a second, with the straight-line time in brackets. The Waystones stand at the square, the gate and the forest gate.

Build the models before the world. This runs every script in folder order, so `world/` comes last:

```bash
python tools/blender.py "blender/*/*.py" --preview
```

`--preview` also renders `World.png`, the academy road, the forest path and the forest road, and close-ups of the village, the academy, the training yard, the showcase, the wand gallery, the monsters, the boss and each Castle Grounds landmark. `World_zones.png` is a map from straight above, north up, with the zones and bounds on it. Five EEVEE pictures go through `rbx.beauty`: `World_vista_academy.png` up the academy road, `World_vista_west.png` over the forest and the western ranges, `World_vista_aerial.png`, `World_vista_ruins.png` and `World_vista_pitch.png`. They have a low sun behind the camera, a sky, the haze and the mist.

The scene is assembled from the scripts, so don't save hand edits into `World.blend`; the next build replaces it. Change a model in its own script, and change the part map in `tools/build.py` or `tools/layout.py`, then rebuild. To add a model to the game:

1. Write its script under `blender/models/`.
2. Add its `.blend` and where the game stands it to `PLACED`.
3. Export and import it into Studio as before (steps 3 to 5).

### The layout

`tools/layout.py` sets where the areas stand. `tools/build.py`'s builders lay every area out beside Hollowmere, where the map was first made, at the points in `build.LAID_OUT`. The layout then moves them, so the walks between them take half a minute. `build.POINTS`, `src/shared/WorldPoints.lua` and `Workspace.Markers` hold the moved points.

- **Hollowmere stays put,** since players spawn there.
- **The academy** stands 300 studs north with its grounds: the training yard, the duel arena, Mirrorlake, its lamps, teachers and lesson targets.
- **Whisperwood** stands 300 studs west with its monsters, chests, gate and Waystone, and with Tobb, who sends players into it.
- **Roads:** the academy road and the forest path are carried out to them by `build.py`'s own road builders and lamps. A forest road leaves the academy road just south of the gate and runs straight to the forest path beside Tobb, and the west wing's campus path is carried down to it.
- **Ground:** the meadow and the invisible world edge widen to hold everything.
- **Castle Grounds landmarks.** `GROUNDS` stands four landmarks from the design plan on the land between, each with a gravel path from a road. `tools/grounds.py` builds them as plain parts in the build kit, at full size:
  - The **flying pitch** is east of the academy road: a 160 × 84 field with markings, a beacon spire and two marker posts at each end, and three-tier stands down both sides under the house banners. It stays empty until the flying sport.
  - The **Ruins of Old Ravenmoor**, for the House War, are between the three roads. A breached wall surrounds a 120 × 110 court with tower stumps, the old keep's broken tower, a fallen colonnade and the three control points.
  - The **greenhouses**, for herb gathering, are south of the forest path near the village: three glasshouses, herb beds and a potting shed.
  - The **groundskeeper's hut** is across the path from Tobb at the forest edge: a stone cottage with a vegetable plot, a woodpile and a beast pen.

The game's code follows the layout. `Config.Zones`, `Config.WorldBounds` and `Config.Waystones` cover the moved areas. `MonsterService`'s spawns, `DuelService`'s arena and `InteractionService`'s training dummies stand where their areas now are. `tools/validate_academy.py` moves the campus constants from `tools/academy.py` by the same 300 studs. Walking times against the layout before the move:

| Walk | Before | Now |
|---|---|---|
| Square to academy gate | 10 s | 29 s |
| Square to forest gate | 14 s | 32 s |
| Academy gate to forest gate | 12 s | 37 s |
| Training yard to Tobb | 12 s | 40 s |

After changing the layout, rebuild the map and copy it into the place:

```bash
python tools/build.py --world-only
```

```bash
python tools/sync_scripts.py --map
```

Then rebuild the ranges and import them again. Run `place_waystones.lua` again too, because a map sync brings back the slate stones.

## Conventions

| Rule | Why |
|---|---|
| 1 Blender unit = 1 stud. The player is 5.5 studs tall, an everyday door 6 × 10 (docs/BUILD-KIT.md). | Exports use Roblox's recommended "FBX Unit Scale", read as studs. |
| Z is up and the model's front faces −Y, Blender's Front view (numpad 1). | The export turns Z up into Roblox's Y up. |
| One `rbx.Mesh` = one MeshPart. Colour each piece with a palette colour from `tools/palette.py`. | Vertex colours need no textures or UVs, and Roblox allows one material per mesh. |
| At most 20,000 triangles per mesh and 4 bone influences per vertex. Every piece of a rigged mesh is moved by one bone. | Roblox's mesh and skinning limits. |
| Animations run at 30 fps, one animation per FBX, with keys inside the scene's `frames`. | Roblox imports a single animation track per file. |
| Lay bones along +Y where you can. | Then a bone's axes match the world's, and `move`/`turn` values read naturally. |

## Writing a script

```python
"""Brass candlestick for the Great Hall tables: a turned stem on a round foot, with a lit candle."""
import rbx
from palette import GOLD, LAMPLIGHT

rbx.scene('Candlestick')
stick = rbx.Mesh('Candlestick')
stick.lathe([(0, 0), (0.6, 0), (0.6, 0.1), (0.15, 0.3), (0.12, 1.4), (0.35, 1.5), (0, 1.55)], GOLD)
stick.cylinder(0.12, 0.8, (0, 0, 1.95), (236, 228, 210))
stick.sphere(0.08, (0, 0, 2.43), LAMPLIGHT, scale=(1, 1, 2))
rbx.export('Candlestick', [stick.finish(sharp=35)])
```

The shapes are `box`, `cylinder` (optionally tapered), `sphere`, `lathe` (spin a radius-and-height profile around Z) and `torus`. Each accepts `turn` (degrees) where it makes sense, and `bone` for rigged meshes. For a rig, see `animations/spellbook.py`. List bones as `(name, parent, head, tail)`, key them with `rig.key(frame, bone, move=..., turn=...)`, then export once for the model and once with `animation=True` for each animation.

## Working with Claude

Ask for a model or animation in plain words ("a raven perched on a post, with a wing-flap idle"). Claude writes the script here, builds it with `--preview`, checks the render and iterates. You then import the result (steps 3 and 4), which uploads it under your Roblox account. With the Studio connection, Claude can then inspect the imported model, place it on the map and wire up its animation.
