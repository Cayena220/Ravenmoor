--[[ Set up the imported glass ward (blender/vfx/ward.py, see blender/README.md, "Glass ward").

Import blender/exports/WardVFX.fbx, then paste this whole file into View > Command Bar and press Enter. Running it
again changes nothing. It moves the imported WardVFX model into ReplicatedStorage.VFX, where every client's
EffectsController clones it for the ward, its cracks and its shatter. It also drops Blender's .001 name suffixes and
turns the meshes white; EffectsController colours each copy and sets its material as it plays. A WardVFX already
there, from an earlier import, is replaced.
]]
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ChangeHistoryService = game:GetService("ChangeHistoryService")

local NEEDED = {"Shell", "Frame", "Circle", "Crack", "Shard1", "Shard2", "Shard3", "Shard4", "Shard5", "Shard6", "Ring", "Glint"}

local vfx = ReplicatedStorage:FindFirstChild("VFX")
local imported
for _, item in ipairs(game:GetDescendants()) do
    local ok, found = pcall(function()
        return item:IsA("Model") and item.Name == "WardVFX" and not (vfx and item:IsDescendantOf(vfx))
    end)
    if ok and found then imported = item; break end
end
local placed = vfx and vfx:FindFirstChild("WardVFX")
assert(imported or placed, "Import blender/exports/WardVFX.fbx first")
local recording = ChangeHistoryService:TryBeginRecording("Place glass ward")
if imported then
    if not vfx then vfx = Instance.new("Folder"); vfx.Name = "VFX"; vfx.Parent = ReplicatedStorage end
    if placed then placed:Destroy() end
    placed = imported
end
for _, item in ipairs(placed:GetDescendants()) do
    local base = (item:IsA("BasePart") or item:IsA("Model")) and item.Name:match("^(.-)%.%d%d%d$")
    if base then item.Name = base end
    if item:IsA("MeshPart") then
        item.Color, item.Anchored, item.CanCollide, item.CanQuery, item.CanTouch = Color3.new(1, 1, 1), true, false, false, false
        item.CastShadow = false
    end
end
-- EffectsController looks for the meshes as WardVFX's own children: lift them out of any wrapper model.
local inner = placed:FindFirstChild("WardVFX")
if inner then
    for _, item in ipairs(inner:GetChildren()) do item.Parent = placed end
    inner:Destroy()
end
placed.Parent = vfx

if recording then ChangeHistoryService:FinishRecording(recording, Enum.FinishRecordingOperation.Commit) end

local missing = {}
for _, name in ipairs(NEEDED) do if not placed:FindFirstChild(name) then table.insert(missing, name) end end
local report = "WardVFX in ReplicatedStorage.VFX" .. (#missing > 0 and ("; MISSING: " .. table.concat(missing, ", "))
    or (", with all " .. #NEEDED .. " meshes"))
print(report)
return report
