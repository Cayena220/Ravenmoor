# Saving and test data

`Config.StudioSaves = false` is the default. Studio players receive fresh in-memory
profiles. This allows the downloaded place to run without API access. Stopping the
session resets progress; the Settings panel identifies this mode.

Published Roblox servers use `Wandbound_Alpha_v1` with keys `Player_<UserId>`.
One UpdateAsync record holds the whole data snapshot and a session lock. Locks
renew on a 60-second save cycle, expire after 180 seconds, and release on normal
leave. A stale server cannot overwrite a lock held by another server. If initial
loading fails, the live session is stopped instead of saving default data over an
unknown existing record. Prolonged save failures stop play before the lock expires.

The implementation is intentionally small and has not been verified against live
Roblox services. It is not a substitute for production persistence testing.

To test real persistence:

1. Publish a **separate private test experience** under your account.
2. Change its `DataStoreName` to a separate test namespace.
3. Set `StudioSaves = true` only in that test copy, and enable Studio API access in the experience's security settings if you want Studio to reach its DataStores.
4. Earn a small known amount of currency, learn a spell, and leave normally. Rejoin and compare house, level, XP, quest, loadout and inventory.
5. Test rapid reconnect, server shutdown, denied API access and throttled/failed writes. Monitor Output.

Studio uses the experience's actual DataStores when enabled. Keep your production
experience separate from the test copy. This build has no purchase receipts,
cross-server transactions, trading or teleport handoff. Add and test those flows
before implementing their corresponding features.

Schema version is `1`. Future schema changes should add explicit migrations; do
not delete or overwrite existing player keys as a migration shortcut.
