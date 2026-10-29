# Roblox Studio playtest

The automated checks passed outside Studio. Complete these engine checks on the
actual place before calling this build tested or publishing it to players.

## 1. First session

1. Open the `.rbxlx`, open Output, and press Play (F5).
2. Confirm the map, welcome panel and avatar appear. Output should show the server ready message and no red errors.
3. Get a wand from Oakhart. Confirm Scintara, Aegara and Glimmora appear in the spellbook.
4. Shoot a wall and a dummy. Projectiles should stop at walls, and an unlearned spell should not be available.
5. Choose a house at the Mirror; verify the sash, house name and perk. You can override the quiz's suggestion.
6. Walk around the sides of the Great Hall to the open classrooms behind it. Trace Quill's rune in the indicated direction. A poor trace should fail.
7. Pass the rune and shoot five teal lesson targets. Confirm the class reward is granted once, and expired/used targets cannot grant it again.
8. Complete five outdoor dummy hits, speak to Tobb, and defeat six Thornimps. Confirm the next quest and level 4 Flamara eligibility.
9. Learn Flamara from Rook. Equip it in slot 1; check mana, burn, cooldown and mastery progress.

## 1a. Village, roads and houses

1. Orientation: Whisperwood lies west (negative X) of the village and academy, and the dueling platform east of the academy. Each NPC stands in its shop doorway.
2. Roofs peak upward with gables on the short sides. If they form a V, set `ROOF_FLIP = True` in `tools/build.py`, rebuild with `--world-only` and sync with `--map`.
3. Each shop shows its sign above the door: OAKHART'S WANDS, VAULTKEEP BANK, HOLLOWMERE APOTHECARY, THREADS & THIMBLES. Text is readable and not mirrored.
4. Walk into every shop and cottage, and use the Oakhart, Bank and Apothecary prompts from outside the door.
5. Walk along and across curbs, lanes and garden paths without snagging. Dodge across the road and through a curb gap.
6. Thornimps still chase and attack you along the forest path. Spells are not blocked by curbs, lamp arms or window boxes.
7. Lamps hang their lanterns over the roads, and the plaza's Waystone, benches and planters are clear of the spawn pad.
8. Check frame rate in the village on a phone emulator. The expanded map is about 1,998 parts.

## 1b. Wands, bag and skill tree

1. Open the bag (B). Your first wand appears with a 3D preview, its two bonuses and an EQUIPPED tag. The wand in your hand matches the preview.
2. Talk to Oakhart again and commission a wand for 200 Gilders. It appears in the bag; Equip it and check the hand model and the spellbook's mana/cooldown numbers change to match its bonuses.
3. Discard needs a second click (Confirm?). The equipped wand cannot be discarded. Equipping is refused within 5 seconds of combat and during duels.
4. Fill the case to 10: further commissions are refused with a message.
5. Open Skills. You have one point per level above 1. Tier 2 skills unlock after 3 points in that school, tier 3 after 6. After "+1", the list stays at the same scroll position.
6. Bulwark and Renewing Spirit raise maximum health; Deep Reserves raises mana. Reset skills at the Restricted Shelf; a second reset the same day is refused.
7. Rejoin in a saving test experience: wands, the equipped wand and skills persist. A save from before this update converts its old wand into a Common wand in the bag.

## 1c. Named wands

Use the command bar to grant levels and items where noted. The wands' design sheets are in the Ravenmoor Wands design system.

1. Oakhart's odds list Common, Uncommon and Rare only; 200-Gilder commissions never give Heartwood, Vexfang or an Epic.
2. Complete The Rotbark Seal: Stormfork arrives in the bag. In the bag preview and in your hand it has a forked tip with two glowing caps, a spark between them and a brass coil. Bolts leave from the spark.
3. With Stormfork equipped, hit a Thornimp with Spark Bolt four times while a second Thornimp stands within 12 studs: a yellow arc jumps to it on the 4th hit for half the damage. Training dummies don't count. Swap wands and the count restarts.
4. Repeat step 2 with a full case: a notice says Oakhart will keep it, and the bag says so. Discard a wand, talk to Oakhart, and it is handed over.
5. At level 18 with 3 Heartwood and 600 Gilders, commission Hearthroot from Oakhart. It shows a leaf near the tip, roots behind the pommel and a pale-blue core window. Below level 18 or short of Heartwood, the button refuses with a reason and takes nothing.
6. With Hearthroot equipped, cast Mend on yourself below full health: you gain 6 mana and see a green burst. At full health, nothing is refunded. On an ally, a green beam runs back to you.
7. Bring 5 Widow's Bite trophies to Oakhart and forge Widow's Bite: a black wand with eight legs, silk wraps, purple metal and a magenta fang. It is visibly the longest wand in the bag.
8. With Widow's Bite equipped, root a monster with Stone Bind (it lasts about 1.7 s) and land critical hits: they are about a third bigger than critical hits on a free monster. Mother Vexweave is immune to roots, so it never applies to her.
9. Defeat Mother Vexweave several times: Widow's Bite drops about one time in ten, besides the trophy and the 35% Rare wand.
10. In a saving experience, a profile that finished The Rotbark Seal before this update receives Stormfork once, on its next visit to Oakhart.

## 2. Spell and movement coverage

- Aegara: absorbs damage and expires after two seconds.
- Glimmora: toggles light and drains mana while active.
- Resero: aim at one of the three chests, use the spell from within 35 studs; a repeat opening should be denied for five minutes.
- Vitara: self-heals when no eligible ally is aimed at; heals eligible allies outside a duel.
- Velocis: temporary movement boost; respects chill and root.
- Excido: obtain from Vey at level 6; silence prevents casting.
- Saxifra: root; Aerovanta: lift; Somnara: sleep that breaks on damage. A sleeping or stunned monster shows no attack circle; a lifted monster always lands back on the ground.
- Frigora then Tonitra: Shatter; Ruptara on a burning enemy: Combust. Discoveries appear in the journal.
- Speculo: reflect a duelist's first projectile or a Lanternwisp attack during its short window.
- Purgo: removes negative effects; Durassa: damage reduction and slow.
- Tractum: obtain at level 14 from the Restricted Shelf; pulls non-boss targets without crossing walls.
- Murallis: unlock after Vexweave at level 20; blocks incoming hostile duel projectiles and monster attacks against its owner.
- Shift dodge: stamina cost, short damage immunity, wall clearance, no dodging while rooted. Dodging through a monster is not cut short.
- Double-tap W, A, S or D: dodges forward, left, back or right as the camera sees it, and tumbles the same way. A slow second tap, or a different key, does nothing.
- Dying: return to the last touched Waystone after five seconds, without losing currency.
- Exact chat incantation and `/cast Flamara`: one cast per message, including in a multi-client session; normal chat stays filtered and visible normally.

## 3. Two-player session

Use Studio's server/client test controls with two players.

1. Shoot each other in the village: no player damage should be possible.
2. Both players stand near Vey. Send an invitation and accept it. Verify countdown, full resources and teleport to the platform.
3. Win a duel. The loser stops at one HP, both return, and only the winner receives the reward. Walk outside the arena or disconnect to test forfeits.
4. Invite a third player while a duel is active: a second match should not occupy the same platform.
5. Attack the same monster with both players. Each contributor in range should receive their own loot and XP. An uninvolved player should receive none. Stand between your partner and the monster: their bolts and beams pass through you and hit the monster. Melee monsters close in without circling, and an attack circle still hits a player standing behind another player.
6. Run simultaneous classes: a player must not advance by hitting someone else's lesson targets.
7. Check Vexweave's three phases with more than one contributor; after defeat no lingering attack should continue to damage players.

## 4. Economy and saving

- Buy and brew a Health Draught. Check exact ingredient/currency deductions and the shared cooldown.
- Deposit and withdraw. A negative, infinite or oversized amount must not change either balance.
- Attune and travel between Waystones. Undiscovered stones, insufficient funds and recent combat must prevent travel.
- Kill 15 enemies for the daily task. Further kills must not grant the daily reward twice.
- Follow `SAVING.md` in a separate private test experience. Rejoin with known XP, house, inventory, quest and loadout values. Check that values survive server shutdown.
- Test rapid reconnect and DataStore failure. A failed load must not create a blank live profile over an existing save.

## 5. Devices and publishing

- Use phone/tablet emulators and a real phone. Check portrait and landscape hotbars, jump/joystick clearance, scrolling, all menu buttons and gesture drawing.
- Use a physical gamepad. Check menu selection, gesture tracing without moving the avatar, casting, and restoring movement after closing a menu.
- Check StreamingEnabled on a slower device: distant landmarks, streamed enemy health labels, NPC prompts and returning to a Waystone.
- Profile a server with 15 active monsters and several simultaneous spell users. Inspect physics, script time and memory.
- Set experience title, description, avatar settings and player limit in your own Creator Dashboard. Complete Roblox's current publishing requirements there.

There is no automatic publishing, monetization, external telemetry or account
connection in this project. This place has not been published for you.

## Input, inventory and conversation regressions (requires Studio)

These engine checks have not been run by the cloud test suite.

1. Start a fresh Play session. Talk to Oakhart, ask for advice, then select Wands. Confirm the starter wand and three spells are awarded once. Glimmora occupies only slot 1; slots 2–4 remain free.
2. Use B → K → M to switch directly between bag, spells and map. Press the same key again to close. Type these letters in chat without opening menus.
3. Hold LMB or gamepad RT to repeat Scintara. Vary trigger pressure; casting should continue until release. Open a menu, focus chat, or switch away from the window while holding: casting must stop and require a fresh press.
4. Unlock the cursor with Ctrl and aim at a dummy away from screen center. The spell should follow the pointer. Relock to aim with the crosshair. Test with a controller plugged in while using the mouse; labels should follow the active input.
5. Assign spells using the spellbook. Confirm the selected slot highlights only after the server updates the profile, then cast with 1–4 or X/Y/B/RB. Ward means RMB/LT. Check Shift dodges without enabling Roblox shift lock.
6. In a multiplayer test, cast through at least five friendly players toward a monster. Bolts should reach the monster. Cast while facing a nearby wall; bolts should not start on its far side.
7. Equip and discard wands, including identical copies. Rapidly repeat a confirmed discard under simulated network latency: only the selected wand should be removed. The equipped wand remains protected.
8. Materials in the bag are informational. Use a Health Draught at full health: quantity should remain unchanged. Take damage and use it again: one is consumed, healing runs over four seconds, and the shared cooldown applies.
9. Talk to Tobb, each professor, the banker, apothecary and duelmaster. Check advice, quest guidance, and the service choice. Walk out of interaction range before selecting a service: no transaction or lesson should start. Verify first-wand, sorting, lesson and Tobb quest progression still completes.
10. Reopen the updated place and start Play several times. The welcome panel and HUD must appear every time; Output must not report `Controllers is not a valid member of PlayerScripts`. Open the bag before and after receiving your first wand; check both the empty state and the wand preview.
11. Hold gamepad X beside each NPC: it should open the conversation without casting slot 1. Leave the prompt and check X casts again. Keyboard 1 should still cast beside an NPC.
12. Buy and brew Health Draughts, then check bag quantities and consumed ingredients. Use a tome below its required level (no consumption), at its required level (learns and consumes one), and after learning the spell (no further consumption).
13. Check the Restricted Shelf, Mirror sorting, and all three Waystone menus. Verify Library and Duelmaster spell unlocks at their required levels, and that deposits/withdrawals update the carried and banked balances in the bag.

## Academy campus

Walk from the Main Gate up both flights of the Grand Stair, across both bridges into the classroom wings, down each wing stair, through the Keep into the Great Hall, down the back stair and up the stair of every house quarter. The stairs use 1-stud steps: no step should need a jump. Check that the cameras stay usable inside the halls and on the bridges, and that the stair string walls, gables and spires slope the right way. Test a lesson in each classroom, the Mirror, the restricted shelf and a duel from the Duelmaster's new spot south of the arena. Check night lighting and mobile performance. These engine checks remain unrun here; see `ACADEMY-DESIGN.md` for the layout.
