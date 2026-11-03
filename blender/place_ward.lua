--[[ Set up the imported glass ward (blender/vfx/ward.py, see blender/README.md, "Glass ward") and its sounds.

Import blender/exports/WardVFX.fbx, then paste this whole file into View > Command Bar and press Enter. Running it
again changes nothing. It moves the imported WardVFX model into ReplicatedStorage.VFX, where every client's
EffectsController clones it for the ward, its cracks and its shatter. It also drops Blender's .001 name suffixes and
turns the meshes white; EffectsController colours each copy and sets its material as it plays. A WardVFX already
there, from an earlier import, is replaced.

It also puts the ward's sounds in ReplicatedStorage.SFX as Sounds named after SOUNDS below. EffectsController plays a
copy at the ward: WardRaise as it rises, WardCrack on each hit and WardShatter when it breaks. A sound left without an
id is skipped, and the ward plays without it.
]]
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ChangeHistoryService = game:GetService("ChangeHistoryService")

local NEEDED = {"Shell", "Frame", "Circle", "Crack", "Shard1", "Shard2", "Shard3", "Shard4", "Shard5", "Shard6", "Ring", "Glint"}
-- From Roblox's licensed sound library (Creator Store, ProSoundEffects): free to use in any experience.
local SOUNDS = {
    WardRaise = {Id = "rbxassetid://9116409574", Volume = 0.55, Speed = 1.1},    -- Magic Swirling Tone 1: a spinning chime and sparkle
    WardCrack = {Id = "rbxassetid://9114863345", Volume = 0.7, Speed = 1.25},    -- Ice Cubes Fall Dropping To Floor 2: a sharp rattling tinkle
    WardShatter = {Id = "rbxassetid://9114592245", Volume = 1, Speed = 1},       -- Glass Breaks 3: breaks, hits and bounces, debris shards
}

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

local sfx = ReplicatedStorage:FindFirstChild("SFX") or Instance.new("Folder")
sfx.Name = "SFX"; sfx.Parent = ReplicatedStorage
local sounds = {}
for name, entry in pairs(SOUNDS) do
    local sound = sfx:FindFirstChild(name)
    if entry.Id ~= "" then
        sound = sound or Instance.new("Sound")
        sound.Name, sound.SoundId, sound.Volume, sound.PlaybackSpeed = name, entry.Id, entry.Volume, entry.Speed or 1
        sound.RollOffMinDistance, sound.RollOffMaxDistance = 10, 120
        sound.Parent = sfx
        table.insert(sounds, name)
    end
end
table.sort(sounds)
if recording then ChangeHistoryService:FinishRecording(recording, Enum.FinishRecordingOperation.Commit) end

local missing = {}
for _, name in ipairs(NEEDED) do if not placed:FindFirstChild(name) then table.insert(missing, name) end end
local report = "WardVFX in ReplicatedStorage.VFX" .. (#missing > 0 and ("; MISSING: " .. table.concat(missing, ", "))
    or (", with all " .. #NEEDED .. " meshes")) .. "; sounds in ReplicatedStorage.SFX: "
    .. (#sounds > 0 and table.concat(sounds, ", ") or "none yet")
print(report)
return report
