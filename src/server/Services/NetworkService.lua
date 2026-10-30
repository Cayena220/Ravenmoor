local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local N = {}
function N:Init(services)
    self.S = services; self.Buckets = {}; self.Handlers = {}
    self.Folder = Instance.new("Folder"); self.Folder.Name = "Remotes"; self.Folder.Parent = RS
    for _, name in ipairs({"Cast", "Channel", "Action", "Gesture", "Profile", "State", "UI", "CastReply"}) do
        local r = Instance.new("RemoteEvent"); r.Name = name; r.Parent = self.Folder; self[name] = r
    end
    for _, name in ipairs({"Aim", "FX"}) do
        local r = Instance.new("UnreliableRemoteEvent"); r.Name = name; r.Parent = self.Folder; self[name] = r
    end
end
function N:Allow(player, key, rate, burst)
    local user = self.Buckets[player] or {}; self.Buckets[player] = user
    local t = os.clock(); local b = user[key] or {Time = t, Tokens = burst}; user[key] = b
    b.Tokens = math.min(burst, b.Tokens + (t-b.Time)*rate); b.Time = t
    if b.Tokens < 1 then return false end
    b.Tokens = b.Tokens-1; return true
end
function N:Bind(name, rate, burst, callback)
    self[name].OnServerEvent:Connect(function(player, ...)
        if not self:Allow(player, name, rate, burst) then return end
        callback(player, ...)
    end)
end
function N:Notice(player, text)
    if player.Parent then self.UI:FireClient(player, "Toast", text) end
end
function N:Sync(player)
    local data = self.S.PlayerDataService:Get(player)
    if data and player.Parent then self.Profile:FireClient(player, data) end
end
function N:Start()
    self:Bind("Action", 5, 10, function(player, action, a, b)
        if type(action) ~= "string" or #action > 32 then return end
        local fn = self.Handlers[action]; if fn then fn(player, a, b) end
    end)
    self.Handlers.Ready = function(player) self:Sync(player) end
    Players.PlayerRemoving:Connect(function(player) self.Buckets[player] = nil end)
end
return N
