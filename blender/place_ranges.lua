--[[ Set up the imported mountain ranges and woods (blender/models/ranges.py, see blender/README.md, "Mountains and woods").

Import blender/exports/Ranges.fbx with Insert Using Scene Position on, then paste this whole file into View > Command
Bar and press Enter. Running it again gives the same result. It:
  * moves the imported Ranges model into Workspace.Scenery, out of Workspace.Map, so tools/sync_scripts.py --map
    leaves it alone, and streams Scenery persistently, so the far ranges never vanish past the streaming radius;
  * remakes each mountain tile from its uploaded mesh with PreciseConvexDecomposition collision. Players then walk
    up the slopes and are stopped by the crags, instead of by the importer's rough hull, which fills the valleys;
  * anchors every mesh and turns it white, so the vertex colours show true. Mountains collide and stop spells;
    the trees are scenery that players and spells pass through.
]]
local AssetService = game:GetService("AssetService")
local ChangeHistoryService = game:GetService("ChangeHistoryService")

local WHITE = Color3.new(1, 1, 1)   -- Studio multiplies a mesh's vertex colours by its part's Color
local PRECISE = Enum.CollisionFidelity.PreciseConvexDecomposition

local ranges = workspace:FindFirstChild("Ranges", true)
assert(ranges and ranges:IsA("Model"), "Import blender/exports/Ranges.fbx into Workspace first (Insert Using Scene Position)")
local recording = ChangeHistoryService:TryBeginRecording("Place ranges")
local scenery = workspace:FindFirstChild("Scenery") or Instance.new("Model")
scenery.Name, scenery.ModelStreamingMode = "Scenery", Enum.ModelStreamingMode.Persistent
scenery.Parent = workspace
ranges.Parent = scenery

local tiles, trees, failed = 0, 0, 0
for _, part in ipairs(ranges:GetDescendants()) do
    if not part:IsA("MeshPart") then continue end
    if part.Parent.Name == "Mountains" then
        if part.CollisionFidelity ~= PRECISE then
            local ok, fresh = pcall(function()
                return AssetService:CreateMeshPartAsync(Content.fromUri(part.MeshId), {CollisionFidelity = PRECISE})
            end)
            if ok then
                fresh.Name, fresh.Size, fresh.CFrame = part.Name, part.Size, part.CFrame
                fresh.Parent = part.Parent
                part:Destroy()
                part = fresh
            else
                failed = failed + 1
                warn(part.Name .. ": kept the imported collision, could not remake the mesh: " .. tostring(fresh))
            end
        end
        part.CanCollide, part.CanQuery = true, true
        tiles = tiles + 1
    else
        part.CanCollide, part.CanQuery = false, false
        trees = trees + 1
    end
    part.Anchored, part.CanTouch, part.CastShadow = true, false, true
    part.Color, part.Material = WHITE, Enum.Material.SmoothPlastic
end
if recording then ChangeHistoryService:FinishRecording(recording, Enum.FinishRecordingOperation.Commit) end
print(string.format("Ranges: %d mountain tiles with precise collision%s, %d meshes of trees, in Workspace.Scenery",
    tiles - failed, failed > 0 and string.format(" (%d kept the importer's)", failed) or "", trees))
