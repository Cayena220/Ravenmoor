--[[ The models the game builds in code, recorded outside Roblox for the world scene (blender/world/world.py).

The game's own builders run here against just enough of Roblox to record the parts they make: Instance, Vector3,
CFrame (with real rotations), Color3 and Enum. Nothing is copied from them, so the world shows what the game spawns:
  * every monster, from MonsterService:Start's spawn list through MonsterService:Spawn;
  * wands from WandModel.Build: each wood at each rarity, and the three named wands, in a gallery by the arrival pad;
  * the training dummies, from the block that builds them in InteractionService:Start;
  * the five lesson targets in front of each teacher, from the loop that builds them in ClassService.
The last two are built inside larger functions, so their blocks are lifted out of the source by the lines that
open and close them, and the run stops with an error if those lines move.

The caller sets ROOT (the project folder) and gets back JSON: a list of models, each a group, a name and its parts.
]]
local Vmt, Cmt, Imt = {}, {}, {}

local function vec(x, y, z) return setmetatable({X = x or 0, Y = y or 0, Z = z or 0}, Vmt) end
Vmt.__index = function(v, k)
    local m = math.sqrt(v.X * v.X + v.Y * v.Y + v.Z * v.Z)
    if k == "Magnitude" then return m end
    if k == "Unit" then return vec(v.X / m, v.Y / m, v.Z / m) end
end
Vmt.__add = function(a, b) return vec(a.X + b.X, a.Y + b.Y, a.Z + b.Z) end
Vmt.__sub = function(a, b) return vec(a.X - b.X, a.Y - b.Y, a.Z - b.Z) end
Vmt.__unm = function(a) return vec(-a.X, -a.Y, -a.Z) end
Vmt.__div = function(a, b) return vec(a.X / b, a.Y / b, a.Z / b) end
Vmt.__mul = function(a, b)
    if type(a) == "number" then return vec(a * b.X, a * b.Y, a * b.Z) end
    if type(b) == "number" then return vec(a.X * b, a.Y * b, a.Z * b) end
    return vec(a.X * b.X, a.Y * b.Y, a.Z * b.Z)
end
Vector3 = {new = vec, zero = vec(0, 0, 0), one = vec(1, 1, 1)}

-- A CFrame is a position and a row-major 3x3 rotation, composed as Roblox composes them.
local function cf(x, y, z, r) return setmetatable({x = x, y = y, z = z, r = r or {1, 0, 0, 0, 1, 0, 0, 0, 1}}, Cmt) end
local function mulR(a, b)
    local r = {}
    for i = 0, 2 do for j = 0, 2 do r[i * 3 + j + 1] = a[i * 3 + 1] * b[j + 1] + a[i * 3 + 2] * b[3 + j + 1] + a[i * 3 + 3] * b[6 + j + 1] end end
    return r
end
Cmt.__index = function(c, k)
    if k == "Position" then return vec(c.x, c.y, c.z) end
end
Cmt.__mul = function(a, b)
    local r = a.r
    if getmetatable(b) == Vmt then
        return vec(a.x + r[1] * b.X + r[2] * b.Y + r[3] * b.Z, a.y + r[4] * b.X + r[5] * b.Y + r[6] * b.Z, a.z + r[7] * b.X + r[8] * b.Y + r[9] * b.Z)
    end
    local p = a * vec(b.x, b.y, b.z)
    return cf(p.X, p.Y, p.Z, mulR(r, b.r))
end
Cmt.__add = function(a, v) return cf(a.x + v.X, a.y + v.Y, a.z + v.Z, a.r) end
Cmt.__sub = function(a, v) return cf(a.x - v.X, a.y - v.Y, a.z - v.Z, a.r) end
CFrame = {}
function CFrame.new(x, y, z)
    if x == nil then return cf(0, 0, 0) end
    if type(x) == "table" then return cf(x.X, x.Y, x.Z) end
    return cf(x, y, z)
end
function CFrame.Angles(rx, ry, rz)   -- Rx * Ry * Rz, as CFrame.fromEulerAnglesXYZ
    local cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return cf(0, 0, 0, mulR(mulR({1, 0, 0, 0, cx, -sx, 0, sx, cx}, {cy, 0, sy, 0, 1, 0, -sy, 0, cy}), {cz, -sz, 0, sz, cz, 0, 0, 0, 1}))
end

Color3 = {fromRGB = function(r, g, b) return {r, g, b} end, new = function(r, g, b) return {r * 255, g * 255, b * 255} end}
Enum = setmetatable({}, {__index = function(enums, kind)
    local items = setmetatable({}, {__index = function(t, name) local item = {Name = name}; rawset(t, name, item); return item end})
    rawset(enums, kind, items); return items
end})

local methods = {
    IsA = function(o, class) return o.ClassName == class or (class == "BasePart" and o.ClassName == "Part") end,
    GetChildren = function(o) return rawget(o, "_children") end,
    FindFirstChild = function(o, name) for _, c in ipairs(rawget(o, "_children")) do if c.Name == name then return c end end end,
    SetAttribute = function() end, GetAttribute = function() end, Destroy = function() end,
}
Imt.__index = function(o, k)
    if methods[k] then return methods[k] end
    local props = rawget(o, "_props")
    if k == "Position" and props.CFrame then return props.CFrame.Position end
    return props[k]
end
Imt.__newindex = function(o, k, v)
    local props = rawget(o, "_props")
    if k == "Parent" then table.insert(rawget(v, "_children"), o); props.Parent = v
    elseif k == "Position" then props.CFrame = cf(v.X, v.Y, v.Z, props.CFrame and props.CFrame.r)
    else props[k] = v end
end
Instance = {new = function(class) return setmetatable({ClassName = class, _props = {Name = class}, _children = {}}, Imt) end}

-- Services: the shared modules and loot tables load from src/; anything else is a do-nothing stand-in.
local nothing; nothing = setmetatable({}, {__index = function() return nothing end, __call = function() return nothing end})
local function folder(path) return setmetatable({}, {__index = function(_, name) return {Path = ROOT .. path .. name .. ".lua"} end}) end
local services = {ReplicatedStorage = {Shared = folder("/src/shared/")}, ServerStorage = folder("/src/serverstorage/")}
game = {GetService = function(_, name) return services[name] or nothing end}
workspace = nothing
task = {spawn = function() end, wait = function() end, delay = function() end}
local loaded = {}
require = function(m) if not loaded[m.Path] then loaded[m.Path] = assert(loadfile(m.Path))() end; return loaded[m.Path] end
local function shared(name) return require({Path = ROOT .. "/src/shared/" .. name .. ".lua"}) end

-- Lift a block out of a source file: from the line containing `first` through the line containing `last` and the
-- `after` lines that follow it (the end of its loop), as a function taking `params`.
local function lift(file, first, last, after, params)
    local lines = {}
    for line in io.lines(ROOT .. file) do lines[#lines + 1] = line end
    local a, b
    for i, line in ipairs(lines) do
        if not a and line:find(first, 1, true) then a = i end
        if a and not b and line:find(last, 1, true) then b = i + after end
    end
    assert(a and b, file .. ": the block from '" .. first .. "' to '" .. last .. "' has moved")
    return assert(load("return function(" .. params .. ")\n" .. table.concat(lines, "\n", a, b) .. "\nend", "=" .. file))()
end

local models = {}
local function record(group, model)
    local parts = {}
    for _, p in ipairs(model:GetChildren()) do
        if p.ClassName == "Part" and p.CFrame then
            local c, s = p.CFrame, p.Size
            local ellipsoid = false
            for _, m in ipairs(p:GetChildren()) do if m.ClassName == "SpecialMesh" then ellipsoid = true end end
            parts[#parts + 1] = {shape = ellipsoid and "Ball" or (p.Shape and p.Shape.Name or "Block"), size = {s.X, s.Y, s.Z},
                cframe = {c.x, c.y, c.z, table.unpack(c.r)}, color = p.Color or {163, 162, 165},
                transparency = p.Transparency or 0}
        end
    end
    models[#models + 1] = {group = group, name = model.Name, parts = parts}
end

-- Monsters, each at its spawn point.
local server = {WorldService = {Monsters = Instance.new("Folder"), Targets = Instance.new("Folder"),
    Anchor = function(_, name) local p = shared("WorldPoints")[name]; return {Position = vec(p[1], p[2], p[3])} end},
    CombatService = {Register = function(_, _, state) return state end}}
local monsters = assert(loadfile(ROOT .. "/src/server/Services/MonsterService.lua"))()
monsters:Init(server); monsters:Start()
for _, spawn in ipairs(monsters.Spawns) do monsters:Spawn(spawn.Id, spawn.Position, spawn) end
for _, m in ipairs(server.WorldService.Monsters:GetChildren()) do record("Monsters", m) end

-- Wands: each wood at each rarity (cores in turn), lying with their tips north, then the named wands behind them.
local W, build = shared("WandData"), shared("WandModel")
local function sorted(t) local keys = {}; for k in pairs(t) do keys[#keys + 1] = k end; table.sort(keys); return keys end
local woods, cores = sorted(W.Woods), sorted(W.Cores)
local rarities = {"Common", "Uncommon", "Rare", "Epic"}
for i, wood in ipairs(woods) do
    for j, rarity in ipairs(rarities) do
        if W.Rarities[rarity] then
            local wand = {Wood = wood, Core = cores[(i + j - 2) % #cores + 1], Rarity = rarity}
            local model = build.Build(wand, CFrame.new(GALLERY[1] + (i - 1) * 1.0, GALLERY[2], GALLERY[3] + (j - 1) * 4.0), true)
            model.Name = rarity .. " " .. wood .. " wand (" .. wand.Core .. ")"
            record("Wands", model)
        end
    end
end
for i, id in ipairs(W.NamedOrder) do
    local model = build.Build(W.Make(id), CFrame.new(GALLERY[1] + 0.5 + (i - 1) * 2.5, GALLERY[2], GALLERY[3] + 16.5), true)
    model.Name = W.Named[id].Title
    record("Wands", model)
end

-- The training dummies, as InteractionService:Start builds them.
local dummies = lift("/src/server/Services/InteractionService.lua", "-- Straw dummies stand at", "self.S.CombatService:Register(model,{Dummy=true})", 1, "self")
dummies({S = server})
for _, m in ipairs(server.WorldService.Targets:GetChildren()) do record("Training dummies", m) end

-- The lesson targets in front of every teacher, as ClassService builds them when a lesson's test begins.
local Config = shared("Config")
local targets = lift("/src/server/Services/ClassService.lua", "local marker=self.S.WorldService:Anchor(Config.Teachers[l.School].Anchor)",
    "l.Targets[#l.Targets+1]=target", 1, "self, l, player, Config")
for _, school in ipairs(sorted(Config.Teachers)) do
    local before = #server.WorldService.Targets:GetChildren()
    targets({S = server}, {School = school, Targets = {}}, {UserId = 1}, Config)
    local all = server.WorldService.Targets:GetChildren()
    for i = before + 1, #all do record("Lesson targets", all[i]) end
end

-- JSON out.
local function json(v)
    local t = type(v)
    if t == "number" then return string.format("%.5g", v) end
    if t == "string" then return '"' .. v:gsub('[%c"\\]', function(c) return string.format("\\u%04x", c:byte()) end) .. '"' end
    if t == "boolean" then return tostring(v) end
    if v[1] ~= nil or next(v) == nil then
        local out = {}; for i, x in ipairs(v) do out[i] = json(x) end; return "[" .. table.concat(out, ",") .. "]"
    end
    local out = {}; for _, k in ipairs(sorted(v)) do out[#out + 1] = json(k) .. ":" .. json(v[k]) end
    return "{" .. table.concat(out, ",") .. "}"
end
return json(models)
