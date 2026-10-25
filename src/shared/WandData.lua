-- Wand catalogue. A wand is {Wood, Core, Rarity}; wood and core each grant one small bonus.
-- Effects use the same {Stat, Scope, Amount} shape as skill tree effects (see Formulas.Mods).
-- A named wand also carries Named = <key of W.Named>: fixed parts, a Body (WandModel) and a Signature (combat hooks).
local W = {Capacity = 10, Price = 200}
W.Woods = {
    Ash = {Color = {198, 170, 128}, Length = 2.1, Thickness = 0.15, Effect = {"Damage", "All", 0.03}},
    Willow = {Color = {164, 150, 108}, Length = 2.3, Thickness = 0.13, Effect = {"Heal", "All", 0.06}},
    Rowan = {Color = {140, 84, 62}, Length = 2.0, Thickness = 0.15, Effect = {"Cooldown", "All", 0.03}},
    Blackthorn = {Color = {52, 44, 42}, Length = 2.0, Thickness = 0.15, Thorns = true, Effect = {"Crit", "All", 0.02}},
    Silverbirch = {Color = {222, 220, 208}, Length = 2.2, Thickness = 0.14, Knots = true, Effect = {"ManaCost", "All", 0.04}},
    Ironoak = {Color = {92, 78, 64}, Length = 1.9, Thickness = 0.19, Effect = {"Shield", "All", 0.06}},
    Heartwood = {Color = {184, 112, 58}, Length = 1.9, Thickness = 0.18, Knots = true, Effect = {"Regen", "All", 0.05}},
}
W.Cores = {
    Emberplume = {Color = {255, 140, 64}, Effect = {"Damage", "Fire", 0.05}},
    Frostfang = {Color = {140, 220, 255}, Effect = {"Damage", "Frost", 0.05}},
    Stormglass = {Color = {255, 232, 120}, Effect = {"Damage", "Lightning", 0.05}},
    Wyrmscale = {Color = {200, 90, 255}, Effect = {"Damage", "Arcane", 0.04}},
    Moonmane = {Color = {200, 210, 255}, Effect = {"Duration", "All", 0.06}},
    Vexfang = {Color = {232, 72, 154}, Effect = {"Duration", "Alteration", 0.06}},
}
W.Rarities = {
    Common = {Scale = 1, Weight = 65, Metal = {111, 78, 43}},
    Uncommon = {Scale = 1.5, Weight = 28, Metal = {202, 160, 83}},
    Rare = {Scale = 2, Weight = 7, Metal = {214, 220, 228}},
    Epic = {Scale = 2.5, Weight = 0, Metal = {172, 140, 214}},
}
W.Trims = {Leaf = {110, 158, 74}, Silk = {235, 230, 218}}
-- Heartwood, Vexfang and Epic (weight 0) belong to named wands only, so shop rolls never produce them.
W.Named = {
    Stormfork = {Title = "Stormfork", Wood = "Rowan", Core = "Stormglass", Rarity = "Uncommon", Body = "Forked",
        Signature = "Static", Note = "Static: every 4th Spark Bolt arcs to a second enemy"},
    Hearthroot = {Title = "Hearthroot", Wood = "Heartwood", Core = "Moonmane", Rarity = "Rare", Body = "Sprout",
        Signature = "Sapflow", Note = "Sapflow: each Mend that heals refunds 6 mana",
        Recipe = {Level = 18, Gilders = 600, Items = {Heartwood = 3}}},
    WidowsBite = {Title = "Widow's Bite", Wood = "Blackthorn", Core = "Vexfang", Rarity = "Epic", Body = "Fang", Length = 2.4,
        Signature = "VenomBite", Note = "Venom Bite: ×2 crits on Rooted or Asleep enemies",
        Recipe = {Level = 1, Gilders = 0, Items = {["Widow's Bite trophy"] = 5}}},
}
W.WoodOrder = {"Ash", "Willow", "Rowan", "Blackthorn", "Silverbirch", "Ironoak"}
W.CoreOrder = {"Emberplume", "Wyrmscale", "Moonmane", "Stormglass", "Frostfang"}
W.RarityOrder = {"Common", "Uncommon", "Rare", "Epic"}
W.NamedOrder = {"Stormfork", "Hearthroot", "WidowsBite"}
local labels = {Damage = "damage", Heal = "healing", Cooldown = "cooldowns", Crit = "critical chance",
    ManaCost = "mana costs", Shield = "ward strength", Duration = "effect duration", Regen = "mana regeneration"}

function W.Valid(wand)
    if type(wand) ~= "table" or W.Woods[wand.Wood] == nil or W.Cores[wand.Core] == nil or W.Rarities[wand.Rarity] == nil then return false end
    local named = wand.Named == nil or W.Named[wand.Named]
    return named == true or (named ~= nil and named.Wood == wand.Wood and named.Core == wand.Core and named.Rarity == wand.Rarity)
end
function W.Make(id)
    local n = W.Named[id]
    return {Wood = n.Wood, Core = n.Core, Rarity = n.Rarity, Named = id}
end
function W.Length(wand)
    local n = wand.Named and W.Named[wand.Named]
    return n and n.Length or W.Woods[wand.Wood].Length
end
-- The equipped wand's signature ("Static", "Sapflow" or "VenomBite"), or nil.
function W.Signature(data)
    local wand = data and data.Wands and data.Wands[data.EquippedWand]
    local n = wand and wand.Named and W.Named[wand.Named]
    return n and n.Signature
end
function W.Effects(wand)
    local scale = W.Rarities[wand.Rarity].Scale
    local list = {}
    for _, e in ipairs({W.Woods[wand.Wood].Effect, W.Cores[wand.Core].Effect}) do list[#list+1] = {e[1], e[2], e[3]*scale} end
    return list
end
function W.Name(wand)
    if wand.Named then return W.Named[wand.Named].Title .. " · " .. wand.Rarity .. " " .. wand.Wood .. " wand" end
    return wand.Rarity .. " " .. wand.Wood .. " wand · " .. wand.Core .. " core"
end
function W.Label(wand) return wand.Named and W.Named[wand.Named].Title or wand.Wood .. " / " .. wand.Core end
function W.Describe(wand)
    local parts = {}
    for _, e in ipairs(W.Effects(wand)) do
        local reduce = e[1] == "Cooldown" or e[1] == "ManaCost"
        local scope = e[2] ~= "All" and e[2] .. " " or ""
        parts[#parts+1] = string.format("%s%g%% %s%s", reduce and "-" or "+", math.floor(e[3]*1000+0.5)/10, scope, labels[e[1]])
    end
    local text = table.concat(parts, "  ·  ")
    return wand.Named and text .. "\n" .. W.Named[wand.Named].Note or text
end
function W.RollRarity()
    local total = 0; for _, id in ipairs(W.RarityOrder) do total = total + W.Rarities[id].Weight end
    local roll = math.random()*total
    for _, id in ipairs(W.RarityOrder) do roll = roll - W.Rarities[id].Weight; if roll < 0 then return id end end
    return "Common"
end
function W.Roll(rarity)
    return {Wood = W.WoodOrder[math.random(#W.WoodOrder)], Core = W.CoreOrder[math.random(#W.CoreOrder)], Rarity = rarity or W.RollRarity()}
end
-- Saved data repair: drops unknown wands, converts the old "Wood / Core" text wand, clamps the equipped index.
function W.Sanitize(data)
    for i = #data.Wands, 1, -1 do if not W.Valid(data.Wands[i]) then table.remove(data.Wands, i) end end
    while #data.Wands > W.Capacity do table.remove(data.Wands) end
    if data.WandsHeld then for i = #data.WandsHeld, 1, -1 do if not W.Named[data.WandsHeld[i]] then table.remove(data.WandsHeld, i) end end end
    if data.HasWand and #data.Wands == 0 then
        local wood, core = data.Wand:match("^(%a+) / (%a+)$")
        data.Wands[1] = W.Woods[wood] and W.Cores[core] and {Wood = wood, Core = core, Rarity = "Common"} or W.Roll("Common")
    end
    if data.EquippedWand % 1 ~= 0 or data.EquippedWand < 1 or data.EquippedWand > #data.Wands then data.EquippedWand = #data.Wands > 0 and 1 or 0 end
    data.Wand = data.Wands[data.EquippedWand] and W.Label(data.Wands[data.EquippedWand]) or ""
end
return W
