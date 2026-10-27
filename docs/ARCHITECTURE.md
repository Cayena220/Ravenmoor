# Architecture and extension points

The server loads named services in a fixed order, calls every `Init`, then starts
the runtime. Player loading begins last, after remotes, prompts and gameplay
handlers exist. Clients wait for replicated dependencies before initializing.

| Module | Owns |
|---|---|
| NetworkService | Remote creation, token-bucket rate limits, snapshots, notifications |
| PlayerDataService | Profile lifecycle, deep-copy saves, owned session locks, shutdown |
| ProgressionService | XP, attributes, skill tree points, learned spells, mastery, quest progress, personal house contribution |
| WandService | Wand case (grant, equip, discard, Oakhart commissions, boss drops) and the wand model in the player's hand |
| WorldService | Zone rules, anchor proximity, Waystones, day cycle, coarse movement checks |
| CombatService | Player states, target registry, damage/healing, shields, effects, diminishing returns, knockouts |
| SpellService | Cast authorization, equipped/learned gates, traveling projectiles, AoE/beam/utility handlers, spoken casting |
| MonsterService | Spawn budget, AI ticks, threat, boss phases, contribution rewards |
| ClassService | Per-player lesson tokens, gesture scoring, target ownership, completion and reward limits |
| DuelService | Consented match state, countdown, win/loss/draw, arena bounds, forfeits |
| InteractionService | NPC prompts, sorting, bank, shop, potion and tome use, chest openings |
| UIController | HUD, spellbook, skill tree, journal, bag with 3D wand previews, Wandery, sorting, menus, lesson input |
| InputController | Mouse/gamepad/touch bindings, aim, camera offset, menu control suppression |
| EffectsController | Local projectile pool, health labels, numbers, telegraphs, ward effects, quest marker |

Damage, mana costs, learning rewards and currency transactions are computed by
the server. Clients submit intent and aim. Prompt actions are checked for server
distance, player health and duel state even though Roblox already provides an
interaction prompt. Client-provided damage, target IDs, mastery values and class
completion claims are never accepted.

Monster animation is intentionally simple: anchored generated models move at a
5-Hz AI rate. Obstacle steering is suitable for this open prototype map. Replace
it with rigged pathfinding navigation for complex caves or indoor combat. There
is no historical hit rewind or production-grade movement anti-cheat.

Wands and skills share one modifier model. `WandData` (catalogue) and `SkillData`
(skill tree) list effects as `{Stat, Scope, Amount}`, for example `{"Damage", "Fire", 0.05}`.
`Formulas.Mods` sums the equipped wand and learned skills, and `Formulas.Power`,
`Cooldown`, `ManaCost`, `Duration` and `Stats` read the totals. Supported stats are
Damage, Cooldown, ManaCost, Duration (scoped by school or element, or All), plus Crit,
Shield, Heal, Health, Mana, Regen and Guard. A new wand wood or skill needs only a data
entry that uses these stats. `WandModel.Build` makes the 3D wand from parts. The server
welds it into the hand, and the bag draws an anchored copy in a ViewportFrame.

The village is built in `tools/build.py` from a small kit of part builders, with no assets:
- `timber_house(parent, name, x, z, facing, spec)` builds a house in a local frame whose door faces +Z, then turns it in quarter steps (`facing`). A spec sets footprint, storey heights, door, jetty, colors, sign text, windows per storey and optional features (`bay_window`, `columns`, `herb_planters`, `awnings`).
- Every house gets a 0.7-stud stone plinth (the height the NPCs stand on), framed plaster or stone walls, a WedgePart gable roof and a chimney.
- `road_trim` adds curbs, verges and paving bands over a road bed, with curb gaps where lanes join. `lamp`, `plaza`, `bench` and `planter` dress the roads and square.
- Trim is `CanCollide=false, CanQuery=false`, so monster steering, sight lines and spells only see the solid walls, plinths, curbs and roofs.
- Village variation uses its own seeded random stream (`VILLAGE_RNG`), so village changes never move forest trees or castle candles.
- Every structural colour comes from `tools/palette.py`, by family: castle and village stone, slate and metal, timber, a paving scale (road, plaza, path, worn track), ground and three foliage tones, and one warm `LAMPLIGHT`. Content colours, such as a shop's plaster or a house's colour, stay with their data.
- The village and the academy share one kit: `glazing` (window panes, some lit at night), `light` (a warm PointLight), `lamp` (the iron lamp post, with its arm along either axis), `tree` (trunk and three leafy canopies) and `sign` (lettering on a timber board). `build_academy` receives them as `kit`.
- Night lights are parts named in `Config.NightLights` (`Lit window`, `Lantern`). They are glass by day; WorldService turns them to Neon and switches on the lights inside them from 18:30 to 06:00.
- Shops keep their 28×26 footprints and door lines, so `Workspace.Markers` (NPC prompts) never need to move.

The 19 implemented spell IDs are data-driven. Future catalogue entries have
`Implemented = false` and are denied by the server. Add an actual handler, acquisition
path, tests and content before enabling one; simply increasing LevelCap is not enough.

The source plan's exact weekly House Cup, normalized ranked matches and full
commerce are not partially enabled here. Add dedicated cross-server systems for
them. Do not treat `Formulas.Elo` or the local house totals as finished matchmaking
or global standings.

Rendering checks here cover exported geometry and XML integrity, not the Roblox
engine. The native place must be opened and tested in Studio before release.
