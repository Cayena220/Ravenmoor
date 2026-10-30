--[[ Set up the imported Scintara effect (blender/vfx/scintara.py, see blender/README.md, "Scintara effect").

Import blender/exports/ScintaraVFX.fbx, then paste this whole file into View > Command Bar and press Enter. Running it
again changes nothing. It moves the imported ScintaraVFX model into ReplicatedStorage.VFX, where every client's
EffectsController clones it for the spark bolt and the spark lance. It also drops Blender's .001 name suffixes so the
meshes are Spark, Tail, Flash, Beam, Coil, Ring and Splash, and turns them white. EffectsController tints each copy,
makes it Neon and anchors it as it plays. A ScintaraVFX already there, from an earlier import, is replaced.
]]
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ChangeHistoryService = game:GetService("ChangeHistoryService")

local NEEDED = {Spark = true, Tail = true, Flash = true, Beam = true, Coil = true, Ring = true, Splash = true}

-- The imported effect: a Model named ScintaraVFX outside ReplicatedStorage.VFX, wherever the importer put it (it may
-- wrap it in a model of the same name). Parents come before their children here, so the first one found is the
-- outermost.
local vfx = ReplicatedStorage:FindFirstChild("VFX")
local imported
for _, item in ipairs(game:GetDescendants()) do
    local ok, found = pcall(function()
        return item:IsA("Model") and item.Name == "ScintaraVFX" and not (vfx and item:IsDescendantOf(vfx))
    end)
    if ok and found then imported = item; break end
end
local placed = vfx and vfx:FindFirstChild("ScintaraVFX")
assert(imported or placed, "Import blender/exports/ScintaraVFX.fbx first")
local recording = ChangeHistoryService:TryBeginRecording("Place Scintara effect")
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
-- EffectsController looks for the meshes as ScintaraVFX's own children: lift them out of any wrapper model.
local inner = placed:FindFirstChild("ScintaraVFX")
if inner then
    for _, item in ipairs(inner:GetChildren()) do item.Parent = placed end
    inner:Destroy()
end
placed.Parent = vfx
if recording then ChangeHistoryService:FinishRecording(recording, Enum.FinishRecordingOperation.Commit) end
local missing = {}
for name in pairs(NEEDED) do if not placed:FindFirstChild(name) then table.insert(missing, name) end end
table.sort(missing)
local report = "ScintaraVFX in ReplicatedStorage.VFX" .. (#missing > 0 and ("; MISSING: " .. table.concat(missing, ", "))
    or ", with Spark, Tail, Flash, Beam, Coil, Ring and Splash")
print(report)
return report
