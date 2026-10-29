--[[ Set up the imported Hollowmere remodel (blender/models/hollowmere.py, see blender/README.md, "Hollowmere, remodelled").

Import blender/exports/Hollowmere.fbx with Insert Using Scene Position on, then paste this whole file into View >
Command Bar and press Enter. Run it again after every tools/sync_scripts.py --map, which brings the part village back
into view; running it twice changes nothing. It:
  * puts the model back where hollowmere.py made it, if it was imported without scene position, and moves it into
    Workspace.Scenery, out of Workspace.Map, so a map sync leaves it alone;
  * hides the map's part-built houses, street furniture, dock, ferry and village road lamps under it. It keeps their
    collision, doorways and lights, so players walk into the shops as before, the night lamps still shine and the
    checks in tools/validate.py still find the walls, while the meshes show the detail;
  * drops Blender's .001 name suffixes, anchors every mesh, leaves it uncollidable and turns it white, so the vertex
    colours show true. The windows become glass: Lit window in lamplight colour, which WorldService turns to Neon
    after dark, Window glass, and Display glass at Transparency 0.45 as on the map.
]]
local ChangeHistoryService = game:GetService("ChangeHistoryService")

local WHITE = Color3.new(1, 1, 1)                 -- Studio multiplies a mesh's vertex colours by its part's Color
local LAMPLIGHT = Color3.fromRGB(255, 196, 128)   -- Neon glows in the part's Color, as the map's lit windows do
local GROUND = {["Plaza tile"] = true, ["Plaza border"] = true, ["Shop lane"] = true, ["Garden path"] = true}
local LAMPS_FROM_Z = 60                           -- the map's road lamps from here south are the village's

-- The imported village: a Model named Hollowmere holding meshes, beside (not inside) Workspace.Map.
local function imported()
    for _, root in ipairs({workspace:FindFirstChild("Scenery"), workspace}) do
        for _, model in ipairs(root and root:GetChildren() or {}) do
            if model.Name == "Hollowmere" and model:IsA("Model") and model:FindFirstChildWhichIsA("MeshPart", true) then return model end
        end
    end
end

local remodel = imported()
assert(remodel, "Import blender/exports/Hollowmere.fbx into Workspace first (Insert Using Scene Position)")
local map = workspace:FindFirstChild("Map")
assert(map and map:FindFirstChild("Hollowmere") and map:FindFirstChild("Lamps"), "Workspace.Map's Hollowmere or Lamps is missing")
local recording = ChangeHistoryService:TryBeginRecording("Place Hollowmere")
-- The importer keeps the scene's origin as the model's pivot. Without Insert Using Scene Position it drops that pivot
-- where the camera looks, so stand it back on the origin, and the village over the part one.
remodel:PivotTo(CFrame.new())
local scenery = workspace:FindFirstChild("Scenery") or Instance.new("Model")
scenery.Name, scenery.ModelStreamingMode = "Scenery", Enum.ModelStreamingMode.Persistent
scenery.Parent = workspace
remodel.Parent = scenery

local meshes, windows = 0, 0
for _, item in ipairs(remodel:GetDescendants()) do
    local base = (item:IsA("BasePart") or item:IsA("Model")) and item.Name:match("^(.-)%.%d%d%d$")
    if base then item.Name = base end
    if item:IsA("MeshPart") then
        item.Anchored, item.CanCollide, item.CanTouch, item.CanQuery, item.CastShadow = true, false, false, false, true
        item.Color, item.Material, item.Transparency = WHITE, Enum.Material.SmoothPlastic, 0
        if item.Name == "Lit window" then
            item.Color, item.Material = LAMPLIGHT, Enum.Material.Glass
            windows = windows + 1
        elseif item.Name == "Window glass" then
            item.Material = Enum.Material.Glass
        elseif item.Name == "Display glass" then
            item.Material, item.Transparency = Enum.Material.Glass, 0.45
        end
        meshes = meshes + 1
    end
end

-- The part village under the meshes: out of sight, still solid, still lit.
local hidden = 0
local function hide(part)
    part.Transparency, part.CastShadow = 1, false
    for _, child in ipairs(part:GetChildren()) do
        if child:IsA("SurfaceGui") then child.Enabled = false
        elseif child:IsA("Decal") then child.Transparency = 1 end
    end
    hidden = hidden + 1
end
for _, part in ipairs(map.Hollowmere:GetDescendants()) do
    if part:IsA("BasePart") and not GROUND[part.Name] then hide(part) end
end
for _, part in ipairs(map.Lamps:GetDescendants()) do
    if part:IsA("BasePart") and part.Position.Z >= LAMPS_FROM_Z then hide(part) end
end
if recording then ChangeHistoryService:FinishRecording(recording, Enum.FinishRecordingOperation.Commit) end
local report = string.format("Hollowmere: %d meshes in Workspace.Scenery (%d lit-window meshes), %d map parts hidden under them",
    meshes, windows, hidden)
print(report)
return report
