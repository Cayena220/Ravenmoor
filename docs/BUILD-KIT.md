# Ravenmoor Academy build kit

The design reference for the academy remodel, copied from the Ravenmoor Academy design canvas: https://claude.ai/artifact/LApun141Xop1kQk68HfPpx (four artboards: castle elevation, site plan, Great Hall section and build kit). **Superseded for layout:** the academy is now built from the exterior remodel canvas (https://claude.ai/artifact/9WsYqy3tTPN4NaBVxsGduk); see [ACADEMY-DESIGN.md](ACADEMY-DESIGN.md). Its proportions, materials, colours and lighting below still apply.

## Castle elevation at dusk

**Ravenmoor Academy, remodelled.** A gothic castle school on a moorland crag above the loch, seen from the south at dusk. Every tower is built from plain parts and scaled to a 5.5-stud player.

| Scale | Footprint | Tallest |
|---|---|---|
| 1 stud ≈ 0.3 m | 430 × 300 studs | Rookery Tower, 220 studs |

1. **Moor Viaduct and Gatehouse.** You arrive on foot over five stone arches, 130 studs long, and pass between two drum turrets.
2. **Great Hall.** 140 × 46 studs inside. Eight lancet bays between stepped buttresses, a steep slate roof and a copper flèche.
3. **Clock Tower.** A square tower at the hall's east end, over Clock Court. Lit dial, louvred belfry, slate spire.
4. **Rookery Tower.** The tallest tower, 220 studs to the finial. Its copper spire has weathered green, and ravens nest in the lucarnes.
5. **Library Wing.** A three-storey range with five dormers. About a third of its windows are lit; a fully lit castle looks fake.
6. **House Towers.** Four dormitory towers, one per house, around their own court. Two face the loch; two stand behind the library.
7. **Starwatch Tower.** A slim astronomy tower on the east cliff, with an open arcade under a copper dome 190 studs up.
8. **Boathouse and Loch Stair.** A switchback stair cut into the crag drops to a boathouse and a jetty on the water.
9. **Glasshouses and Whisperwood.** Herb glasshouses on the east moor, where the trail into the Whisperwood starts.

## Site plan

The academy sits on a crag with a gorge to the west and the loch to the south. You arrive over the viaduct and every daily walk stays under 25 seconds.

Plan scale: 1.2 px per stud, north up. Walk speed: 16 studs per second.

### Arrival walk

| Step | Route | Distance | Time |
|---|---|---|---|
| 1 | Viaduct to Gatehouse | 130 studs | 8 s |
| 2 | Gatehouse to the court passage | 100 studs | 6 s |
| 3 | Across Clock Court | 60 studs | 4 s |
| 4 | Up to the Great Hall door | 30 studs | 2 s |

320 studs and about 20 seconds from the viaduct to your seat. The longest daily walk, House Court to the Great Hall, is about 210 studs (13 s).

### Zones

| Zone | Places |
|---|---|
| Arrival | Moor Viaduct, Gatehouse, Viaduct Court |
| Teaching | Great Hall, Clock Court, classrooms, Library, Starwatch Tower |
| Living | House Court, four house towers, dormitory ranges |
| Grounds | North terraces, practice yard, glasshouses, loch stair, boathouse, Whisperwood edge |

### Heights above the loch

| Feature | Height |
|---|---|
| Crag top | +60 studs |
| Great Hall ridge | +165 studs |
| Clock Tower spire | +240 studs |
| Starwatch dome | +245 studs |
| Rookery finial | +285 studs |

### Build order

1. Terrain first: the crag, the gorge and the loch.
2. Grey blocks for every building at full size. Walk them at speed 16 before adding detail.
3. One bay module per building type, copied along each range.
4. Roofs, spires and parapets.
5. The lighting pass from the build kit.
6. Interiors, starting with the Great Hall.

## Great Hall

A cross-section through one bay, looking at the high table. The hall stands on an undercroft so its windows clear the courtyard roofs.

| | Specification |
|---|---|
| Inside | 140 × 46 studs. 40 to the wall plate, 73 to the ridge. |
| Bays | Eight bays of 17.5 studs. One lancet per bay, 6 × 26 studs, sill 10 above the floor, set in a 2-stud reveal. |
| Roof | A hammerbeam truss on each of the nine buttress lines, collar beam 58 studs up. Carved pendants hang 2 studs below each hammer beam. |
| End window | 17 × 40 studs over the high table, with three mullions and a round tracery eye. At night it shows moonlight, not lamplight. |
| Floor and dais | Slate flags, 4 × 4, in two tones. The dais rises 2 studs and runs 12 deep. |
| Seating | Four house tables, 100 × 3.5 studs, with a bench on each side. The high table crosses the dais. |
| Light | Six iron chandeliers on chains from the collar beams. PointLight range 28, brightness 1.4, colour 255, 178, 110. Turn CastShadow off on the candle parts. |
| Undercroft | 24 studs high and rib-vaulted, for kitchens and stores. |

Section labels: slate roof, 52°. Hammerbeam truss on every buttress line. House banners, 4 × 20 studs. Lancet, 6 × 26, in a deep reveal. Iron chandeliers, six in all. Player, 5.5 studs. Undercroft kitchens and stores. Heights: ridge +73, wall plate +40, hall floor 0, undercroft −24; 46 studs inside.

**Bay module.** Build one bay as a model: buttress, wall panel, lancet, parapet and truss. Copy it eight times along the hall. Only the two end walls are built by hand.

## Build kit

Proportions, materials and lighting for building the academy in Studio from plain parts: no meshes, decals or asset IDs. Most of the realism comes from depth, varied stone and the lighting pass.

### Scale and proportion, in studs

| Element | Size |
|---|---|
| Player | 5.5 tall |
| Everyday door | 6 × 10 |
| Great door | 12 × 20 |
| Classroom storey | 16 floor to floor |
| Grand room | 24 or more |
| Corridor | 12 wide |
| Stair step | 0.8 rise, 1.6 tread |
| Outer wall | 3 thick |
| Inner wall | 1.5 thick |
| Lancet window | 3 × 10, in a 2-stud reveal |
| Battlements | 3 × 3 merlons, 2 gaps |
| Roof pitch | 52° to 60° |

### Tower kit

| Tower | Size |
|---|---|
| Drum tower | Ø 22, 70 tall, cone 35 |
| Bell tower | 24 × 24, 72 tall, spire 36 |
| Stair turret | Ø 10, 60 tall, cone 16 |

### Materials and colours

| Use | Material | Colour (RGB) | Notes |
|---|---|---|---|
| Wall stone | Slate | 118, 114, 104 | |
| Weathered stone | Slate | 96, 94, 88 | About 1 block in 4 |
| Dressed trim | Limestone | 176, 166, 142 | Window surrounds, corners, string courses |
| Plinth and paving | Cobblestone | 92, 90, 84 | |
| Roofs | Slate | 54, 60, 68 | |
| Spires and flèches | CorrodedMetal | 86, 124, 112 | Copper gone green |
| Timber | WoodPlanks | 88, 60, 40 | Doors, trusses, bridges |
| Lit window glass | Glass | 255, 196, 128 | Transparency 0.3 |
| Crag | Basalt terrain | 62, 60, 58 | |
| Moor and heather | Grass terrain | 96, 104, 64 | Heather patches in 112, 86, 108 |

Build each wall from blocks 4 to 8 studs long rather than one big part, so the two stone tones and the trim can break it up.

### Lighting pass

| Lighting | Value |
|---|---|
| `Technology` | Future |
| `ClockTime` | 19.2 dusk, 15 by day |
| `Brightness` | 2 |
| `Ambient` | 38, 42, 50 |
| `OutdoorAmbient` | 92, 98, 112 |
| `ShadowSoftness` | 0.2 |
| `EnvironmentDiffuseScale` | 1 |
| `EnvironmentSpecularScale` | 1 |

| Atmosphere | Value |
|---|---|
| `Density` | 0.36 |
| `Offset` | 0.2 |
| `Haze` | 1.8 |
| `Glare` | 0.3 |
| `Color` | 199, 191, 182 |
| `Decay` | 96, 86, 100 |

| Post-processing | Value |
|---|---|
| `ColorCorrection.Saturation` | -0.12 |
| `ColorCorrection.Contrast` | 0.08 |
| `Bloom` | 0.5 · size 24 · threshold 1.8 |

| Window lights | Value |
|---|---|
| `SurfaceLight` | On the glass, facing in |
| `Brightness` · `Range` | 1.2 · 14 |
| `Color` | 255, 178, 110 |

### Six rules for realism

1. **Give everything depth.** Set every window and door 2 studs into the wall. No flat face runs longer than 16 studs without a buttress, string course or setback.
2. **Vary the stone.** Mix two close stone tones with about 1 weathered block in 4. Keep a darker plinth at the base and lighter trim at the edges.
3. **Keep roofs steep.** Pitch roofs 52° to 60°, overhang the eaves by 1.5 studs and cap every ridge.
4. **Stretch the verticals.** Make towers at least 3 times as tall as they are wide, with spires 1.5 to 2 times the tower's width.
5. **Light it unevenly.** At night light about 1 window in 3 with warm glass. Leave the rest dark, and let the end windows show moonlight.
6. **Build once, copy often.** Model one bay and copy it along each range. Turn CastShadow and CanCollide off on small trim, and stream each tower as its own model.

## Where the build differs

The campus layout replaced this castle plan; [ACADEMY-DESIGN.md](ACADEMY-DESIGN.md) lists how the build differs from the newer concept. The lighting pass above is still not applied: the place keeps its own Lighting settings, which `EffectsController` tweens by zone. Recent Roblox versions also replace `Technology` with `LightingStyle`, so check that setting in Studio before applying the table.
