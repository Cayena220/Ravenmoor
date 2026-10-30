-- 29 entries; the 19 level 1-20 spells have executable handlers in this alpha.
-- Motion is the wand gesture a spell is cast with, the Cast<Motion> clip (blender/animations/casting.py), whose wand
-- strikes CastTime after the cast is accepted. A spell's type gives it one unless the spell names its own. Spark
-- Bolt has none: Scintara's casts have clips of their own (EffectsController:CastBolt and the lance).
local spells = {}
local motions = {Projectile = "Thrust", Beam = "Zap", Area = "Dome", Self = "Ward", Target = "Mend", Summon = "Swirl", Object = "Twist"}
local function add(id, name, school, level, mana, cooldown, kind, damage, source, extra)
    local s = {Id = id, DisplayName = name, School = school, UnlockLevel = level,
        ManaCost = mana, Cooldown = cooldown, Type = kind, Damage = damage,
        Source = source, Range = 150, Speed = 120, Radius = 0.8,
        CastTime = 0.2, Implemented = level <= 20, Element = "Arcane", Motion = motions[kind]}
    for k, v in pairs(extra or {}) do s[k] = v end
    spells[id] = s
end
-- Scintara's Lance is the spark lance poured while the right mouse button is held (SpellService:Channel): mana to
-- light it, mana a second, a strike every Tick for Damage, and the cooldown once it stops. Slow scales walk speed.
add("Scintara", "Spark Bolt", "Hex", 1, 4, 0.6, "Projectile", 10, "Oakhart's first wand", {CastTime = 0.12, Motion = false,
    Lance = {Ignite = 5, Drain = 20, Tick = 0.2, Damage = 5, Range = 60, Radius = 0.5, Cooldown = 0.8, Slow = 0.6}})
add("Flamara", "Flame Lash", "Hex", 4, 15, 5, "Projectile", 18, "Hexcraft class", {Element = "Fire", Status = "Burn", Duration = 3, Dps = 4, Motion = "Lash"})
add("Frigora", "Frost Shard", "Hex", 8, 18, 6, "Projectile", 22, "Hexcraft class / Gloomspider tome", {Element = "Frost", Status = "Chilled", Duration = 2})
add("Ruptara", "Blast Hex", "Hex", 12, 25, 9, "Projectile", 30, "Hexcraft class", {Blast = 8, Motion = "Hurl"})
add("Tonitra", "Chain Lightning", "Hex", 15, 30, 10, "Beam", 26, "The Rotbark Seal quest", {Element = "Lightning", Story = true})
add("Vortexa", "Vortex Hex", "Hex", 25, 40, 18, "Area", 15, "Future: Hexcraft class")
add("Solarion", "Solar Nova", "Hex", 30, 70, 60, "Area", 80, "Future: Year 5 exam", {CastTime = 1})
add("Aegara", "Ward Shield", "Ward", 1, 12, 6, "Self", 0, "Oakhart's first wand", {Shield = 40, Duration = 2})
add("Speculo", "Mirror Ward", "Ward", 10, 20, 12, "Self", 0, "Warding class", {Duration = 0.6})
add("Durassa", "Stoneskin", "Ward", 18, 25, 20, "Self", 0, "Warding class", {Duration = 5})
add("Murallis", "Bastion Dome", "Ward", 20, 45, 30, "Area", 0, "First Mother Vexweave defeat", {Duration = 4, Story = true})
add("Custos Lumen", "Spirit Warden", "Ward", 30, 50, 90, "Summon", 0, "Future: Chapter 4")
add("Glimmora", "Light Orb", "Charm", 1, 5, 2, "Self", 0, "Oakhart's first wand", {Motion = "Swirl"})
add("Resero", "Unseal", "Charm", 3, 8, 3, "Object", 0, "Charms class", {Range = 35})
add("Velocis", "Swiftstep", "Charm", 5, 10, 12, "Self", 0, "Charms class", {Duration = 4, Motion = "Swirl"})
add("Excido", "Disarm", "Charm", 6, 18, 14, "Projectile", 8, "Duelmaster Vey at level 6", {Status = "Silenced", Duration = 1.5, Story = true})
add("Aerovanta", "Lift", "Charm", 9, 20, 12, "Projectile", 0, "Charms class", {Status = "Airborne", Duration = 1.5, Motion = "Uplift"})
add("Tractum", "Pull", "Charm", 14, 15, 10, "Beam", 0, "Restricted Shelf at level 14", {Story = true, Motion = "Pull"})
add("Translo", "Blink", "Charm", 22, 25, 14, "Self", 0, "Future: Charms class")
add("Vitara", "Mend", "Restoration", 3, 20, 8, "Target", 0, "Restoration class", {Heal = 25})
add("Purgo", "Cleanse", "Restoration", 11, 15, 15, "Target", 0, "Restoration class")
add("Renovo", "Renewal Aura", "Restoration", 24, 40, 30, "Area", 0, "Future: Restoration class")
add("Resurga", "Second Wind", "Restoration", 33, 60, 120, "Target", 0, "Future: Catacombs clear")
add("Saxifra", "Stone Bind", "Alteration", 7, 20, 12, "Projectile", 0, "Alteration class", {Status = "Rooted", Duration = 1.5, Motion = "Chop"})
add("Somnara", "Slumber", "Alteration", 16, 25, 16, "Projectile", 0, "Alteration class / Lanternwisp tome", {Status = "Asleep", Duration = 3, Motion = "Lull"})
add("Mutara", "Critter Curse", "Alteration", 28, 45, 25, "Projectile", 0, "Future: Alteration class")
add("Umbrexa", "Umbral Lash", "Shadow", 35, 30, 8, "Beam", 30, "Future: Marsh Hag")
add("Terrora", "Hex of Dread", "Shadow", 38, 35, 20, "Projectile", 0, "Future: Marsh Hag")
add("Animor", "Soul Siphon", "Shadow", 42, 50, 30, "Beam", 0, "Future: Marsh Hag")
return spells
