local Shared = game:GetService("ReplicatedStorage").Shared
local Wands = require(Shared.WandData)
local Skills = require(Shared.SkillData)
local F = {}
function F.XP(level) return math.floor(100 * level ^ 1.5) end
-- Sums the equipped wand and learned skills into mods[Stat][Scope]; F.Mod reads them back.
function F.Mods(data)
    local mods = {}
    local function add(stat, scope, amount) local m = mods[stat] or {}; mods[stat] = m; m[scope] = (m[scope] or 0) + amount end
    local wand = data.Wands and data.Wands[data.EquippedWand]
    if wand and Wands.Valid(wand) then for _, e in ipairs(Wands.Effects(wand)) do add(e[1], e[2], e[3]) end end
    for id, rank in pairs(data.Talents or {}) do
        local t = Skills.Talents[id]; if t then for _, e in ipairs(t.Effects) do add(e[1], e[2], e[3]*rank) end end
    end
    return mods
end
function F.Mod(mods, stat, ...)
    local m = mods[stat]; if not m then return 0 end
    local total = m.All or 0
    for _, scope in ipairs({...}) do total = total + (m[scope] or 0) end
    return total
end
function F.Stats(data)
    local a = data.Attributes; local mods = F.Mods(data)
    local hp = 100 + 10 * data.Level + 10 * a.Vitality
    if data.House == "Stoneroot" then hp = hp * 1.05 end
    return {HP = math.floor(hp * (1 + F.Mod(mods, "Health"))), Mana = (100 + 2 * data.Level + 5 * a.Focus) * (1 + F.Mod(mods, "Mana")),
        ManaRegen = (4 + 0.2 * a.Focus) * (1 + F.Mod(mods, "Regen")), Speed = 16 * (1 + math.min(0.15, 0.0025 * a.Agility)),
        Crit = math.min(0.4, math.min(0.25, 0.05 + 0.002 * a.Agility) + F.Mod(mods, "Crit")),
        Guard = math.min(0.15, F.Mod(mods, "Guard"))}
end
function F.Mastery(hits)
    if hits >= 300 then return 5 elseif hits >= 150 then return 4 elseif hits >= 75 then return 3 elseif hits >= 25 then return 2 end
    return 1
end
function F.Power(base, data, spell, spoken)
    local mastery = data.Spells[spell.Id] and data.Spells[spell.Id].Mastery or 1
    local mods = F.Mods(data)
    local bonus = 0
    if spell.Damage > 0 then
        bonus = bonus + F.Mod(mods, "Damage", spell.School, spell.Element)
        if data.House == "Emberclaw" then bonus = bonus + 0.05 end
    end
    if spell.Shield then
        bonus = bonus + F.Mod(mods, "Shield")
        if data.House == "Stoneroot" then bonus = bonus + 0.05 end
    end
    if spell.Heal then bonus = bonus + F.Mod(mods, "Heal") end
    return base * (1 + 0.08 * (data.Level - 1)) * (1 + 0.02 * data.Attributes.Power)
        * (1 + 0.05 * (mastery - 1)) * (1 + bonus) * (spoken and 1.1 or 1)
end
function F.Cooldown(spell, data)
    return spell.Cooldown * (data.House == "Skyquill" and 0.95 or 1) * (1 - math.min(0.4, F.Mod(F.Mods(data), "Cooldown", spell.School)))
end
function F.ManaCost(spell, data) return spell.ManaCost * (1 - math.min(0.4, F.Mod(F.Mods(data), "ManaCost", spell.School))) end
function F.Duration(spell, data) return (spell.Duration or 0) * (1 + F.Mod(F.Mods(data), "Duration", spell.School)) end
function F.Monster(level, rank)
    local hp = rank == "Boss" and 15 or (rank == "Elite" and 3 or 1)
    local damage = rank == "Boss" and 2.5 or (rank == "Elite" and 1.5 or 1)
    local xp = rank == "Boss" and 25 or (rank == "Elite" and 4 or 1)
    local gold = rank == "Boss" and 50 or (rank == "Elite" and 5 or 1)
    return {HP = (50 + 25 * level) * hp, Damage = (5 + 2 * level) * damage,
        XP = (10 + 5 * level) * xp, Gilders = 2 + level * gold}
end
function F.Elo(rating, opponent, games, result)
    return math.floor(rating + (games < 10 and 48 or 32) * (result - 1 / (1 + 10 ^ ((opponent - rating) / 400))) + 0.5)
end
function F.CCMult(count) return ({1, 0.5, 0.25})[count] or 0 end
function F.Finite(n) return type(n) == "number" and n == n and math.abs(n) < 10000000 end
return F
