--[[ Set up the imported flying brooms (blender/models/brooms.py, see blender/README.md, "Brooms").

Import blender/exports/Brooms.fbx, then paste this whole file into View > Command Bar and press Enter. Running it
again changes nothing. It moves the four brooms (Ashwind, the primary broom, then Swiftquill, Stoutbough and
Nightwing) into ReplicatedStorage.Brooms, where the game can clone one for a rider, and for each:
  * pivots it on its seat, the point on the shaft where a rider sits, and stands it on the origin with its tip to
    the front (-Z);
  * drops Blender's .001 name suffixes, so its meshes are Wood, Bristles, Metal, Leather and Glow, sets each one's
    material, turns it white so the vertex colours show true, and gives Glow its Neon colour;
  * makes the meshes massless and uncollidable and welds them to Wood, its PrimaryPart, so one weld to a rider
    carries the whole broom.
]]
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ChangeHistoryService = game:GetService("ChangeHistoryService")

local SPACING = 3.2   -- brooms.py lays the seats out this far apart along Blender X, which is Roblox -X
local BROOMS = {
    {Name = "Ashwind", Glow = Color3.fromRGB(194, 163, 255)},
    {Name = "Swiftquill", Glow = Color3.fromRGB(140, 220, 255)},
    {Name = "Stoutbough", Glow = Color3.fromRGB(255, 196, 128)},
    {Name = "Nightwing", Glow = Color3.fromRGB(255, 140, 64)},
}
-- Fabric would darken the straw; the twigs are wood anyway.
local MATERIALS = {Wood = Enum.Material.Wood, Bristles = Enum.Material.Wood, Metal = Enum.Material.Metal,
    Leather = Enum.Material.Leather, Glow = Enum.Material.Neon}
local WHITE = Color3.new(1, 1, 1)   -- Studio multiplies a mesh's vertex colours by its part's Color

local function setUp(broom, glow)
    for _, item in ipairs(broom:GetDescendants()) do
        local base = (item:IsA("BasePart") or item:IsA("Model")) and item.Name:match("^(.-)%.%d%d%d$")
        if base then item.Name = base end
    end
    local wood
    for _, part in ipairs(broom:GetDescendants()) do
        if part:IsA("MeshPart") then
            part.Parent = broom   -- out of any model the importer nested it in
            part.Material = MATERIALS[part.Name] or part.Material
            part.Color = part.Name == "Glow" and glow or WHITE
            part.Anchored, part.Massless, part.CanCollide, part.CanQuery, part.CanTouch = false, true, false, false, false
            part.CastShadow = part.Name ~= "Glow"
            if part.Name == "Wood" then wood = part end
        end
    end
    for _, child in ipairs(broom:GetChildren()) do
        if child:IsA("Model") and not child:FindFirstChildWhichIsA("BasePart", true) then child:Destroy() end
    end
    assert(wood, broom.Name .. " has no Wood mesh")
    broom.PrimaryPart = wood
    for _, part in ipairs(broom:GetChildren()) do
        if part:IsA("MeshPart") and part ~= wood then
            local weld = part:FindFirstChild("ToWood") or Instance.new("WeldConstraint")
            weld.Name, weld.Part0, weld.Part1, weld.Parent = "ToWood", wood, part, part
        end
    end
end

-- The imported model: a Model named Brooms holding the four, wherever the importer put it (it may wrap it in a model
-- of the same name). Parents come before their children here, so the first one found is the outermost.
local imported
for _, item in ipairs(workspace:GetDescendants()) do
    if item:IsA("Model") and item.Name == "Brooms" and item:FindFirstChild("Ashwind", true) then imported = item; break end
end
local folder = ReplicatedStorage:FindFirstChild("Brooms")
assert(imported or folder, "Import blender/exports/Brooms.fbx into Workspace first")

local recording = ChangeHistoryService:TryBeginRecording("Place brooms")
if not folder then
    folder = Instance.new("Folder"); folder.Name = "Brooms"; folder.Parent = ReplicatedStorage
end
if imported then
    -- The importer turns the meshes' points into Roblox's axes, so a mesh lies as brooms.py made it when the part
    -- is unturned; turn the whole import about its pivot until it is. The pivot is the scene's origin, wherever
    -- the importer dropped it: stand it on the world origin, so each seat is where brooms.py put it.
    local pivot, mesh = imported:GetPivot(), imported:FindFirstChildWhichIsA("MeshPart", true)
    imported:PivotTo(CFrame.new(pivot.Position) * mesh.CFrame.Rotation:Inverse() * pivot.Rotation)
    imported:PivotTo(imported:GetPivot().Rotation)
    for i, spec in ipairs(BROOMS) do
        local broom = imported:FindFirstChild(spec.Name, true)
        if broom then
            setUp(broom, spec.Glow)
            -- A model with a PrimaryPart pivots on that part's pivot, which the importer also put on the scene's
            -- origin; move it to the seat.
            broom.PrimaryPart.PivotOffset = broom.PrimaryPart.CFrame:Inverse() * CFrame.new(-SPACING * (i - 1), 0, 0)
            broom:PivotTo(CFrame.new())
            local old = folder:FindFirstChild(spec.Name)
            if old then old:Destroy() end
            broom.Parent = folder
        end
    end
    imported:Destroy()
end
local report = {}
for _, spec in ipairs(BROOMS) do
    local broom = folder:FindFirstChild(spec.Name)
    if broom then
        setUp(broom, spec.Glow)
        local size, meshes = broom:GetExtentsSize(), {}
        for _, part in ipairs(broom:GetChildren()) do if part:IsA("MeshPart") then table.insert(meshes, part.Name) end end
        table.sort(meshes)
        table.insert(report, string.format("%s: %s; %.1f x %.1f x %.1f studs", spec.Name, table.concat(meshes, ", "),
            size.X, size.Y, size.Z))
    else
        table.insert(report, spec.Name .. ": MISSING")
    end
end
if recording then ChangeHistoryService:FinishRecording(recording, Enum.FinishRecordingOperation.Commit) end
local text = "ReplicatedStorage.Brooms\n" .. table.concat(report, "\n")
print(text)
return text
