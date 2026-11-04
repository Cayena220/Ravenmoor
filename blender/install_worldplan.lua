--[[ Put the WorldPlan world (blender/export_worldplan_game.py, see blender/README.md, "WorldPlan in the game") in the
place, in place of the part-built map.

First import every blender/exports/RobloxWorld/WP_*.fbx with File > Import 3D; the importer uploads the meshes to your
account. Then require this module from the Command Bar (or an MCP call) and run the stages in order, each with the
decoded blender/exports/RobloxWorld/manifest.json:

    W.Check(manifest)            lists every mesh that is not imported yet; changes nothing
    W.Stage(manifest, seconds)   sets up imported meshes for up to `seconds`; run again until it reports none left
    W.Trees(manifest, count)     builds the next `count` oaks from the three templates; run again until all stand
    W.Finish(manifest)           swaps the maps, moves the staff, Mirror and Library into the academy interior,
                                 and adds the portals and lamps
    W.Patch(manifest, seconds)   after an export with --patch: sets up the meshes from its imported WP_Patch*.fbx
                                 files, then swaps them in; run again until it reports none left

Every stage can run again and skips what is done. Until Finish, nothing outside ServerStorage."WorldPlan Staging"
changes, and Finish keeps everything it takes off the map in ServerStorage."WorldPlan Recovery".
  * Each mesh gets its place, Roblox material, collision and night-light name from the manifest. Colours come from
    the mesh's vertex colours or its textures, so every part is white. Meshes players walk in or on are remade with
    PreciseConvexDecomposition collision (as place_ranges.lua does), so doorways and stairs stay open.
  * Each oak is a Model of the template's bark and leaves, turned and scaled as WorldPlan stands it, with an
    invisible trunk players and spells stop at.
  * Optimized grass cards use their imported RGBA ColorMap with SurfaceAppearance.AlphaMode = Transparency;
    the part itself stays opaque so only the image's cutouts disappear.
  * The new Map keeps the place's gameplay models: the chests, the staff, the Dueling Club, the Mirror of Choosing,
    the three Waystones and the road lamps that light at night. The mountains go in Workspace.Scenery, which streams
    persistently so the far ranges never vanish.
]]
local AssetService = game:GetService("AssetService")
local ChangeHistoryService = game:GetService("ChangeHistoryService")
local ServerStorage = game:GetService("ServerStorage")

local W = {}
local WHITE = Color3.new(1, 1, 1)                  -- Studio multiplies the vertex colours by the part's Color
local WARM = Color3.fromRGB(255, 214, 150)         -- night lights glow in their Color (Neon ignores vertex colours)
local PRECISE = Enum.CollisionFidelity.PreciseConvexDecomposition
local KEEP = {"RuneChest1", "RuneChest2", "RuneChest3", "Academy staff", "Dueling Club", "Mirror of Choosing",
    "Hollowmere Waystone", "Castle Waystone", "Whisperwood Waystone", "Lamps"}
-- Each teacher stands at the head of a classroom in the interior with the class in front of them, to -Z: the
-- prompt 4 studs ahead, and ClassService's targets 11 studs past it (Markers.Teacher_*.LessonTargetDepth).
local TEACHERS = {["Professor Rook"] = "Teacher_Hex", ["Professor Holloway"] = "Teacher_Ward",
    ["Professor Quill"] = "Teacher_Charm", ["Healer Fenn"] = "Teacher_Restoration", ["Professor Ashgrove"] = "Teacher_Alteration"}

local function v3(a) return Vector3.new(a[1], a[2], a[3]) end
local function folder(parent, name, class)
    local f = parent:FindFirstChild(name)
    if not f then f = Instance.new(class or "Folder"); f.Name = name; f.Parent = parent end
    return f
end
local function staging() return folder(ServerStorage, "WorldPlan Staging") end

-- Every imported (or staged) WorldPlan mesh by name.
local function index()
    local found = {}
    for _, root in ipairs({workspace, staging()}) do
        for _, o in ipairs(root:GetDescendants()) do
            if o:IsA("MeshPart") and o.Name:match("^WP_") then found[o.Name] = found[o.Name] or o end
        end
    end
    for _, root in ipairs({workspace, staging()}) do
        for _, o in ipairs(root:GetDescendants()) do
            local name = o:IsA("MeshPart") and o:GetAttribute("WorldPlanMesh")
            if name then found[name] = o end
        end
    end
    return found
end

function W.Check(manifest)
    local found, missing, files = index(), 0, {}
    for _, file in ipairs(manifest.files) do
        local lacking = 0
        for _, name in ipairs(file.meshes) do if not found[name] then lacking += 1 end end
        if lacking > 0 then missing += lacking; table.insert(files, string.format("%s (%d of %d)", file.file, lacking, #file.meshes)) end
    end
    if missing == 0 then return "Every WorldPlan mesh is imported." end
    return string.format("%d meshes not imported yet, from: %s", missing, table.concat(files, ", "))
end

-- Set one imported mesh up as its manifest row says, remaking it for precise collision when it needs that.
local function setUp(part, row)
    local size = v3(row.size)
    if (part.Size - size).Magnitude > math.max(0.05, size.Magnitude * 0.002) then
        error(string.format("%s imported at %s, expected %s: import with Scale Unit = Studs", row.name, tostring(part.Size), tostring(size)))
    end
    if row.collision == "precise" and part.CollisionFidelity ~= PRECISE and not part:GetAttribute("WorldPlanImprecise") then
        local ok, fresh = pcall(function()
            return AssetService:CreateMeshPartAsync(Content.fromUri(part.MeshId),
                {CollisionFidelity = PRECISE, RenderFidelity = Enum.RenderFidelity.Automatic})
        end)
        if ok then
            fresh.TextureID = part.TextureID
            for _, child in ipairs(part:GetChildren()) do child.Parent = fresh end
            part:Destroy(); part = fresh
        else
            -- Roblox can't always decompose a mesh; it keeps the importer's collision, and the stage reports it.
            part:SetAttribute("WorldPlanImprecise", tostring(fresh))
        end
    end
    part.Size = size; part.CFrame = CFrame.new(v3(row.position))
    part.Anchored, part.CanTouch = true, false
    part.CanCollide = row.collision ~= "none"; part.CanQuery = part.CanCollide
    part.Color, part.Transparency, part.Reflectance = WHITE, 0, 0
    -- Thin things drawn from both sides (planting, cloth, glass) cast no shadow; buildings drawn from both sides do.
    part.CastShadow = row.material ~= "Glass" and (row.cast_shadow or not row.double_sided)
    part.RenderFidelity = Enum.RenderFidelity.Automatic
    pcall(function() part.DoubleSided = row.double_sided end)
    if row.material == "Water" then
        part.Material, part.Transparency, part.Reflectance = Enum.Material.SmoothPlastic, 0.1, 0.3
    else
        part.Material = Enum.Material[row.material]
    end
    if row.material == "Glass" then part.Transparency = 0.35 end
    if row.alpha_mode == "Transparency" then
        local appearance = part:FindFirstChildOfClass("SurfaceAppearance")
        if not appearance then
            assert(part.TextureID ~= "", row.name .. ": import the RGBA card texture before staging")
            appearance = Instance.new("SurfaceAppearance")
            appearance.ColorMap = part.TextureID
            appearance.Parent = part
        elseif appearance.ColorMap == "" then
            assert(part.TextureID ~= "", row.name .. ": imported SurfaceAppearance has no RGBA ColorMap")
            appearance.ColorMap = part.TextureID
        end
        appearance.AlphaMode = Enum.AlphaMode.Transparency
        part.Transparency = row.transparency or 0
    end
    part.Name = row.name
    if row.night then
        -- WorldService.SetNightLights turns these Neon after dark and switches their light on.
        part.Name, part.Material, part.Color, part.Transparency = row.night, Enum.Material.Glass, WARM, 0.2
        if not part:FindFirstChildOfClass("PointLight") then
            local light = Instance.new("PointLight")
            light.Color, light.Range, light.Brightness, light.Enabled = WARM, row.night == "Lantern" and 16 or 12, 1.2, false
            light.Parent = part
        end
    end
    part:SetAttribute("WorldPlanMesh", row.name)
    part:SetAttribute("WorldPlanGroup", row.group)
    part.Parent = folder(staging(), row.group)
    return part
end

function W.Stage(manifest, seconds)
    local found, started, done, left, failed, imprecise = index(), os.clock(), 0, 0, {}, {}
    local recording = ChangeHistoryService:TryBeginRecording("Stage WorldPlan meshes")
    for i, row in ipairs(manifest.meshes) do
        local part = found[row.name]
        if part and part:GetAttribute("WorldPlanMesh") == row.name then continue end
        if not part then left += 1; continue end
        if os.clock() - started > (seconds or 60) then left += 1; continue end
        local ok, result = pcall(setUp, part, row)
        if ok then
            done += 1
            if result:GetAttribute("WorldPlanImprecise") then table.insert(imprecise, row.name) end
        else table.insert(failed, tostring(result)); left += 1 end
        if i % 20 == 0 then task.wait() end
    end
    if recording then ChangeHistoryService:FinishRecording(recording, Enum.FinishRecordingOperation.Commit) end
    return string.format("Staged %d meshes; %d left.%s%s", done, left,
        #imprecise > 0 and " Kept the importer's collision on " .. table.concat(imprecise, ", ") .. "." or "",
        #failed > 0 and " Failed: " .. table.concat(failed, "; ") or "")
end

-- Build the next `count` oaks. A tree's matrix is in Roblox space, its columns the tree's scaled axes.
function W.Trees(manifest, count)
    local stage = staging()
    local forest = folder(stage, "Forest")
    local parts = {}
    for template, rows in pairs(manifest.templates) do
        parts[template] = {}
        for _, row in ipairs(rows) do
            local part = stage:FindFirstChild(template) and stage[template]:FindFirstChild(row.name)
            assert(part, "Stage the oak templates first: " .. row.name)
            table.insert(parts[template], {part = part, offset = v3(row.offset), name = row.leaves and "Leaves" or "Bark"})
        end
    end
    local built, have = 0, #forest:GetChildren()
    for i = have + 1, math.min(#manifest.trees, have + (count or 500)) do
        local tree = manifest.trees[i]; local a = tree.matrix
        local x = Vector3.new(a[1][1], a[2][1], a[3][1]); local y = Vector3.new(a[1][2], a[2][2], a[3][2])
        local z = Vector3.new(a[1][3], a[2][3], a[3][3])
        local scale = Vector3.new(x.Magnitude, y.Magnitude, z.Magnitude)
        local cf = CFrame.fromMatrix(Vector3.new(a[1][4], a[2][4], a[3][4]), x.Unit, y.Unit, x.Unit:Cross(y.Unit))
        local model = Instance.new("Model"); model.Name = string.format("Oak %04d", i)
        for _, p in ipairs(parts[tree.template]) do
            local part = p.part:Clone()
            part:SetAttribute("WorldPlanMesh", nil); part:SetAttribute("WorldPlanGroup", nil)
            part.Name = p.name
            part.Size = p.part.Size * scale
            part.CFrame = cf * CFrame.new(p.offset * scale)
            part.CastShadow = false
            part.Parent = model
        end
        local trunk = Instance.new("Part"); trunk.Name = "Trunk"; trunk.Shape = Enum.PartType.Cylinder
        trunk.Size = Vector3.new(12 * scale.Y, 2.2 * scale.X, 2.2 * scale.Z)
        trunk.CFrame = cf * CFrame.new(0, 6 * scale.Y, 0) * CFrame.Angles(0, 0, math.pi / 2)
        trunk.Transparency, trunk.Anchored, trunk.CanTouch, trunk.CastShadow = 1, true, false, false
        trunk.Parent = model
        model.Parent = forest
        built += 1
        if built % 100 == 0 then task.wait() end
    end
    return string.format("Built %d oaks; %d of %d stand.", built, #forest:GetChildren(), #manifest.trees)
end

-- Stand a model with the bottom centre of its bounds at `feet`, turned by `turn` about Y.
local function stand(model, feet, turn)
    local cf, size = model:GetBoundingBox()
    local foot = cf.Position - Vector3.new(0, size.Y / 2, 0)
    model:PivotTo(CFrame.new(feet) * CFrame.Angles(0, turn or 0, 0) * CFrame.new(-foot) * model:GetPivot())
end

-- The mountains stream to every player all the time, so they cost as little as they can: no shadows, and Roblox's
-- automatic detail, which draws them coarser with distance. (Always the lowest detail opens cracks between the
-- tiles, where the sky shows through.) Those wholly outside Config.WorldBounds, where no one can walk or fly, are
-- remade with box collision and nothing collides with them; the ones that reach the play area keep precise
-- collision, so players can still climb their lower slopes.
function W.LowMountains(seconds)
    local Config = require(game:GetService("ReplicatedStorage").Shared.Config)
    local b, started, done, left = Config.WorldBounds, os.clock(), 0, 0
    for _, part in ipairs(workspace.Scenery:GetChildren()) do
        if not part:IsA("MeshPart") then continue end
        local lo, hi = part.Position - part.Size / 2, part.Position + part.Size / 2
        local reachable = hi.X > b.MinX - 20 and lo.X < b.MaxX + 20 and hi.Z > b.MinZ - 20 and lo.Z < b.MaxZ + 20
        if not reachable and part.CollisionFidelity ~= Enum.CollisionFidelity.Box then
            if os.clock() - started > (seconds or 90) then left += 1; continue end
            local fresh = AssetService:CreateMeshPartAsync(Content.fromUri(part.MeshId),
                {CollisionFidelity = Enum.CollisionFidelity.Box, RenderFidelity = Enum.RenderFidelity.Automatic})
            fresh.Name, fresh.Size, fresh.CFrame, fresh.Material = part.Name, part.Size, part.CFrame, part.Material
            for _, key in ipairs({"WorldPlanGroup"}) do fresh:SetAttribute(key, part:GetAttribute(key)) end
            for _, child in ipairs(part:GetChildren()) do child.Parent = fresh end
            fresh.Parent = part.Parent; part:Destroy(); part = fresh
            done += 1
        end
        part.Anchored, part.CanTouch, part.CastShadow, part.Color = true, false, false, WHITE
        part.CanCollide, part.CanQuery = reachable, reachable
        part.RenderFidelity = Enum.RenderFidelity.Automatic
    end
    return string.format("Mountains without shadows, at automatic detail; %d remade with box collision, %d left.", done, left)
end

-- Window glass is solid, so no one walks or flies in through a window. The export leaves glass without collision
-- (export_worldplan_game.py, CUTS); the panes are flat, so precise collision follows them closely and never closes a
-- doorway. Lanterns stay as they are.
function W.SolidWindows(seconds)
    local started, done, left = os.clock(), 0, 0
    for _, group in ipairs(workspace.Map:GetChildren()) do
        if not group:IsA("Folder") then continue end
        for _, part in ipairs(group:GetChildren()) do
            if not part:IsA("MeshPart") or part.Material ~= Enum.Material.Glass or part.Name == "Lantern" or part.CanCollide then continue end
            if os.clock() - started > (seconds or 90) then left += 1; continue end
            local ok, fresh = pcall(function()
                return AssetService:CreateMeshPartAsync(Content.fromUri(part.MeshId),
                    {CollisionFidelity = PRECISE, RenderFidelity = Enum.RenderFidelity.Automatic})
            end)
            if not ok then fresh = part else
                fresh.Name, fresh.Size, fresh.CFrame, fresh.TextureID = part.Name, part.Size, part.CFrame, part.TextureID
                fresh.Material, fresh.Color, fresh.Transparency, fresh.Reflectance = part.Material, part.Color, part.Transparency, part.Reflectance
                fresh.CastShadow, fresh.Anchored = part.CastShadow, true
                pcall(function() fresh.DoubleSided = part.DoubleSided end)
                for key, value in pairs(part:GetAttributes()) do fresh:SetAttribute(key, value) end
                for _, child in ipairs(part:GetChildren()) do child.Parent = fresh end
                fresh.Parent = part.Parent; part:Destroy()
            end
            fresh.CanCollide, fresh.CanQuery, fresh.CanTouch = true, true, false
            done += 1
            task.wait()
        end
    end
    return string.format("%d windows made solid, %d left.", done, left)
end

-- After an export with --patch and an import of its WP_Patch*.fbx files: the patch's meshes take the patched ones'
-- places in the installed map (first Nightfang's and Skyquill's glass, split so their windows are solid and their
-- glazed doors open; then the castle and the four houses, rebuilt whole). Each run sets up new meshes in the staging
-- folder for up to `seconds`. Once every one is set up, it removes the patched meshes from the map and puts the new
-- ones in their places, so the map never stands half patched.
function W.Patch(manifest, seconds)
    local found, new = index(), {}
    for _, file in ipairs(manifest.files) do
        if file.replaces then for _, name in ipairs(file.meshes) do new[name] = true end end
    end
    for _, row in ipairs(manifest.meshes) do
        if new[row.name] and not (found[row.name] and found[row.name]:IsDescendantOf(workspace.Map)) then
            assert(found[row.name], "Import the patch's FBX files first: " .. row.name)
        end
    end
    local started, staged, left, removed, added, imprecise = os.clock(), 0, 0, 0, {}, {}
    local recording = ChangeHistoryService:TryBeginRecording("Patch WorldPlan meshes")
    for i, row in ipairs(manifest.meshes) do
        local part = found[row.name]
        if not new[row.name] or part:IsDescendantOf(workspace.Map) or part:GetAttribute("WorldPlanMesh") == row.name then continue end
        if os.clock() - started > (seconds or 120) then left += 1; continue end
        found[row.name] = setUp(part, row); staged += 1
        if i % 10 == 0 then task.wait() end
    end
    if left == 0 then
        -- By the WorldPlanMesh tag, as night lights are renamed Lit window or Lantern.
        local patched = {}
        for _, name in ipairs(manifest.patched or {}) do patched[name] = true end
        for _, group in ipairs(workspace.Map:GetChildren()) do
            for _, old in ipairs(group:GetChildren()) do
                if old:IsA("MeshPart") and (patched[old.Name] or patched[old:GetAttribute("WorldPlanMesh")]) then
                    old:Destroy(); removed += 1
                end
            end
        end
        for _, row in ipairs(manifest.meshes) do
            local part = found[row.name]
            if new[row.name] and not part:IsDescendantOf(workspace.Map) then
                part.Parent = workspace.Map[row.group]
                added[row.group] = (added[row.group] or 0) + 1
                if part:GetAttribute("WorldPlanImprecise") then table.insert(imprecise, row.name) end
            end
        end
        for _, o in ipairs(workspace:GetChildren()) do
            if o.Name:match("^WP_") and not o:FindFirstChildWhichIsA("BasePart", true) then o:Destroy() end
        end
    end
    if recording then ChangeHistoryService:FinishRecording(recording, Enum.FinishRecordingOperation.Commit) end
    if left > 0 then return string.format("Set up %d patch meshes; %d left: run Patch again.", staged, left) end
    local areas = {}
    for group, n in pairs(added) do table.insert(areas, group .. " " .. n) end
    table.sort(areas)
    return string.format("Removed %d meshes; added %s.%s", removed, #areas > 0 and table.concat(areas, ", ") or "nothing",
        #imprecise > 0 and " Kept the importer's collision on " .. table.concat(imprecise, ", ") .. "." or "")
end

-- A meadow-green floor just under the ground, over Config.WorldBounds and a little past it. It closes the seams
-- between WorldPlan's meadow and mountain meshes (one runs along the east edge), so no one falls through or sees sky.
function W.Floor(map)
    local floor = map:FindFirstChild("Meadow floor") or Instance.new("Part")
    floor.Name, floor.Anchored, floor.CanTouch, floor.CastShadow = "Meadow floor", true, false, false
    floor.Size, floor.Position = Vector3.new(1020, 2, 1285), Vector3.new(-150, -1.35, -332.5)
    floor.Material, floor.Color = Enum.Material.Grass, Color3.fromRGB(86, 110, 48)
    floor.Parent = map
    return floor
end

function W.Finish(manifest)
    assert(not workspace:GetAttribute("WorldPlanInstalled"), "WorldPlan is already installed")
    local stage = staging(); local found = index()
    for _, row in ipairs(manifest.meshes) do
        assert(found[row.name] and found[row.name]:GetAttribute("WorldPlanMesh") == row.name, "Stage every mesh first: " .. row.name)
    end
    assert(#stage.Forest:GetChildren() == #manifest.trees, "Build every oak first")
    local recording = ChangeHistoryService:TryBeginRecording("Install WorldPlan")
    local recovery = folder(ServerStorage, "WorldPlan Recovery")
    local markers = workspace.Markers
    local saved = markers:Clone(); saved.Name = "Previous Markers"; saved.Parent = recovery

    -- The gameplay models move to the new Map; the rest of the old one, and its scenery, go to the recovery folder.
    local old = workspace.Map
    local map = Instance.new("Model"); map.Name = "Map"
    for _, name in ipairs(KEEP) do assert(old:FindFirstChild(name), "The map has no " .. name).Parent = map end
    old.Name = "Previous Map"; old.Parent = recovery
    for _, name in ipairs({"Scenery", "Cauldron"}) do
        local o = workspace:FindFirstChild(name)
        if o then o.Name = "Previous " .. name; o.Parent = recovery end
    end
    local scenery = Instance.new("Model"); scenery.Name = "Scenery"
    scenery.ModelStreamingMode = Enum.ModelStreamingMode.Persistent
    -- In the world first, then filled a chunk at a time, so no single move inserts thousands of parts at once.
    map.Parent = workspace; scenery.Parent = workspace

    -- Staff, the Mirror and the Spellbook stand where WorldPlan put them in the interior.
    local props = manifest.props
    for name, anchor in pairs(TEACHERS) do
        local feet = v3(props[name].feet)
        stand(map["Academy staff"][name], feet, math.pi)
        markers[anchor].Position = feet + Vector3.new(0, 3, -4)
        markers[anchor]:SetAttribute("LessonTargetDepth", -11)
    end
    local mirror = v3(props["Mirror of Choosing"].feet)
    stand(map["Mirror of Choosing"], mirror, 0)
    markers.Mirror.Position = mirror + Vector3.new(0, 3, -4)   -- in front: it faces down the side aisle, to -Z
    local book = v3(props.Spellbook.feet)
    local spellbook = workspace:FindFirstChild("Spellbook_Open")
    if spellbook then stand(spellbook, book, 0); spellbook.Parent = map end
    markers.Library.Position = book + Vector3.new(0, 0, 4)

    -- World meshes by area; the mountains are scenery.
    for _, group in ipairs(stage:GetChildren()) do
        if group.Name == "Forest" or group.Name:match("^Oak_") then continue end
        local dest = folder(map, group.Name)
        for i, part in ipairs(group:GetChildren()) do
            -- Each part keeps its WorldPlanMesh tag, so Check and Patch know it after a night light's rename.
            if group.Name == "Landscape" and part.Material == Enum.Material.Rock and part.Size.Y > 40 then
                part.Parent = scenery
            else
                part.Parent = dest
            end
            if i % 50 == 0 then task.wait() end
        end
    end
    -- The templates stay in the staging folder, out of the world, for rebuilding trees.
    local forest = folder(map, "Forest")
    for i, tree in ipairs(stage.Forest:GetChildren()) do
        tree.Parent = forest
        if i % 200 == 0 then task.wait() end
    end
    stage.Forest:Destroy()

    -- Portals between the academy's door and its interior (WorldService.StartAcademyPortals).
    local portals = folder(workspace, "AcademyPortals")
    local function portal(name, from, to, action)
        local m, spot = manifest.markers[from], manifest.markers[to]
        local s = m.scale
        local p = Instance.new("Part"); p.Name = name; p.Size = Vector3.new(2 * s[1], 2 * s[3], 2 * s[2])
        p.Position = v3(m.position); p.Anchored, p.Transparency, p.CanCollide, p.CanQuery, p.CanTouch = true, 1, false, false, true
        p:SetAttribute("ActionText", action)
        -- Both spawns face +Z: the interior's forward_axis +Y runs into the hall, and the exterior's -Y, turned by the
        -- academy's half turn, runs out of the door down the approach. Arrive three studs up, facing that way.
        local at = v3(spot.position) + Vector3.new(0, 3, 0)
        local cf = Instance.new("CFrameValue"); cf.Name = "Destination"; cf.Value = CFrame.lookAt(at, at + Vector3.new(0, 0, 1)); cf.Parent = p
        p.Parent = portals
    end
    portal("Enter", "PORTAL_Academy_Enter", "SPAWN_Academy_Interior", "Enter the academy")
    portal("Return", "PORTAL_Academy_Return", "SPAWN_Academy_Exterior", "Return to the grounds")

    -- WorldPlan's lamps: always on inside the academy, and night lights (named Lantern) outdoors.
    local lamps = folder(map, "WorldPlan lamps")
    for _, light in ipairs(manifest.lights) do
        local inside = light.position[2] > 1000
        local holder = Instance.new("Part"); holder.Name = inside and "Lamp light" or "Lantern"
        holder.Size = Vector3.new(0.4, 0.4, 0.4); holder.Position = v3(light.position)
        holder.Anchored, holder.CanCollide, holder.CanQuery, holder.CanTouch, holder.CastShadow = true, false, false, false, false
        holder.Transparency, holder.Material = 1, Enum.Material.Glass
        local glow = Instance.new("PointLight"); glow.Color = Color3.new(light.color[1], light.color[2], light.color[3])
        glow.Brightness = math.clamp(light.energy / 900, 0.6, 2.5); glow.Range = math.clamp(math.sqrt(light.energy) * 0.7, 10, 40)
        glow.Shadows = inside; glow.Enabled = inside; glow.Parent = holder
        holder.Parent = lamps
    end

    W.Floor(map)
    W.LowMountains(600)
    W.SolidWindows(600)
    for _, o in ipairs(workspace:GetChildren()) do
        if o.Name:match("^WP_") and not o:FindFirstChildWhichIsA("BasePart", true) then o:Destroy() end
    end
    workspace:SetAttribute("WorldPlanInstalled", true)
    workspace:SetAttribute("WorldPlanSource", manifest.source_sha256)
    if recording then ChangeHistoryService:FinishRecording(recording, Enum.FinishRecordingOperation.Commit) end
    return string.format("WorldPlan installed: %d meshes, %d oaks, %d lamps; the old map is in ServerStorage.WorldPlan Recovery",
        #manifest.meshes, #manifest.trees, #manifest.lights)
end

return W
