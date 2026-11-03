-- Every sound the game plays. All of them come from the licensed libraries in Roblox's Creator Store (ProSoundEffects
-- sound effects, APM Music tracks), free to use in any experience. EffectsController and FlightController play the
-- effects; MusicController plays the music. Volume is the sound's own, Speed its PlaybackSpeed.
local S = {}

S.Effects = {
    -- Ward Shield, the glass ward (EffectsController:Ward).
    WardRaise = {Id = 9116409574, Volume = 0.55, Speed = 1.1},           -- Magic Swirling Tone 1: a spinning chime and sparkle
    WardCrack = {Id = 9114863345, Volume = 0.7, Speed = 1.25},           -- Ice Cubes Fall Dropping To Floor 2: a sharp rattling tinkle
    WardShatter = {Id = 9114592245, Volume = 1, Speed = 1},              -- Glass Breaks 3: breaks, hits and bounces, debris shards
    -- Scintara: the spark bolt and the spark lance.
    ScintaraCast = {Id = 9116275766, Volume = 0.45, Speed = 1.35},       -- Lightning Flashes Quick Electrical Bursts 10
    ScintaraHit = {Id = 9116275285, Volume = 0.55, Speed = 1.1},         -- Lightning Flashes Quick Electrical Bursts 4
    ScintaraLanceIgnite = {Id = 9116272379, Volume = 0.7, Speed = 1},    -- Lightning Flashes Quick Electrical Bursts 6
    ScintaraLanceHum = {Id = 9125636390, Volume = 0.5, Speed = 1.15},    -- Magic Glow Constant Arcing Zaps Electrical Hum 1
    ScintaraLanceFade = {Id = 9116418234, Volume = 0.35, Speed = 1.6},   -- Magic Tone Falling Shimmer Flanged 1
    -- Broom flight (FlightController).
    BroomTakeOff = {Id = 9125442578, Volume = 0.6, Speed = 1},           -- Cloth Whooshes Fast Whooshing Pass Bys Airy Hum 3
    BroomWind = {Id = 9125742262, Volume = 0.55, Speed = 1},             -- Plasma Trails Constant Airy Whooshing Windy 2
    BroomDash = {Id = 9114374050, Volume = 0.7, Speed = 1},              -- Fast Pass By Airy Whooshes Windy 10
    BroomLand = {Id = 9125442175, Volume = 0.55, Speed = 0.9},           -- Cloth Whooshes Fast Whooshes Rumbling Pass Bys 9
}

-- Music for each zone (Config.Zones, the player's Zone attribute), and for flying a broom anywhere.
S.Music = {
    Hollowmere = {Id = 1843199417, Volume = 0.3},    -- Village Fun
    Castle = {Id = 1848134067, Volume = 0.3},        -- The Magic Waltz B
    Grounds = {Id = 1845410144, Volume = 0.3},       -- Gifts Of Nature
    Whisperwood = {Id = 9039950721, Volume = 0.3},   -- Behind The Mirror
    Flying = {Id = 1838007177, Volume = 0.3},        -- Magic Carpet Ride (a 60)
}
S.Crossfade = 2.5   -- seconds from one track to the next

return S
