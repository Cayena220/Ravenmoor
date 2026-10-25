local Players = game:GetService("Players")
Players.CharacterAutoLoads = false
local order = {"NetworkService", "PlayerDataService", "ProgressionService", "WorldService",
    "CombatService", "SpellService", "MonsterService", "ClassService", "DuelService", "WandService", "InteractionService"}
local services = {}
for _, name in ipairs(order) do services[name] = require(script.Parent.Services[name]) end
for _, name in ipairs(order) do services[name]:Init(services) end
for _, name in ipairs(order) do if name ~= "PlayerDataService" then services[name]:Start() end end
services.PlayerDataService:Start()
workspace:SetAttribute("WandboundReady", true)
print("[Wandbound] Ravenmoor Academy 0.1.0 ready")
