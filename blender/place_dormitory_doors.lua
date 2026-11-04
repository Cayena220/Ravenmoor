--[[ Doors between each house's common room and its dormitories (see blender/README.md, "Dormitory doors").

The four houses (blender/models/*_house.py) keep their bedrooms in two residential wings either side of the common
room, on a ground and an upper floor, but the models give the wings no doorway and no stair. These doors stand in for
them; WorldService.StartPortals gives each one a prompt that takes a student through:
  * on each side wall of the common room, "Go to the dormitory" leads to that wing's ground floor, and a door there
    leads back;
  * at the wing's far end, "Go upstairs" and "Go downstairs" join its two floors.

Each house's numbers are in its builder's own studs: its floors' tops, the faces of the common room's side wall, of
the wing's inner wall and of its far end wall (distance from the house's centre line), and the depth along the house
where each pair of doors stands, chosen clear of beds, desks, the hall's furniture, windows and corner towers.
Skyquill's reading rotunda is lined with bookcases, so its doors stand in the entrance hall in front of it, on the
side walls between the front doors and the rotunda. integrate_house_quarters.py
stood each house in WorldPlan at `anchor`, a quarter turn either way and a scale of .78; export_worldplan_game.py
turns WorldPlan's (x, y, z) into Roblox's (-x, z, y).

Paste into the Command Bar (or require it) in Edit mode. It rebuilds workspace.DormitoryDoors as one undoable change,
stands each door on the floor found under it, and reports each door with anything in the way of the spot in front of
it or a missing wall behind it.
]]
local ChangeHistoryService = game:GetService("ChangeHistoryService")

local SCALE = 0.78
local HOUSES = {
    {name = "EmberClaw", anchor = {180, -730}, turn = -1, floors = {5.225, 19.275}, hall = 17.33, inner = 18.675,
        outer = 59.33, hallDepth = 33, wingDepth = 18.8, stairDepth = 18.8, wood = Color3.fromRGB(92, 56, 34), trim = Color3.fromRGB(150, 28, 32)},
    {name = "Stoneroot", anchor = {180, -880}, turn = -1, floors = {5.3, 22.2}, hall = 22.35, inner = 23.65,
        outer = 64.35, hallDepth = 36, wingDepth = 43, stairDepth = 37, wood = Color3.fromRGB(96, 68, 40), trim = Color3.fromRGB(196, 140, 52)},
    {name = "Skyquill", anchor = {-260, -730}, turn = 1, floors = {5.175, 23.175}, hall = 12.35, inner = 22.65,
        outer = 67.35, hallDepth = -11.5, wingDepth = 10, stairDepth = 14, wood = Color3.fromRGB(38, 62, 120), trim = Color3.fromRGB(200, 206, 214)},
    {name = "Nightfang", anchor = {-260, -880}, turn = 1, floors = {5.4, 23.5}, hall = 22.3, inner = 25.68,
        outer = 63.3, hallDepth = 28, wingDepth = 52, stairDepth = 33, wood = Color3.fromRGB(28, 78, 58), trim = Color3.fromRGB(200, 206, 214)},
}
local DOOR = Vector3.new(4.6, 8, 0.3)   -- width, height, thickness
local STAND = 2.6                        -- builder studs from a wall to where a student stands at its door

local function at(house, x, y, z)
    local ax, ay = house.anchor[1], house.anchor[2]
    if house.turn < 0 then return Vector3.new(-ax - SCALE * y, 0.4 + SCALE * z, ay - SCALE * x) end
    return Vector3.new(-ax + SCALE * y, 0.4 + SCALE * z, ay + SCALE * x)
end

local rays = RaycastParams.new()
rays.FilterType = Enum.RaycastFilterType.Include
rays.FilterDescendantsInstances = {workspace.Map}
local overlap = OverlapParams.new()
overlap.FilterType = Enum.RaycastFilterType.Include
overlap.FilterDescendantsInstances = {workspace.Map}
overlap.RespectCanCollide = true
-- A student-sized box tested against the map's collision shapes (bounding boxes would take in whole merged meshes).
local probe = Instance.new("Part")
probe.Size, probe.Anchored, probe.CanCollide, probe.CanQuery, probe.Transparency = Vector3.new(2.2, 5.6, 2.2), true, false, false, 1

-- A door's spot: where a student stands at it (on the floor found there) and where the wall behind it is. `into` is
-- the way into the room from the wall: toward the house's centre line (-1), or, for a wing's inner wall, away (1).
local function spot(house, side, face, into, depth, floor, warnings, label)
    local stand = at(house, side * (face + into * STAND), depth, floor)
    local wall = at(house, side * face, depth, floor)
    local hit = workspace:Raycast(stand + Vector3.new(0, 4, 0), Vector3.new(0, -8, 0), rays)
    if hit then
        stand, wall = Vector3.new(stand.X, hit.Position.Y, stand.Z), Vector3.new(wall.X, hit.Position.Y, wall.Z)
    else
        table.insert(warnings, label .. ": no floor found")
    end
    probe.CFrame = CFrame.new(stand + Vector3.new(0, 3.2, 0)); probe.Parent = workspace
    local inWay = workspace:GetPartsInPart(probe, overlap)
    probe.Parent = nil
    if #inWay > 0 then table.insert(warnings, label .. ": " .. inWay[1].Name .. " stands where a student would") end
    local behind = workspace:Raycast(stand + Vector3.new(0, 3, 0), (wall - stand).Unit * (STAND * SCALE + 1.5), rays)
    if not behind then table.insert(warnings, label .. ": no wall behind the door") end
    return {stand = stand, wall = wall}
end

-- A student arriving at a door stands in front of it, facing into the room.
local function arrival(s)
    local from = s.stand + Vector3.new(0, 3, 0)
    return CFrame.lookAt(from, from + (s.stand - s.wall) * Vector3.new(1, 0, 1))
end

local function door(folder, house, name, action, object, here, there)
    local out = (here.stand - here.wall) * Vector3.new(1, 0, 1)
    local centre = here.wall + out.Unit * (DOOR.Z / 2 + 0.05) + Vector3.new(0, DOOR.Y / 2, 0)
    local slab = Instance.new("Part")
    slab.Name = name
    slab.Size = DOOR
    slab.CFrame = CFrame.lookAt(centre, centre + out)
    slab.Material, slab.Color = Enum.Material.WoodPlanks, house.wood
    slab.Anchored, slab.CanCollide, slab.CanTouch, slab.CastShadow = true, false, false, false
    slab:SetAttribute("ActionText", action)
    slab:SetAttribute("ObjectText", object)
    for _, piece in ipairs({
        {"Lintel", Vector3.new(DOOR.X + 0.6, 0.5, 0.2), CFrame.new(0, DOOR.Y / 2 + 0.25, -0.05), house.trim, Enum.Material.Metal},
        {"Band", Vector3.new(DOOR.X, 0.25, 0.08), CFrame.new(0, 1.2, -0.18), house.trim, Enum.Material.Metal},
        {"Handle", Vector3.new(0.25, 0.9, 0.25), CFrame.new(DOOR.X / 2 - 0.6, -0.4, -0.3), Color3.fromRGB(196, 160, 74), Enum.Material.Metal},
    }) do
        local p = Instance.new("Part")
        p.Name, p.Size, p.CFrame, p.Color, p.Material = piece[1], piece[2], slab.CFrame * piece[3], piece[4], piece[5]
        p.Anchored, p.CanCollide, p.CanTouch, p.CanQuery, p.CastShadow = true, false, false, false, false
        p.Parent = slab
    end
    local destination = Instance.new("CFrameValue")
    destination.Name = "Destination"
    destination.Value = arrival(there)
    destination.Parent = slab
    slab.Parent = folder
end

return (function()
    local recording = ChangeHistoryService:TryBeginRecording("Place the dormitory doors")
    local old = workspace:FindFirstChild("DormitoryDoors")
    if old then old:Destroy() end
    local folder = Instance.new("Folder")
    folder.Name = "DormitoryDoors"
    local warnings, count = {}, 0
    for _, house in ipairs(HOUSES) do
        for _, side in ipairs({-1, 1}) do
            local centre = at(house, 0, house.hallDepth, house.floors[1])
            local wing = at(house, side * house.outer, house.hallDepth, house.floors[1])
            local label = house.name .. " " .. (wing.Z < centre.Z and "north" or "south") .. " wing"
            local hall = spot(house, side, house.hall, -1, house.hallDepth, house.floors[1], warnings, label .. ", common room door")
            local back = spot(house, side, house.inner, 1, house.wingDepth, house.floors[1], warnings, label .. ", door back")
            local up = spot(house, side, house.outer, -1, house.stairDepth, house.floors[1], warnings, label .. ", stairs up")
            local down = spot(house, side, house.outer, -1, house.stairDepth, house.floors[2], warnings, label .. ", stairs down")
            door(folder, house, label .. ": to the dormitory", "Go to the dormitory", house.name .. " dormitory", hall, back)
            door(folder, house, label .. ": to the common room", "Back to the common room", house.name .. " common room", back, hall)
            door(folder, house, label .. ": upstairs", "Go upstairs", house.name .. " dormitory", up, down)
            door(folder, house, label .. ": downstairs", "Go downstairs", house.name .. " dormitory", down, up)
            count += 4
        end
    end
    probe:Destroy()
    folder.Parent = workspace
    if recording then ChangeHistoryService:FinishRecording(recording, Enum.FinishRecordingOperation.Commit) end
    return string.format("Placed %d dormitory doors.%s", count,
        #warnings > 0 and "\n  " .. table.concat(warnings, "\n  ") or " Every spot has floor, room to stand and a wall.")
end)()
