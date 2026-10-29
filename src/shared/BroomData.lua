-- Flying brooms: the models come from blender/models/brooms.py and sit in ReplicatedStorage.Brooms
-- (blender/place_brooms.lua). Every student with a wand flies Ashwind; the others unlock with level.
-- Speed is studs a second flat out, Climb studs a second straight up or down, and Handling how quickly the
-- broom answers the stick (higher is snappier).
local B = {Default = "Ashwind",
    Ceiling = 180,          -- no climbing above this height; FlightService grounds riders 25 studs over it
    CombatLockout = 6,      -- seconds after dealing or taking damage before you can take off
    ToggleCooldown = 1.5,   -- seconds between taking off and landing
    SeatDrop = 1.35}        -- the broom's seat sits this far under the rider's HumanoidRootPart
B.Brooms = {
    Ashwind = {Title = "Ashwind", Level = 1, Speed = 40, Climb = 20, Handling = 6,
        Note = "The academy's own broom, issued with your wand: steady and forgiving."},
    Stoutbough = {Title = "Stoutbough", Level = 6, Speed = 36, Climb = 26, Handling = 8,
        Note = "A hauler with a saddle and a lantern: slower, but it climbs hard and holds a hover."},
    Swiftquill = {Title = "Swiftquill", Level = 12, Speed = 60, Climb = 18, Handling = 4,
        Note = "A racer: the fastest broom in a straight line, wide in the turns."},
    Nightwing = {Title = "Nightwing", Level = 18, Speed = 52, Climb = 30, Handling = 9,
        Note = "A wild blackthorn broom: quick, sharp and eager to climb."},
}
B.Order = {"Ashwind", "Stoutbough", "Swiftquill", "Nightwing"}
function B.Unlocked(data, id)
    local broom = B.Brooms[id]
    return broom ~= nil and (data.Level or 1) >= broom.Level
end
-- A saved broom that is unknown or not yet earned falls back to Ashwind.
function B.Sanitize(data)
    if type(data.Broom) ~= "string" or not B.Unlocked(data, data.Broom) then data.Broom = B.Default end
end
function B.Stats(id)
    local broom = B.Brooms[id]
    return string.format("Speed %d · Climb %d · Handling %d", broom.Speed, broom.Climb, broom.Handling)
end
return B
