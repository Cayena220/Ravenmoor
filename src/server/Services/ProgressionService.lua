local RS = game:GetService("ReplicatedStorage")
local Config = require(RS.Shared.Config)
local F = require(RS.Shared.Formulas)
local Spells = require(RS.Shared.SpellData)
local Quests = require(RS.Shared.QuestData)
local Skills = require(RS.Shared.SkillData)
local P = {}
function P:Init(services) self.S = services; self.HouseTotals = {}; for house in pairs(Config.Houses) do self.HouseTotals[house] = 0 end end
function P:Refresh(player)
    local d = self.S.PlayerDataService:Get(player); if not d then return end
    if player:FindFirstChild("leaderstats") then
        for _, v in ipairs(player.leaderstats:GetChildren()) do v.Value = d[v.Name] end
    end
    player:SetAttribute("House", d.House)
    player:SetAttribute("Level", d.Level)
    self.S.CombatService:HouseTrim(player)
    if d.SealDefeated and d.Level >= 15 then self:Learn(player, "Tonitra", true) end
    if d.BossDefeated and d.Level >= 20 then self:Learn(player, "Murallis", true) end
    self.S.NetworkService:Sync(player)
end
function P:Learn(player, id, quiet)
    local d = self.S.PlayerDataService:Get(player); local sp = Spells[id]
    if not d or not sp or not sp.Implemented or d.Level < sp.UnlockLevel or d.Spells[id] then return false end
    d.Spells[id] = {Mastery = 1, Hits = 0}
    if id ~= "Scintara" and id ~= "Aegara" then
        for i = 1,4 do local key = "Slot"..i; if d.Loadout[key] == "" then d.Loadout[key] = id; break end end
    end
    if not quiet then self.S.NetworkService:Notice(player, "Learned " .. sp.DisplayName .. " · " .. id) end
    self.S.NetworkService:Sync(player)
    return true
end
function P:Award(player, xp, gilders)
    local d = self.S.PlayerDataService:Get(player); if not d then return end
    d.XP = d.XP + xp; d.Gilders = d.Gilders + gilders
    local levelled = false
    while d.Level < Config.LevelCap and d.XP >= F.XP(d.Level) do
        d.XP = d.XP - F.XP(d.Level); d.Level = d.Level+1
        d.Attributes.Unspent = d.Attributes.Unspent+2; levelled = true
    end
    if d.Level == Config.LevelCap then d.XP = math.min(d.XP, F.XP(d.Level)) end
    if levelled then
        self.S.NetworkService:Notice(player, "Level " .. d.Level .. "! Spend attribute points in your journal and skill points under Skills.")
        self.S.CombatService:UpdateStats(player, true)
    end
    self:Refresh(player)
end
function P:HousePoints(player, amount)
    local d = self.S.PlayerDataService:Get(player); if not d or d.House == "" then return end
    d.HousePoints = d.HousePoints + amount
    self.HouseTotals[d.House] = self.HouseTotals[d.House] + amount
    self:Refresh(player)
end
function P:Event(player, kind, target)
    local d = self.S.PlayerDataService:Get(player); if not d then return end
    local q = Quests[d.Quest]
    if q and q.Kind == kind and (not q.Target or q.Target == target) then
        d.QuestProgress = d.QuestProgress+1
        if d.QuestProgress >= q.Need then
            d.QuestDone[q.Id] = true; d.Quest = d.Quest+1; d.QuestProgress = 0
            self.S.NetworkService:Notice(player, "Quest complete: " .. q.Title .. "  +" .. q.XP .. " XP")
            self:Award(player, q.XP, q.Gold)
            if q.Wand and not d.WandRewards[q.Wand] then
                d.WandRewards[q.Wand] = true
                self.S.WandService:GrantNamed(player, q.Wand, "Quest reward: %s. Equip it from your bag.")
            end
        end
    end
    if kind == "Kill" then
        local day = math.floor(os.time()/86400)
        if d.Daily.Day ~= day then d.Daily = {Day = day, Kills = 0, Claimed = false} end
        d.Daily.Kills = math.min(15, d.Daily.Kills+1)
        if d.Daily.Kills == 15 and not d.Daily.Claimed then
            d.Daily.Claimed = true; self:Award(player, 600, 120); self:HousePoints(player, 10)
            self.S.NetworkService:Notice(player, "Daily complete · 15 woodland foes defeated")
        end
    end
    self:Refresh(player)
end
function P:Hit(player, id)
    local d = self.S.PlayerDataService:Get(player); local s = d and d.Spells[id]; if not s then return end
    s.Hits = s.Hits+1; local m = F.Mastery(s.Hits)
    if m > s.Mastery then s.Mastery = m; self.S.NetworkService:Notice(player, id.." reached Mastery "..m); self:Refresh(player) end
end
function P:Talent(player, id)
    local d = self.S.PlayerDataService:Get(player)
    if not d or type(id) ~= "string" or self.S.DuelService:IsBusy(player) then return false end
    local ok, reason = Skills.CanLearn(d, id)
    if not ok then self.S.NetworkService:Notice(player, reason); return false end
    d.Talents[id] = (d.Talents[id] or 0) + 1
    local t = Skills.Talents[id]
    self.S.NetworkService:Notice(player, t.Name .. " · rank " .. d.Talents[id] .. " / " .. t.MaxRank)
    self.S.CombatService:UpdateStats(player, false); self:Refresh(player)
    return true
end
function P:Combo(player, combo)
    local d = self.S.PlayerDataService:Get(player); if not d or d.Combos[combo] then return end
    d.Combos[combo] = true; self.S.NetworkService:Notice(player, "Combo discovered: " .. combo); self:Refresh(player)
end
function P:Start()
    self.S.NetworkService.Handlers.Loadout = function(player, slot, id)
        local d = self.S.PlayerDataService:Get(player)
        if not d or type(slot) ~= "string" or type(id) ~= "string" or not d.Spells[id] then return end
        if slot ~= "Ward" and not slot:match("^Slot[1-4]$") then return end
        if slot == "Ward" and Spells[id].School ~= "Ward" then return end
        d.Loadout[slot] = id; self:Refresh(player)
    end
    self.S.NetworkService.Handlers.Attribute = function(player, name)
        local d = self.S.PlayerDataService:Get(player)
        if not d or not ({Power=true, Focus=true, Vitality=true, Agility=true})[name] or d.Attributes.Unspent < 1 then return end
        d.Attributes.Unspent = d.Attributes.Unspent-1; d.Attributes[name] = d.Attributes[name]+1
        self.S.CombatService:UpdateStats(player, false); self:Refresh(player)
    end
    self.S.NetworkService.Handlers.Talent = function(player, id) self:Talent(player, id) end
    self.S.NetworkService.Handlers.Setting = function(player, key, value)
        local d = self.S.PlayerDataService:Get(player)
        if not d or (key ~= "SpokenCasting" and key ~= "ReducedEffects") or type(value) ~= "boolean" then return end
        d.Settings[key] = value; self:Refresh(player)
    end
end
return P
