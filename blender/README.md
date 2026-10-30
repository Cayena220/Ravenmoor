# Blender models and animations

Python scripts in this folder build meshes, rigs and animations in Blender and export them as FBX files for Roblox Studio. Blender runs in the background, so you never need to open it, and no add-ons are involved. You can still open any result in Blender to look at it or tweak it.

```text
blender/rbx.py            Helpers: shapes, vertex colours, rigs, keyframes, Roblox-checked FBX export, previews, EEVEE pictures
blender/terrain.py        Mountain ranges, woods and ground mist, as Roblox meshes
blender/models/           One script per static model (cauldron.py, waystone.py, the four flying brooms in brooms.py, the
                          whole village in hollowmere.py, and the mountain ranges and woods round the world in ranges.py)
blender/animations/       One script per rigged model and its animations (spellbook.py, character.py, and every other
                          spell's wand gesture in casting.py)
blender/r15.py            The R15 avatar rig and the tools for posing it, for casting.py (character.py has its own copy)
blender/vfx/              One script per effect: plain meshes that the game tints and animates in code (dash.py,
                          scintara.py)
blender/world/            world.py: assembles the whole game in one scene, exports/World.blend
blender/exports/          Generated .fbx, .blend and .png files (ignored by git; rebuild any time)
blender/after_import.lua  Studio fix-up to run once the models are imported (step 5)
blender/place_waystones.lua  Studio script that stands the Waystone meshes at the map's three Waystones
blender/place_ranges.lua  Studio script that sets up the imported mountain ranges and woods
blender/place_hollowmere.lua  Studio script that sets up the imported village over the part one
blender/place_dash.lua    Studio script that puts the imported dash effect in ReplicatedStorage.VFX
blender/place_scintara.lua  Studio script that puts the imported Scintara effect in ReplicatedStorage.VFX
blender/place_brooms.lua  Studio script that puts the imported brooms in ReplicatedStorage.Brooms
tools/blender.py          Finds Blender and runs scripts
tools/place_animations.py Writes character clips from CharacterAnimations.json and CastAnimations.json into the place
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

## Scintara effect

`vfx/scintara.py` builds `ScintaraVFX.fbx`: one Model, ScintaraVFX, holding seven near-white meshes for Scintara, the spell every wand knows. A left click throws one spark bolt. Holding the right mouse button (LT, or the touch Lance button) pours a spark lance: 5 mana to light it, then 20 mana a second while it pours. Every mesh runs along the way the spell goes, with its front (the part's LookVector) away from the wand. Nothing is animated in Blender: `EffectsController` clones the meshes, tints them arcane violet, makes them Neon and moves them each frame.

| Mesh | What it is | In the game |
|---|---|---|
| `Spark` | A six-spiked star round a small ball, with four short spikes between | The bolt's head, spinning |
| `Tail` | A tapered core and three ribbons twisting 3.4 studs back | Behind the spark, growing out over the bolt's first studs |
| `Flash` | Two six-pointed stars, a twelfth of a turn apart | Blooms at the wand tip as a bolt leaves; spins there, with a light, while the lance pours |
| `Beam` | A tube 1 stud long and 1 across | The lance's white core and its violet glow, stretched to the lance's length |
| `Coil` | Two helix ribbons, 2.5 turns in 6 studs | Tiled end to end along the lance and spun, so the twist seems to pour out of the wand |
| `Ring` | A thin ring with a fainter ripple inside | Three run out along the lance, fading |
| `Splash` | Seven sparks spraying back round a shock ring | Pulses where the lance strikes; blooms where a bolt lands |

The bolt leaves the wand tip and closes onto the server's path, which starts at the chest, over its first 12 studs. Every client draws each lance from the caster's wand to the end the server sets in the caster's `ScintaraLance` attribute ten times a second. Your own lance follows your aim each frame. With Reduced effects on, a lance keeps only its core, glow and splash. Until the meshes are imported, the bolt is the old ball and the lance a plain neon rod.

```bash
python tools/blender.py blender/vfx/scintara.py --preview
```

`--preview` renders `ScintaraVFX.png`, the seven meshes in a row. It also renders `ScintaraVFX_bolt.png`, the bolt put together, and `ScintaraVFX_lance.png`, a 14-stud lance put together. The file has 4,800 triangles; the largest mesh, `Coil`, has 2,100.

Import it like any model (step 3), then paste [place_scintara.lua](place_scintara.lua) into **View → Command Bar** and press Enter. It moves the ScintaraVFX model into `ReplicatedStorage.VFX`, drops Blender's `.001` name suffixes and turns the meshes white. Running it again changes nothing, and after a rebuild it replaces the old copy with the new import.

## Character animations

`animations/character.py` animates R15 avatars: `Walk` (1 s loop), `Sprint` (0.6 s loop) and a roll each way, 0.5 s: sideways (`TumbleRight` and `TumbleLeft`), a somersault (`TumbleForward`) and a back roll (`TumbleBack`), and `BroomRide` (2 s loop), the pose for riding a broom: leaning into the flight, hands on the grip, legs splayed round the shaft and back to the stirrups. Scintara's casts have three clips (see "Casting Scintara" below). Each broom also has a ride of its own, `BroomRide<Broom>`, and each house a dash for every broom, `BroomDash<House><Broom>` (see "Flying each broom" and "Dashing through the air" below). The rig's bones are the R15 joints, named after the part each one moves and placed at a Studio avatar's rest pose. Each bone's axes are turned to Roblox's (X right, Y up, Z back). R15 joint frames are axis-aligned, so a keyed rotation is the joint's Transform in game. The script exports `Character<Name>.fbx` with preview strips, plus `CharacterAnimations.json`, which holds every key pose as Roblox CFrames.

These clips are not imported with the 3D Importer. They are KeyframeSequences inside the Animations in `ReplicatedStorage.Animations`, built from the JSON. With the place closed in Studio, `tools/place_animations.py` writes them into the `.rbxlx`: run it bare to list the clips and see which the place lacks, then name the ones to add or replace:

```bash
python tools/place_animations.py BroomRideAshwind BroomRideStoutbough BroomRideSwiftquill BroomRideNightwing --force
```

Claude can also build them over the Studio connection. `EffectsController` then works as follows:

- When your character spawns, it puts Walk and Sprint into the default Animate script's `walk` and `run` slots. Animate plays walk up to 8 studs a second and run at full speed.
- On your own dodge, it turns you to face where the camera looks and plays the Tumble the way you went: Right or Left across the camera's view, Forward into it, Back toward it. Shift dodges the way you are moving; tapping W, A, S or D twice within 0.3 s dodges that way. Without the clip, a dodge turns you to face the way you went.
- On a broom, `FlightController` plays that broom's ride, or `BroomRide` if it has none, slower in a hover and quicker flat out. Flat out, your house's dash on that broom takes over.

Until a clip is published, Studio playtests play it from its KeyframeSequence, and a live game keeps Roblox's defaults. To publish one, right-click its KeyframeSequence and choose **Save to Roblox**. Then paste the new ID into that Animation's `AnimationId`. Publish under the account or group that owns the experience.

### Casting Scintara

Scintara's clips key only the upper body: the torso, head and arms. The legs keep walking or standing under a cast. They play at priority Action2, over the walk, the rides and the tumbles.

| Clip | Length | The cast |
|---|---|---|
| `ScintaraBolt` | 0.4 s | A left click. The shoulders turn right as the wand is cocked back over the shoulder (frame 2). It is flicked out level at frame 4 (0.13 s), as the server lets the bolt go after Scintara's 0.12 s cast time, and the body turns into it. The wrist dips through, and the arm settles. |
| `ScintaraBeamStart` | 0.2 s | The right button pressed. The wand is drawn in to the chest with the left hand coming up to it, then thrust out at the aim with both arms. |
| `ScintaraBeam` | 0.6 s loop | Held while the lance pours. The wand arm reaches in across the chest with the wand level, and the left hand braces under the wand wrist. The body leans back against the pour. A quick tremor runs through the wand arm and wrist, and a slow heave pushes the shoulders back. |

The wand is welded below the middle of the right hand and points along the hand's front, so a hanging arm holds it level and a raised one points it up. Wherever a cast aims the wand, the script solves the wrist (`aimed`) so the wand points straight ahead, whatever the arm and body do. In the lance, the left hand is fitted under the wand wrist at every key, as the brooms' grips are (`hold`). The build prints how close it comes. The previews are taken from the wand side, with a preview-only wand in the hand, `_Wand`, which is never exported.

On a left click, `InputController` fires the bolt and `EffectsController:CastBolt` turns you to face the aim and plays `ScintaraBolt`. Holding the right button plays `ScintaraBeamStart`, then loops `ScintaraBeam`. While the lance pours, you face your aim. Letting go fades the hold out over 0.15 s. Animations played on your own character show to every player. Put the clips in the place like the others:

```bash
python tools/place_animations.py ScintaraBolt ScintaraBeamStart ScintaraBeam
```

### Casting every other spell

`animations/casting.py` gives every other spell a wand gesture of its own: a clip per gesture, `Cast<Motion>`, and `SpellData` gives each spell its `Motion`. A spell's type picks one (a projectile thrusts, a beam zaps, an area spell raises a dome, a ward on yourself wards, a heal mends) unless the spell names its own. Spark Bolt has none, since Scintara's casts are the clips above.

| Clip | Spells | The gesture |
|---|---|---|
| `CastLash` | Flame Lash | A whip. The wand is drawn back high over the right shoulder while the left hand points the way, then lashed down and across the body to the far hip, the shoulders turning through. |
| `CastThrust` | Frost Shard, Disarm | A fencer's lunge. The wand is chambered at the ribs with the left hand out as a guide, then stabbed at the aim at full stretch as the left hand sweeps back to the hip. |
| `CastHurl` | Blast Hex | Both hands. The wand stands over the cupped left hand as if holding an orb at the chest, draws it in, and both hands hurl it out at the aim. |
| `CastZap` | Chain Lightning | The wand raised high, struck down at the aim and held there, shuddering with the discharge, while the left hand braces the wand arm from below. |
| `CastPull` | Pull | Both hands reach out at the aim as the beam takes hold, then yank back to the chest, leaning away. |
| `CastUplift` | Lift | A scoop: both hands low and palm up, swept up together. |
| `CastChop` | Stone Bind | An overhead chop, brought down hard at the aim. |
| `CastLull` | Slumber | A lullaby: the wand sways side to side like a pendulum, releasing on the first swing, while the left hand smooths the air, palm down. |
| `CastWard` | Ward Shield, Mirror Ward, Stoneskin | The wand swept up to stand straight before the face, and the left palm pushed out beside it like a shield. |
| `CastDome` | Bastion Dome | Both hands flung up overhead, then spread wide and drawn down round the sides, tracing the dome. |
| `CastSwirl` | Light Orb, Swiftstep | The wand held up and stirred once round overhead, its tip ringing the air, then flourished down to the front. |
| `CastMend` | Mend, Cleanse | The left hand held out palm up while the wand stirs above it, then the palm pushes the healing out at the aim. |
| `CastTwist` | Unseal | The wand pushed into the lock like a key, then turned. |

Each gesture is written as where the hands go, not as joint angles. At each key the script gives where the middle of the wand hand goes and which way the wand points, and for the left hand which way its palm faces and its fingers point. It then bends each arm onto those marks (`arm`, a least-squares solve over the shoulder, elbow, forearm twist and wrist). When a mark can't all be met, the wand's aim wins over where its hand goes: a hand a fraction of a stud off doesn't show, a wand off its aim does. The build prints how close each clip comes, and stops if a hand misses its mark by 0.6 studs or 40 degrees. R15 hands have no fingers, so the hands gesture from the wrist. The wand is held as `WandService` welds it, as for Scintara.

Every gesture is timed to the server. It starts when the server accepts the cast (`CastReply`), and the server fires the spell 0.2 s later, the spell's cast time. So the wand strikes at frame 6, and that keyframe carries a `Release` marker, where `EffectsController` flashes the wand tip in the spell's colour. A gesture keys only the arms, upper torso and head, at priority Action2, so the legs go on walking, sprinting or riding under it, and the head turns against the torso to keep looking ahead. Animations played on your own character show to every player.

The gestures work in both views:

- **Third person.** You turn to face the aim and hold that facing through the gesture.
- **Both views.** While any cast plays, a gesture or one of Scintara's, `EffectsController:Arms` tilts the arms about the shoulders toward the aim, by the shoulder joints' `C0`, so the wand strikes up or down at it.
- **First person.** The camera sits a stud above the shoulders, so the arms would play low at the bottom of the view. While a cast plays they are lifted 14 degrees and turned 8 degrees toward the middle of the view. Your forearms, hands and wand are always drawn there. The upper arms stay hidden, since a stud from the camera they would fill the view.

`--preview` renders three strips of four frames for each clip. `Cast<Motion>.png` is from the front right. `Cast<Motion>_third.png` is from the game's over-the-shoulder camera, closed in on the character. `Cast<Motion>_first.png` is from the first-person camera, with the arms lifted as in game and only the forearms, hands and wand drawn.

```bash
python tools/blender.py blender/animations/casting.py --preview
```

The script writes `CastAnimations.json` beside `CharacterAnimations.json`, and `tools/place_animations.py` reads both and writes each `Release` marker as a KeyframeMarker. Put the clips in the place like the others:

```bash
python tools/place_animations.py CastLash CastThrust CastHurl CastZap CastPull CastUplift CastChop CastLull CastWard CastDome CastSwirl CastMend CastTwist
```

## Brooms

`models/brooms.py` builds `Brooms.fbx`: four flying brooms, one primary and three with designs of their own. Each is 7 to 9 studs long, lies with its tip to the front and has its seat, the point on the shaft where a rider sits, on the origin of its own model.

| Broom | Design | Glow |
|---|---|---|
| **Ashwind**, the primary broom | The academy's own, issued to every first-year. A straight ash shaft that lifts a little at the brass-capped tip, a leather grip between brass collars, an arcane rune on each side of the collar, brass stirrups, and a classic flared tail of straw-brown twigs in three brass bands. | Arcane violet |
| **Swiftquill** | A racer. A long slim silverbirch shaft with a frost crystal held out in silver claws at the nose, glowing speed stripes, a low padded seat, swept silver stirrup fins, and a tight tail that tapers to a point between three stabiliser fins. | Frost blue |
| **Stoutbough** | A hauler. A thick knotted ironoak shaft with an iron cap and tow ring, a lantern hung under the tip, iron bands and rivets, a deep saddle with saddlebags, a plank footboard on iron struts, and a big round tail lashed with rope. | Lamplight |
| **Nightwing** | A wild one. A twisting blackthorn shaft wound with a vine and set with thorns, curling into a crook that cradles an ember gem, and pewter claws gripping a ragged fan of raven-dark twigs and feathers with smouldering tips. | Ember orange |

Each broom is a Model of up to five meshes, one per Roblox material: `Wood`, `Bristles` (Wood too, since Fabric darkens the straw), `Metal`, `Leather` and `Glow` (Neon, in the broom's colour). A broom is 7,000 to 12,500 triangles, most of them in its twigs. With `--preview` the script renders a lineup (`Brooms.png`), a side view of each (`Brooms_<name>.png`), Ashwind with a rider for scale (`Brooms_rider.png`) and an EEVEE picture of all four (`Brooms_picture.png`).

```bash
python tools/blender.py blender/models/brooms.py --preview
```

To put them in the game:

1. Import `Brooms.fbx` as in step 3. Insert Using Scene Position can be on or off; the script puts the brooms back where they belong.
2. Paste [place_brooms.lua](place_brooms.lua) into **View → Command Bar** and press Enter. It moves the four into `ReplicatedStorage.Brooms` and pivots each on its seat. It sets each mesh's material and the Glow colour, and makes the meshes massless and uncollidable, welded to the broom's `Wood`, its PrimaryPart. One weld to a rider then carries the whole broom.
3. Save the place. Running the script again changes nothing. After rebuilding the brooms, import the new file and run the script again: it replaces the old ones.

In game, F takes off and lands (`FlightService` on the server, `FlightController` on the client, stats in `src/shared/BroomData.lua`). The server welds a copy of your chosen broom 1.35 studs under your HumanoidRootPart, so you sit on its seat, and your client flies you there in that broom's own ride. Ashwind is every student's from their first wand. Stoutbough unlocks at level 6, Swiftquill at 12 and Nightwing at 18, and you choose among them in the Bag.

### Flying each broom

Each broom is flown in a looped ride of its own, made in `animations/character.py`:

| Clip | Loop | The ride |
|---|---|---|
| `BroomRideAshwind` | 2.4 s | A first-year's easy cruise. A comfortable lean with both hands on the grip, right ahead of left, knees in and feet in the brass stirrups. The body rocks gently side to side and bobs, and the head looks round, left and then right. |
| `BroomRideStoutbough` | 3.2 s | The hauler's slow roll. Sat deep in the saddle, one hand driving at the back of the grip and the other on the hip, elbow out, boots flat on the footboard. The whole body rocks forward and back with the heavy broom, and the head nods along. |
| `BroomRideSwiftquill` | 1.2 s | A racer's tuck. Chest down along the shaft, head up, both hands far forward on the bare birch with the elbows in, legs folded back onto the pegs and up on the toes, shaken by quick small tremors from the wind. |
| `BroomRideNightwing` | 1.6 s | Ridden like a bucking beast. Both hands clamped on the grip, the body rolls hard from side to side and twists with it, knees clamped round the thorny shaft. |

The broom is welded to the HumanoidRootPart, so it never moves in the rig's space. Each ride is written as the body's motion over one loop and keyed every 3 frames. At every key the script bends the gripping arms so the hands close on that broom's grip, and the legs so the feet stand on its stirrups, pegs or footboard (`fit`, a small least-squares solve). Each key's solve starts from the key before, and the loop is gone round twice, so an arm that could reach two ways keeps to one all the way round. The body sways while the hands and feet stay put, and the build stops if a hand or foot can't reach. The keys are joined by straight lines (`Linear` easing), which keeps the motion even. With `--preview`, each ride's strip shows the mannequin on its broom, read from `exports/Brooms.blend`.

`FlightController` plays `BroomRide<Broom>` for the broom you fly, falling back to `BroomRide`. It speeds the loop up as you go faster, from three quarters speed in a hover to one and a quarter flat out. Like the other clips, the rides play from their KeyframeSequences in Studio playtests and need publishing for a live game (see "Character animations").

### Dashing through the air

Flown at four fifths of the broom's top speed or more, a rider is dashing through the air. Their house's dash takes over from the ride, with a 0.3 s blend, until they slow below three fifths. Every house tucks low into the wind its own way, and the wind's quick shakes run through the head and shoulders on top:

| House | Loop | The dash |
|---|---|---|
| Emberclaw | 1.0 s | The charge. Head down like a ram and elbows flared, the rider drives forward twice a second as if spurring the broom on. |
| Stoneroot | 1.2 s | The brace. Low, square and still, elbows locked in and eyes level. Only a slow heave and a fine shudder in the shoulders. |
| Skyquill | 1.6 s | The glide. Flat like a diving hawk, the rider carves a long slow curve one way and back, keeping the head level as the body banks. |
| Nightfang | 1.2 s | The prowl. Low and coiled, the rider weaves like a serpent, hips one way and shoulders the other, head locked ahead. |

Each house's dash is fitted to every broom's grip and stirrups as the rides are, so there are sixteen clips, `BroomDash<House><Broom>`. They are keyed every 2 frames, fine enough for the shakes. A rider not yet sorted into a house keeps the ride.

Every client also draws the wind round each dashing rider, in the colour of the rider's house (`Config.Houses`), or arcane violet before sorting. It uses the dodge's Blender meshes, `ReplicatedStorage.VFX.DashVFX` (see "Dash effect"), so there is nothing more to import. The Streak's two ribbons wrap the rider and spin about the line of flight, trailing 12 studs behind. The Speed lines stream back past the rider and fade, and the Ring bursts behind them as the dash begins. With Reduced effects on, only a fainter streak shows.

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
  - The four brooms (`models/brooms.py`), hovering in a row south of the pad with each seat at a rider's height, tips to the north, and a mannequin on each one in that broom's own ride.
- **Animations.** Every clip (Walk, Sprint, the four Tumbles, BroomRide, each broom's ride and the Spellbook's opening) is kept in the file. To play one, select a rig and pick the clip in Blender's Action editor.
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
