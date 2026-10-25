-- Skill tree: one point per level after level 1. Deeper tiers need points already spent in that school.
-- Effects are {Stat, Scope, Amount per rank}; Formulas.Mods sums them with the equipped wand's effects.
local S = {Schools = {"Hex", "Ward", "Charm", "Restoration", "Alteration"}, Talents = {}, Order = {}, Requires = {0, 3, 6}}
local function add(id, school, name, tier, maxRank, text, effects)
    S.Talents[id] = {Id = id, School = school, Name = name, Tier = tier, MaxRank = maxRank, Text = text, Effects = effects, Requires = S.Requires[tier]}
    S.Order[school] = S.Order[school] or {}
    table.insert(S.Order[school], id)
end
add("SearingFocus", "Hex", "Searing Focus", 1, 3, "+3% Hex damage per rank.", {{"Damage", "Hex", 0.03}})
add("ElementalAttunement", "Hex", "Elemental Attunement", 1, 3, "+3% Fire, Frost and Lightning damage per rank.", {{"Damage", "Fire", 0.03}, {"Damage", "Frost", 0.03}, {"Damage", "Lightning", 0.03}})
add("QuickenedHexes", "Hex", "Quickened Hexes", 2, 2, "-5% Hex cooldowns per rank.", {{"Cooldown", "Hex", 0.05}})
add("Overload", "Hex", "Overload", 3, 1, "+5% critical chance.", {{"Crit", "All", 0.05}})
add("ThickWards", "Ward", "Thick Wards", 1, 3, "+8% ward shield strength per rank.", {{"Shield", "All", 0.08}})
add("SteadyStance", "Ward", "Steady Stance", 1, 3, "-2% damage taken per rank.", {{"Guard", "All", 0.02}})
add("WardensRhythm", "Ward", "Warden's Rhythm", 2, 2, "-6% Ward cooldowns per rank.", {{"Cooldown", "Ward", 0.06}})
add("Bulwark", "Ward", "Bulwark", 3, 1, "+8% maximum health.", {{"Health", "All", 0.08}})
add("NimbleCharms", "Charm", "Nimble Charms", 1, 3, "-4% Charm cooldowns per rank.", {{"Cooldown", "Charm", 0.04}})
add("EfficientCasting", "Charm", "Efficient Casting", 1, 3, "-3% mana cost of all spells per rank.", {{"ManaCost", "All", 0.03}})
add("LingeringCharms", "Charm", "Lingering Charms", 2, 2, "+10% Charm effect duration per rank.", {{"Duration", "Charm", 0.10}})
add("DeepReserves", "Charm", "Deep Reserves", 3, 1, "+10% maximum mana and mana regeneration.", {{"Mana", "All", 0.10}, {"Regen", "All", 0.10}})
add("GentleHands", "Restoration", "Gentle Hands", 1, 3, "+8% healing per rank.", {{"Heal", "All", 0.08}})
add("VitalFlow", "Restoration", "Vital Flow", 1, 3, "+5% mana regeneration per rank.", {{"Regen", "All", 0.05}})
add("RenewingSpirit", "Restoration", "Renewing Spirit", 2, 2, "+3% maximum health per rank.", {{"Health", "All", 0.03}})
add("Lifebloom", "Restoration", "Lifebloom", 3, 1, "+15% healing and -10% Restoration cooldowns.", {{"Heal", "All", 0.15}, {"Cooldown", "Restoration", 0.10}})
add("BindingMastery", "Alteration", "Binding Mastery", 1, 3, "+6% Alteration effect duration per rank.", {{"Duration", "Alteration", 0.06}})
add("Stonecaller", "Alteration", "Stonecaller", 1, 3, "-6% Alteration mana cost per rank.", {{"ManaCost", "Alteration", 0.06}})
add("PatientWeaving", "Alteration", "Patient Weaving", 2, 2, "-6% Alteration cooldowns per rank.", {{"Cooldown", "Alteration", 0.06}})
add("Dreamweaver", "Alteration", "Dreamweaver", 3, 1, "+8% duration for every effect you apply.", {{"Duration", "All", 0.08}})

function S.Points(level) return math.max(0, level-1) end
function S.Spent(talents, school)
    local total = 0
    for id, rank in pairs(talents) do local t = S.Talents[id]; if t and (not school or t.School == school) then total = total+rank end end
    return total
end
function S.CanLearn(data, id)
    local t = S.Talents[id]; if not t then return false, "Unknown skill." end
    local rank = data.Talents[id] or 0
    if rank >= t.MaxRank then return false, t.Name .. " is already mastered." end
    if S.Spent(data.Talents) >= S.Points(data.Level) then return false, "No skill points left. You earn one each level." end
    if S.Spent(data.Talents, t.School) < t.Requires then return false, "Spend " .. t.Requires .. " points in " .. t.School .. " first." end
    return true
end
-- Saved data repair: unknown skills are dropped and ranks clamped; an overspent tree is refunded.
function S.Sanitize(data)
    for id, rank in pairs(data.Talents) do
        local t = S.Talents[id]
        if not t or type(rank) ~= "number" or rank ~= rank or rank < 1 then data.Talents[id] = nil else data.Talents[id] = math.min(t.MaxRank, math.floor(rank)) end
    end
    if S.Spent(data.Talents) > S.Points(data.Level) then data.Talents = {} end
end
return S
