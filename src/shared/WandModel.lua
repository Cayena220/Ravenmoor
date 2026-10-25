-- Builds a wand from parts, no assets. The grip sits at `at`; the wand points along at's -Z.
-- anchored=true makes a static preview (bag); otherwise parts are welded to the handle for a hand.
local Wands = require(game:GetService("ReplicatedStorage").Shared.WandData)
local M = {}
local function rgb(c, scale) scale = scale or 1; return Color3.fromRGB(math.min(255, c[1]*scale), math.min(255, c[2]*scale), math.min(255, c[3]*scale)) end
function M.Build(wand, at, anchored)
    local wood, core, rarity = Wands.Woods[wand.Wood], Wands.Cores[wand.Core], Wands.Rarities[wand.Rarity]
    local body = wand.Named and Wands.Named[wand.Named].Body
    local model = Instance.new("Model"); model.Name = "Wand"
    local along = CFrame.Angles(0, math.pi/2, 0) -- Cylinders run along X; turn them to run along Z.
    local function part(name, shape, size, z, color, material)
        local p = Instance.new("Part"); p.Name = name; p.Shape = shape; p.Size = size
        p.Color = color; p.Material = material or Enum.Material.Wood
        p.CanCollide = false; p.CanTouch = false; p.CanQuery = false; p.Massless = true; p.CastShadow = false
        p.Anchored = anchored == true
        p.CFrame = at * CFrame.new(0, 0, z) * (shape == Enum.PartType.Cylinder and along or CFrame.new())
        p.Parent = model
        return p
    end
    -- A thin cylinder leaving (y, z), tilted `angle` degrees from the tip direction toward +Y.
    local function seg(name, len, girth, y, z, angle, color, material)
        local p = part(name, Enum.PartType.Cylinder, Vector3.new(len, girth, girth), z, color, material)
        p.CFrame = at * CFrame.new(0, y, z) * CFrame.Angles(math.rad(angle), 0, 0) * CFrame.new(0, 0, -len/2) * along
        return p
    end
    -- An ellipsoid (sphere SpecialMesh on a block), long along Z, tilted `angle` degrees toward +Y.
    local function oval(name, size, y, z, angle, color, material)
        local p = part(name, Enum.PartType.Block, size, z, color, material)
        p.CFrame = at * CFrame.new(0, y, z) * CFrame.Angles(math.rad(angle), 0, 0)
        local mesh = Instance.new("SpecialMesh"); mesh.MeshType = Enum.MeshType.Sphere; mesh.Parent = p
        return p
    end
    local function ball(name, size, y, z, color, material)
        local p = part(name, Enum.PartType.Ball, Vector3.one*size, z, color, material)
        p.CFrame = at * CFrame.new(0, y, z)
        return p
    end
    local t, length = wood.Thickness, Wands.Length(wand)
    local metal, glow, neon = rgb(rarity.Metal), rgb(core.Color), Enum.Material.Neon
    local handle = part("Handle", Enum.PartType.Cylinder, Vector3.new(0.8, t*1.6, t*1.6), 0.05, rgb(wood.Color, 0.72))
    model.PrimaryPart = handle
    part("Pommel", Enum.PartType.Ball, Vector3.one*t*2, 0.5, metal, Enum.Material.Metal)
    local shaftEnd = body == "Forked" and 1.8 or length
    part("Shaft", Enum.PartType.Cylinder, Vector3.new(shaftEnd-0.35, t, t), -0.35-(shaftEnd-0.35)/2, rgb(wood.Color))
    local tip
    if body == "Forked" then
        -- Stormfork: the shaft splits at a brass collar into two prongs; the spark between them is the tip.
        ball("Collar", t*1.3, 0, -shaftEnd, metal, Enum.Material.Metal)
        for _, side in ipairs({1, -1}) do
            local a = math.rad(24)
            seg("Prong", 0.34, t*0.55, 0, 0.02-shaftEnd, 24*side, rgb(wood.Color, 0.9))
            ball("Cap", t*0.65, side*0.34*math.sin(a), 0.02-shaftEnd-0.34*math.cos(a), glow, neon)
        end
        for i = 0, 3 do part("Coil", Enum.PartType.Cylinder, Vector3.new(0.05, t*1.35, t*1.35), -0.75-i*0.12, metal, Enum.Material.Metal) end
        tip = part("Tip", Enum.PartType.Ball, Vector3.one*t*0.8, -2.07, glow, neon); tip.Transparency = 0.2
    elseif body == "Fang" then
        -- Widow's Bite: a stretched fang between two mandibles, eight legs and a silk-wrapped grip.
        for side = 1, -1, -2 do oval("Mandible", Vector3.new(t*0.42, t*0.42, t*1.01), side*t*0.6, -length, -14*side, metal, Enum.Material.Metal) end
        tip = oval("Tip", Vector3.new(t, t, t*2.6), 0, -length-0.07, 0, glow, neon); tip.Transparency = 0.15
        for i = 0, 3 do
            local z = -0.72-i*0.26
            for _, angle in ipairs({128, -128}) do
                seg("Leg", 0.22, t*0.3, 0, z, angle, rgb(wood.Color))
                ball("Claw", t*0.36, 0.22*math.sin(math.rad(angle)), z-0.22*math.cos(math.rad(angle)), rgb(wood.Color))
            end
        end
        for _, z in ipairs({0.3, 0.2, 0.1}) do part("Silk", Enum.PartType.Cylinder, Vector3.new(0.07, t*1.68, t*1.68), z, rgb(Wands.Trims.Silk), Enum.Material.Fabric) end
    else
        tip = part("Tip", Enum.PartType.Ball, Vector3.one*t*1.1, -length, glow, neon); tip.Transparency = 0.15
    end
    local attachment = Instance.new("Attachment"); attachment.Name = "Tip"; attachment.Parent = tip
    local rank = ({Common = 0, Uncommon = 1, Rare = 2, Epic = 3})[wand.Rarity]
    if rank >= 1 then part("Band", Enum.PartType.Cylinder, Vector3.new(0.08, t*1.9, t*1.9), -0.38, metal, Enum.Material.Metal) end
    if rank >= 2 then
        part("Band", Enum.PartType.Cylinder, Vector3.new(0.08, t*1.9, t*1.9), 0.4, metal, Enum.Material.Metal)
        part("Core", Enum.PartType.Cylinder, Vector3.new(0.18, t*1.7, t*1.7), -0.12, glow, neon)
    end
    if rank >= 3 then part("Collar", Enum.PartType.Cylinder, Vector3.new(0.06, t*1.5, t*1.5), 0.1-length, metal, Enum.Material.Metal) end
    for i = 1, body ~= "Fang" and (wood.Thorns or wood.Knots) and 3 or 0 do
        local z = -0.55-(length-0.8)*i/4
        local bump = part(wood.Thorns and "Thorn" or "Knot", Enum.PartType.Ball, Vector3.one*t*(wood.Thorns and 0.7 or 1.25), z, rgb(wood.Color, 0.8))
        if wood.Thorns then bump.CFrame = bump.CFrame * CFrame.new((i % 2 == 0 and 1 or -1)*t*0.45, t*0.3, 0) end
    end
    if body == "Sprout" then
        -- Hearthroot: two roots behind the pommel, a bud under the middle knot and a leaf near the tip.
        local leaf = rgb(Wands.Trims.Leaf)
        for _, angle in ipairs({140, 220}) do
            seg("Root", 0.36, t*0.45, 0, 0.44, angle, rgb(wood.Color, 0.6))
            ball("Root", t*0.5, 0.36*math.sin(math.rad(angle)), 0.44-0.36*math.cos(math.rad(angle)), rgb(wood.Color, 0.6))
        end
        ball("Bud", t*0.5, -t*0.72, -0.55-(length-0.8)/2, leaf, Enum.Material.LeafyGrass)
        local y, z = t*0.4, 0.5-length
        seg("Stem", 0.13, t*0.22, y, z, 50, rgb(Wands.Trims.Leaf, 0.8), Enum.Material.LeafyGrass)
        y, z = y+0.13*math.sin(math.rad(50))+0.1, z-0.13*math.cos(math.rad(50))-0.173
        oval("Leaf", Vector3.new(t*0.25, t*0.85, t*2.3), y, z, 30, leaf, Enum.Material.LeafyGrass)
    end
    model.WorldPivot = at
    if not anchored then
        for _, p in ipairs(model:GetChildren()) do
            if p ~= handle and p:IsA("BasePart") then local weld = Instance.new("WeldConstraint"); weld.Part0 = handle; weld.Part1 = p; weld.Parent = p end
        end
    end
    return model
end
return M
