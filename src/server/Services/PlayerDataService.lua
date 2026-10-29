local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local DataStoreService = game:GetService("DataStoreService")
local HttpService = game:GetService("HttpService")
local Shared = game:GetService("ReplicatedStorage").Shared
local Config = require(Shared.Config)
local SpellData = require(Shared.SpellData)
local WandData = require(Shared.WandData)
local SkillData = require(Shared.SkillData)
local BroomData = require(Shared.BroomData)
local D = {}
local function clone(value)
    if type(value) ~= "table" then return value end
    local copy = {}; for k,v in pairs(value) do copy[k] = clone(v) end; return copy
end
local function template()
    return {Version = 1, Level = 1, XP = 0, House = "", HousePoints = 0, Gilders = 0, BankGilders = 0,
        Attributes = {Power = 0, Focus = 0, Vitality = 0, Agility = 0, Unspent = 0},
        Spells = {}, Loadout = {Ward = "Aegara", Slot1 = "Glimmora", Slot2 = "", Slot3 = "", Slot4 = ""},
        HasWand = false, Wand = "", Quest = 1, QuestProgress = 0, QuestDone = {},
        Inventory = {}, Combos = {}, LastWaystone = "Hollowmere", Waystones = {Hollowmere = true},
        Daily = {Day = 0, Kills = 0, Claimed = false}, DuelWins = 0,
        Settings = {SpokenCasting = true, ReducedEffects = false},
        BossDefeated = false, SealDefeated = false, LessonRewards = {}, LastRespec = 0,
        Wands = {}, EquippedWand = 0, WandsHeld = {}, WandRewards = {}, Talents = {}, LastTalentReset = 0,
        Broom = BroomData.Default}
end
local function reconcile(data, defaults)
    for k,v in pairs(defaults) do
        if data[k] == nil or type(data[k]) ~= type(v) then data[k] = clone(v)
        elseif type(v) == "table" then reconcile(data[k], v) end
    end
end
function D:Init(services)
    self.S = services; self.Profiles = {}; self.Loading = {}; self.Closing = false
    self.SessionId = game.JobId ~= "" and game.JobId or HttpService:GenerateGUID(false)
    self.Ephemeral = RunService:IsStudio() and not Config.StudioSaves
    if not self.Ephemeral then self.Store = DataStoreService:GetDataStore(Config.DataStoreName) end
end
function D:Get(player)
    local p = self.Profiles[player]
    if p and not p.Closing then return p.Data end
    return nil
end
function D:Load(player)
    if self.Loading[player] or self.Profiles[player] or self.Closing then return end
    self.Loading[player] = true
    local data
    if self.Ephemeral then data = template() else
        for attempt = 1, 3 do
            local ok, result = pcall(function()
                return self.Store:UpdateAsync("Player_" .. player.UserId, function(old)
                    if old and old.Session and old.Session.Id ~= self.SessionId and old.Session.Expires > os.time() then return nil end
                    return {Data = old and old.Data or template(), Session = {Id = self.SessionId, Expires = os.time() + Config.LockLifetime}}
                end)
            end)
            if ok and result and result.Session and result.Session.Id == self.SessionId then data = result.Data; break end
            if attempt < 3 then task.wait(attempt * 2) end
        end
    end
    self.Loading[player] = nil
    if not data then
        if player.Parent then player:Kick("Your progress could not be opened safely. Please rejoin in a moment.") end
        return
    end
    reconcile(data, template())
    data.Level = math.clamp(math.floor(data.Level), 1, Config.LevelCap)
    for id in pairs(data.Spells) do if not SpellData[id] then data.Spells[id] = nil end end
    WandData.Sanitize(data); SkillData.Sanitize(data); BroomData.Sanitize(data)
    local profile = {Data = data, SavedAt = os.time(), Busy = false, Closing = false}
    self.Profiles[player] = profile
    if not player.Parent or self.Closing then self:Release(player); return end
    player:SetAttribute("SessionOnly", self.Ephemeral)
    player:SetAttribute("DataReady", true)
    local stats = Instance.new("Folder"); stats.Name = "leaderstats"; stats.Parent = player
    for _, name in ipairs({"Level", "Gilders", "HousePoints"}) do local v = Instance.new("IntValue"); v.Name = name; v.Value = data[name]; v.Parent = stats end
    self.S.ProgressionService:Refresh(player)
    self.S.CombatService:BindPlayer(player)
    player:LoadCharacterAsync()
    self.S.NetworkService:Sync(player)
end
function D:Save(player, release)
    local p = self.Profiles[player]; if not p then return true end
    local deadline = os.clock() + 22
    while p.Busy and os.clock() < deadline do task.wait(0.1) end
    if p.Busy then return false end
    p.Busy = true
    if self.Ephemeral then p.Busy = false; return true end
    local snapshot = clone(p.Data)
    local success = false
    for attempt = 1, 3 do
        local ok, result = pcall(function()
            return self.Store:UpdateAsync("Player_" .. player.UserId, function(old)
                -- Never overwrite a profile whose lock another server owns.
                if not old or not old.Session or old.Session.Id ~= self.SessionId then return nil end
                local nextSession = nil
                if not release then nextSession = {Id = self.SessionId, Expires = os.time() + Config.LockLifetime} end
                return {Data = snapshot, Session = nextSession}
            end)
        end)
        if ok and result then success = true; p.SavedAt = os.time(); break end
        if ok and not result then break end -- Lost lock; do not retry a stale writer.
        if attempt < 3 then task.wait(attempt) end
    end
    p.Busy = false
    if not success then
        warn("[Wandbound] Save unavailable for user", player.UserId)
        if player.Parent then self.S.NetworkService:Notice(player, "Saving is temporarily unavailable. Please stay connected.") end
    end
    return success
end
function D:Release(player)
    local p = self.Profiles[player]; if not p or p.Releasing then return end
    p.Releasing = true; p.Closing = true
    self:Save(player, true)
    self.Profiles[player] = nil
end
function D:Start()
    Players.PlayerAdded:Connect(function(player) self:Load(player) end)
    Players.PlayerRemoving:Connect(function(player) self:Release(player) end)
    for _, player in ipairs(Players:GetPlayers()) do task.spawn(function() self:Load(player) end) end
    task.spawn(function()
        while not self.Closing do
            task.wait(Config.SaveInterval)
            for player, p in pairs(self.Profiles) do
                if not p.Closing then task.spawn(function() self:Save(player, false) end) end
            end
        end
    end)
    task.spawn(function()
        while not self.Closing do
            task.wait(5)
            for player,p in pairs(self.Profiles) do
                if not self.Ephemeral and not p.Closing and os.time()-p.SavedAt > Config.LockLifetime-30 then
                    p.Closing = true
                    player:Kick("Saving has been unavailable too long. Rejoin shortly to protect your saved progress.")
                end
            end
        end
    end)
    game:BindToClose(function()
        self.Closing = true
        local pending = 0
        for player in pairs(self.Profiles) do
            pending = pending + 1
            task.spawn(function() self:Release(player); pending = pending-1 end)
        end
        local untilTime = os.clock() + 25
        while pending > 0 and os.clock() < untilTime do task.wait(0.1) end
    end)
end
return D
