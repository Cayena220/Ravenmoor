--[[ Place the remodelled Waystones (blender/models/waystone.py, see blender/README.md, "Waystone, remodelled").

Paste this whole file into View > Command Bar and press Enter. Running it again gives the same result, so run it
after every `tools/sync_scripts.py --map`, which brings back the map's slate blocks. For each of the three
"<name> Waystone" models that tools/build.py puts in Workspace.Map it:
  * builds the four meshes from the uploaded Waystone.fbx assets in MESHES, or reuses them if already there,
    and sets each one's material, colour and collision;
  * centres them on the Waystone's marker, on the lowest ground under the dais, and turns the sigil toward
    where Config.Waystones lands travellers;
  * moves the slate Stone's nameplate onto the new Stone, then removes the slate Stone and the neon Rune.
The asset IDs belong to the account that imported Waystone.fbx. After importing it again, copy the new MeshIds
from the imported MeshParts into MESHES.
]]
local AssetService = game:GetService("AssetService")
local ChangeHistoryService = game:GetService("ChangeHistoryService")
local Config = require(game:GetService("ReplicatedStorage").Shared.Config)

local GLOW = Color3.fromRGB(130, 228, 226)   -- Neon glows in the part's Color and ignores the mesh's vertex colours
local WHITE = Color3.new(1, 1, 1)            -- Studio multiplies the vertex colours by this
-- Each mesh's centre from the dais's bottom centre, with the sigil facing -Z (waystone.py's front).
local MESHES = {
    {Name = "Stone", Id = "rbxassetid://120745877307016", Offset = Vector3.new(0, 3.56, 0),
        Material = Enum.Material.Slate, Color = WHITE, Collide = true},
    {Name = "Ironwork", Id = "rbxassetid://97426240572755", Offset = Vector3.new(0, 5.8011, 0),
        Material = Enum.Material.Metal, Color = WHITE, Collide = false},
    {Name = "Runes", Id = "rbxassetid://118795373207391", Offset = Vector3.new(0, 3.2895, 0.0047),
        Material = Enum.Material.Neon, Color = GLOW, Collide = false},
    {Name = "Crystal", Id = "rbxassetid://129181605440465", Offset = Vector3.new(0, 8.85, 0),
        Material = Enum.Material.Neon, Color = GLOW, Collide = false},
}
local DAIS = 3.65          -- half the dais's width across its flats
local HEIGHT = 9.65        -- dais to talon tips
local SINK = 0.02          -- how far the dais sits into the ground, so no seam shows
local NAMEPLATE = Vector3.new(0, 7.6, 0)   -- above the Stone's centre: 1.7 studs over the talons, as over the old rune

local function newMesh(id, collide)
    local fidelity = collide and Enum.CollisionFidelity.PreciseConvexDecomposition or Enum.CollisionFidelity.Box
    local ok, part = pcall(function()
        return AssetService:CreateMeshPartAsync(Content.fromUri(id), {CollisionFidelity = fidelity})
    end)
    if not ok then part = AssetService:CreateMeshPartAsync(id, {CollisionFidelity = fidelity}) end
    return part
end

-- The lowest ground under the dais, sampled every half stud inside its octagon, so that no edge of it floats.
local function groundUnder(centre, ignore)
    local params = RaycastParams.new()
    params.FilterType = Enum.RaycastFilterType.Exclude
    params.FilterDescendantsInstances = ignore
    local low, high, on = math.huge, -math.huge, nil
    for i = -7, 7 do
        for j = -7, 7 do
            local dx, dz = i / 2, j / 2
            if math.abs(dx) + math.abs(dz) <= DAIS * math.sqrt(2) then   -- inside the diagonal flats too
                local hit = workspace:Raycast(Vector3.new(centre.X + dx, centre.Y + 10, centre.Z + dz), Vector3.new(0, -30, 0), params)
                if hit then
                    if hit.Position.Y < low then low = hit.Position.Y; on = hit.Instance.Name end
                    high = math.max(high, hit.Position.Y)
                end
            end
        end
    end
    return low, high, on
end

local function place(key)
    local map = workspace:FindFirstChild("Map")
    local model = map and map:FindFirstChild(key .. " Waystone") or workspace:FindFirstChild(key .. " Waystone", true)
    local marker = workspace:FindFirstChild("Markers") and workspace.Markers:FindFirstChild("Waystone_" .. key)
    local landing = Config.Waystones[key]
    if not (model and marker and landing) then return key .. ": skipped (no Waystone model, marker or Config entry)" end
    local ignore = {model, workspace.Markers}
    for _, player in ipairs(game:GetService("Players"):GetPlayers()) do table.insert(ignore, player.Character) end
    local low, high, on = groundUnder(marker.Position, ignore)
    if low == math.huge then return key .. ": skipped (no ground under the marker)" end
    local base = Vector3.new(marker.Position.X, low - SINK, marker.Position.Z)
    local toward = Vector3.new(landing[1] - base.X, 0, landing[3] - base.Z)
    local pose = toward.Magnitude > 0.01 and CFrame.lookAt(base, base + toward) or CFrame.new(base)
    local made, built = {}, 0
    for _, mesh in ipairs(MESHES) do
        local part = model:FindFirstChild(mesh.Name)
        if not (part and part:IsA("MeshPart") and part.MeshId == mesh.Id) then
            part = newMesh(mesh.Id, mesh.Collide)
            built = built + 1
        end
        part.Name = mesh.Name
        part.CFrame = pose * CFrame.new(mesh.Offset)
        part.Anchored = true
        part.Material = mesh.Material
        part.Color = mesh.Color
        part.CanCollide, part.CanTouch, part.CanQuery = mesh.Collide, mesh.Collide, mesh.Collide
        made[mesh.Name] = part
    end
    -- Swap the slate Stone for the mesh one, taking its nameplate along.
    local removed = 0
    for _, old in ipairs(model:GetChildren()) do
        if old:IsA("BasePart") and not old:IsA("MeshPart") and (old.Name == "Stone" or old.Name == "Rune") then
            local plate = old:FindFirstChild("Nameplate")
            if plate then plate.Parent = made.Stone end
            old:Destroy()
            removed = removed + 1
        end
    end
    for _, mesh in ipairs(MESHES) do made[mesh.Name].Parent = model end
    local plate = made.Stone:FindFirstChild("Nameplate")
    if plate then plate.StudsOffset = NAMEPLATE end
    model.PrimaryPart = made.Stone
    model.WorldPivot = pose
    -- Anything else standing inside the waystone's volume.
    local overlap = OverlapParams.new()
    overlap.FilterType = Enum.RaycastFilterType.Exclude
    overlap.FilterDescendantsInstances = ignore
    local blocked = {}
    for _, part in ipairs(workspace:GetPartBoundsInBox(pose * CFrame.new(0, 0.15 + HEIGHT / 2, 0), Vector3.new(DAIS * 2, HEIGHT, DAIS * 2), overlap)) do
        table.insert(blocked, part:GetFullName())
    end
    local facing = pose.LookVector
    local line = string.format("%s: %d meshes built, %d slate parts removed, on %s at y=%.2f (ground under the dais %.2f to %.2f), sigil faces (%.0f, %.0f), nameplate %s",
        model.Name, built, removed, on, base.Y, low, high, facing.X, facing.Z, plate and "on the Stone" or "MISSING")
    if #blocked > 0 then line = line .. "\n  WARNING: inside its volume: " .. table.concat(blocked, ", ") end
    if high - low > 0.15 then line = line .. string.format("\n  WARNING: the ground rises %.2f studs under the dais; its high side is buried", high - low) end
    return line
end

local recording = ChangeHistoryService:TryBeginRecording("Place Waystones")
local ok, result = pcall(function()
    local lines = {}
    for _, key in ipairs({"Hollowmere", "Castle", "Whisperwood"}) do table.insert(lines, place(key)) end
    return table.concat(lines, "\n")
end)
if recording then
    ChangeHistoryService:FinishRecording(recording, Enum.FinishRecordingOperation.Commit)
end
local report = ok and result or ("Waystones not placed: " .. tostring(result))
print(report)
return report
