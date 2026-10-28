# Blender models and animations

Python scripts in this folder build meshes, rigs and animations in Blender and export them as FBX files for Roblox Studio. Blender runs in the background, so you never need to open it, and no add-ons are involved. You can still open any result in Blender to look at it or tweak it.

```text
blender/rbx.py            Helpers: shapes, vertex colours, rigs, keyframes, Roblox-checked FBX export, previews
blender/models/           One script per static model (cauldron.py, waystone.py, and the whole village in hollowmere.py)
blender/animations/       One script per rigged model and its animations (spellbook.py)
blender/vfx/              One script per effect: plain meshes that the game tints and animates in code (dash.py)
blender/exports/          Generated .fbx, .blend and .png files (ignored by git; rebuild any time)
blender/after_import.lua  Studio fix-up to run once the models are imported (step 5)
blender/place_waystones.lua  Studio script that stands the Waystone meshes at the map's three Waystones
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

`Hollowmere.fbx` has 39 meshes and about 95,000 triangles. The largest mesh has about 16,400, under the 20,000 limit. Each building is a Model holding a `Building` mesh, plus `Lit window` and `Window glass` meshes named as WorldService's night lights expect. Oakhart's also has `Display glass`, which needs Transparency 0.45 to match the map. Import it with **Insert Using Scene Position** on, and it lands exactly over the part village. Then run the fix-up (step 5), which also removes Blender's `.001` name suffixes. The importer uploads every mesh to your account.

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

Import it like any model (step 3), run the fix-up (step 5), then move the DashVFX model into `ReplicatedStorage.VFX`, so every client can clone it. Until it is there, a dodge shows the old plain burst.

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
