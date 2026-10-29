--[[ Set up the imported dash effect (blender/vfx/dash.py, see blender/README.md, "Dash effect").

Import blender/exports/DashVFX.fbx, then paste this whole file into View > Command Bar and press Enter. Running it
again changes nothing. It moves the imported DashVFX model into ReplicatedStorage.VFX, where every client's
EffectsController:Dash clones it on a dodge, drops Blender's .001 name suffixes so the meshes are Streak, Speed lines
and Ring, and turns them white. EffectsController tints each copy, makes it Neon and anchors it as it plays.
]]
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ChangeHistoryService = game:GetService("ChangeHistoryService")

local NEEDED = {Streak = true, ["Speed lines"] = true, Ring = true}

-- The imported effect: a Model named DashVFX, wherever the importer put it (it may wrap it in a model of the same
-- name). Parents come before their children here, so the first one found is the outermost.
local dash
for _, item in ipairs(game:GetDescendants()) do
    local ok, found = pcall(function() return item:IsA("Model") and item.Name == "DashVFX" end)
    if ok and found then dash = item; break end
end
assert(dash, "Import blender/exports/DashVFX.fbx first")
local recording = ChangeHistoryService:TryBeginRecording("Place dash effect")
local vfx = ReplicatedStorage:FindFirstChild("VFX") or Instance.new("Folder")
vfx.Name = "VFX"
vfx.Parent = ReplicatedStorage
for _, item in ipairs(dash:GetDescendants()) do
    local base = (item:IsA("BasePart") or item:IsA("Model")) and item.Name:match("^(.-)%.%d%d%d$")
    if base then item.Name = base end
    if item:IsA("MeshPart") then
        item.Color, item.Anchored, item.CanCollide, item.CanQuery, item.CanTouch = Color3.new(1, 1, 1), true, false, false, false
    end
end
-- EffectsController looks for the meshes as DashVFX's own children: lift them out of any wrapper model.
local inner = dash:FindFirstChild("DashVFX")
if inner then
    for _, item in ipairs(inner:GetChildren()) do item.Parent = dash end
    inner:Destroy()
end
dash.Parent = vfx
if recording then ChangeHistoryService:FinishRecording(recording, Enum.FinishRecordingOperation.Commit) end
local missing = {}
for name in pairs(NEEDED) do if not dash:FindFirstChild(name) then table.insert(missing, name) end end
local report = "DashVFX in ReplicatedStorage.VFX" .. (#missing > 0 and ("; MISSING: " .. table.concat(missing, ", ")) or ", with Streak, Speed lines and Ring")
print(report)
return report
