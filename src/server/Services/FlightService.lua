local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local Brooms = require(RS.Shared.BroomData)
-- Broom flight. The server decides who may fly and welds their broom (ReplicatedStorage.Brooms) under them; the
-- rider's own client flies the character, which it owns (FlightController). A rider is grounded by a hit, a duel,
-- crowd control, Whisperwood's sky or the ceiling.
local F = {}
function F:Init(services) self.S = services; self.Riders = {}; self.LastToggle = {} end
-- Whether `player` may take off now, and why not.
function F:CanFly(player)
    local d = self.S.PlayerDataService:Get(player); local s = self.S.CombatService.States[player]
    local root = self.S.WorldService:Root(player)
    if not d or not s or not root or s.Humanoid.Health <= 0 then return false end
    if not d.HasWand then return false, "Visit Oakhart in Hollowmere for your wand, and your first broom comes with it." end
    if self.S.DuelService:IsBusy(player) then return false, "Duels are fought on foot." end
    if not self.S.CombatService:CanAct(s) or self.S.CombatService:Has(s, "Rooted") then return false, "You can't take off right now." end
    if os.clock()-s.LastCombat < Brooms.CombatLockout then return false, "Catch your breath: you can fly a few seconds after combat." end
    if not self.S.WorldService:Zone(root.Position).Safe then return false, "Whisperwood's old wards keep brooms out of its sky." end
    return true
end
function F:Mount(player)
    local ok, reason = self:CanFly(player)
    if not ok then if reason then self.S.NetworkService:Notice(player, reason) end; return false end
    local d = self.S.PlayerDataService:Get(player); local s = self.S.CombatService.States[player]
    local folder = RS:FindFirstChild("Brooms"); local template = folder and folder:FindFirstChild(d.Broom)
    if not template or not template.PrimaryPart then
        self.S.NetworkService:Notice(player, "The brooms aren't in this place yet (blender/place_brooms.lua).")
        return false
    end
    local broom = template:Clone(); broom.Name = "RavenmoorBroom"
    local seat = broom.PrimaryPart
    -- The broom pivots on its seat, which sits on the shaft between the rider's legs.
    local weld = Instance.new("Weld"); weld.Name = "Seat"; weld.Part0 = s.Root; weld.Part1 = seat
    weld.C0 = CFrame.new(0, -Brooms.SeatDrop, 0); weld.C1 = seat.PivotOffset; weld.Parent = seat
    broom.Parent = s.Model
    self.Riders[player] = {Broom = d.Broom, Model = broom, Character = s.Model, Since = os.clock()}
    s.FlySpeed = Brooms.Brooms[d.Broom].Speed
    player:SetAttribute("Broom", d.Broom)
    return true
end
function F:Dismount(player, reason)
    local rider = self.Riders[player]; if not rider then return end
    self.Riders[player] = nil; self.LastToggle[player] = os.clock()
    rider.Model:Destroy()
    local s = self.S.CombatService.States[player]; if s then s.FlySpeed = nil end
    -- A rider still carries some speed for a moment after landing.
    local moved = self.S.WorldService.Movement[player]; if moved then moved.Grace = math.max(moved.Grace or 0, os.clock()+1.5) end
    player:SetAttribute("Broom", nil)
    if reason then self.S.NetworkService:Notice(player, reason) end
end
function F:Toggle(player)
    local now = os.clock()
    if now-(self.LastToggle[player] or -100) < Brooms.ToggleCooldown then return end
    self.LastToggle[player] = now
    if self.Riders[player] then self:Dismount(player) else self:Mount(player) end
end
function F:Choose(player, id)
    local d = self.S.PlayerDataService:Get(player); local broom = type(id) == "string" and Brooms.Brooms[id]
    if not d or not broom then return end
    if not Brooms.Unlocked(d, id) then return self.S.NetworkService:Notice(player, broom.Title.." unlocks at level "..broom.Level..".") end
    d.Broom = id; self.S.NetworkService:Sync(player)
    -- Swap brooms in the air.
    if self.Riders[player] and self.Riders[player].Broom ~= id then self:Dismount(player); self:Mount(player) end
end
-- Ground every rider who may no longer fly.
function F:Check()
    local combat = self.S.CombatService
    for player, rider in pairs(self.Riders) do
        local s = combat.States[player]
        if not player.Parent or not s or s.Model ~= rider.Character or not rider.Model.Parent or s.Humanoid.Health <= 0 then
            self:Dismount(player)
        elseif (s.HurtAt or 0) > rider.Since then self:Dismount(player, "The hit knocks you off your broom!")
        elseif self.S.DuelService:IsBusy(player) then self:Dismount(player, "Duels are fought on foot.")
        elseif not combat:CanAct(s) or combat:Has(s, "Rooted") then self:Dismount(player, "You tumble off your broom.")
        elseif not self.S.WorldService:Zone(s.Root.Position).Safe then self:Dismount(player, "Whisperwood's old wards pull you from the sky.")
        elseif s.Root.Position.Y > Brooms.Ceiling+25 then self:Dismount(player, "The air is too thin to fly this high.")
        end
    end
end
function F:Start()
    local net = self.S.NetworkService
    net.Handlers.Fly = function(player) self:Toggle(player) end
    net.Handlers.ChooseBroom = function(player, id) self:Choose(player, id) end
    Players.PlayerRemoving:Connect(function(player) self.Riders[player] = nil; self.LastToggle[player] = nil end)
    task.spawn(function()
        while true do task.wait(0.25); self:Check() end
    end)
end
return F
