local Players = game:GetService("Players")
local Lighting = game:GetService("Lighting")
local Config = require(game:GetService("ReplicatedStorage").Shared.Config)
local W = {}
function W:Init(services)
    self.S = services; self.Markers = workspace:WaitForChild("Markers"); self.Movement = {}
    self.Runtime = Instance.new("Folder"); self.Runtime.Name = "Runtime"; self.Runtime.Parent = workspace
    self.Monsters = Instance.new("Folder"); self.Monsters.Name = "Monsters"; self.Monsters.Parent = self.Runtime
    self.Targets = Instance.new("Folder"); self.Targets.Name = "Targets"; self.Targets.Parent = self.Runtime
end
function W:Root(player)
    return player.Character and player.Character:FindFirstChild("HumanoidRootPart")
end
function W:Zone(position)
    for _, z in ipairs(Config.Zones) do
        if math.abs(position.X-z.Center[1]) <= z.Size[1]/2 and math.abs(position.Z-z.Center[2]) <= z.Size[2]/2 then return z end
    end
    return {Id = "Grounds", Name = "Castle Grounds", Safe = true}
end
function W:Anchor(name) return self.Markers:FindFirstChild(name) end
function W:Near(player, anchor, range)
    local root = self:Root(player); local marker = type(anchor) == "string" and self:Anchor(anchor) or anchor
    local s = self.S.CombatService.States[player]
    return root and marker and s and s.Humanoid.Health > 0 and (root.Position-marker.Position).Magnitude <= (range or 15)
end
function W:Teleport(player, position)
    local root = self:Root(player); if not root then return end
    self.Movement[player] = {Pos = position, Time = os.clock(), Grace = os.clock()+2}
    player.Character:PivotTo(CFrame.new(position))
    root.AssemblyLinearVelocity = Vector3.zero
end
-- Portal parts: the academy's door and the way back, installed with the WorldPlan map, and the doors between each
-- house's common room and its dormitories (blender/place_dormitory_doors.lua). Older maps have neither.
function W:StartPortals()
    local cooldown, pending={},{}
    Players.PlayerRemoving:Connect(function(player) cooldown[player]=nil; pending[player]=nil end)
    for _,name in ipairs({"AcademyPortals","DormitoryDoors"}) do
        local portals=workspace:FindFirstChild(name)
        for _,portal in ipairs(portals and portals:GetChildren() or {}) do
            local destination=portal:IsA("BasePart") and portal:FindFirstChild("Destination")
            if destination and destination:IsA("CFrameValue") then self:Portal(portal,destination,cooldown,pending,name=="DormitoryDoors") end
        end
    end
end
-- A portal part sends a student who uses its prompt to its Destination. The academy's door also sends one who walks
-- into it. A dormitory door stands against a wall students walk along, with its partner just behind that wall, so it
-- answers only its prompt, and only in sight of it.
function W:Portal(portal,destination,cooldown,pending,door)
    local function enter(player)
        if pending[player] or os.clock()<(cooldown[player] or 0) then return end
        local root=self:Root(player)
        if not root or not self:Near(player,portal,18) or self.S.DuelService:IsBusy(player) then return end
        pending[player]=true
        local character=player.Character
        if workspace.StreamingEnabled then pcall(function() player:RequestStreamAroundAsync(destination.Value.Position,5) end) end
        if player.Character==character and self:Near(player,portal,18) then
            self.S.ClassService:Cancel(player)
            self:Teleport(player,destination.Value.Position)
            character:PivotTo(destination.Value)
            local moved=self:Root(player)
            if moved then moved.AssemblyAngularVelocity=Vector3.zero end
            cooldown[player]=os.clock()+2
        end
        pending[player]=nil
    end
    local prompt=Instance.new("ProximityPrompt")
    prompt.Name=door and "DormitoryDoor" or "AcademyEntrance"; prompt.ActionText=portal:GetAttribute("ActionText") or "Enter"
    prompt.ObjectText=portal:GetAttribute("ObjectText") or "Ravenmoor Academy"; prompt.MaxActivationDistance=door and 8 or 12
    prompt.RequiresLineOfSight=door; prompt.HoldDuration=.2; prompt.Parent=portal
    prompt.Triggered:Connect(enter)
    if door then return end
    portal.Touched:Connect(function(hit)
        local character=hit:FindFirstAncestorOfClass("Model")
        local player=character and Players:GetPlayerFromCharacter(character)
        if player then enter(player) end
    end)
end
function W:Travel(player, destination)
    local d = self.S.PlayerDataService:Get(player); local pos = Config.Waystones[destination]
    local s = self.S.CombatService.States[player]
    if not d or not pos or not d.Waystones[destination] or not s then return end
    if self.S.DuelService:IsBusy(player) or os.clock()-s.LastCombat < 8 then return self.S.NetworkService:Notice(player, "Travel is unavailable during combat.") end
    local near = false
    for id in pairs(Config.Waystones) do if self:Near(player, "Waystone_"..id, 16) then near = true end end
    if not near then return self.S.NetworkService:Notice(player, "Stand beside a Waystone to travel.") end
    if d.Gilders < 25 then return self.S.NetworkService:Notice(player, "Waystone travel costs 25 Gilders.") end
    d.Gilders = d.Gilders-25; d.LastWaystone = destination
    self:Teleport(player, Vector3.new(pos[1],pos[2],pos[3])); self.S.ProgressionService:Refresh(player)
end
-- Night lights (Config.NightLights: lit windows and lanterns across the map, and in the imported village in
-- Workspace.Scenery) are plain glass by day. After dark they glow, and the lights inside them switch on.
function W:SetNightLights(night)
    if night == self.Night then return end
    self.Night = night
    for _, glass in ipairs(self.NightLights) do
        glass.Material = night and Enum.Material.Neon or Enum.Material.Glass
        for _, light in ipairs(glass:GetChildren()) do if light:IsA("Light") then light.Enabled = night end end
    end
end
function W:Start()
    self:StartPortals()
    self.S.NetworkService.Handlers.Travel = function(player, id) if type(id) == "string" then self:Travel(player, id) end end
    Players.PlayerRemoving:Connect(function(player) self.Movement[player] = nil end)
    self.NightLights = {}
    local names = {}
    for _, name in ipairs(Config.NightLights) do names[name] = true end
    for _, name in ipairs({"Map", "Scenery"}) do
        local root = workspace:FindFirstChild(name)
        if root then
            for _, item in ipairs(root:GetDescendants()) do
                if item:IsA("BasePart") and names[item.Name] then table.insert(self.NightLights, item) end
            end
        end
    end
    task.spawn(function()
        local start = os.clock()
        while true do
            task.wait(0.5)
            Lighting.ClockTime = (9 + (os.clock()-start)/Config.DayLength*24) % 24
            self:SetNightLights(Lighting.ClockTime >= 18.5 or Lighting.ClockTime < 6)
            for _, player in ipairs(Players:GetPlayers()) do
                local root = self:Root(player); local state = self.S.CombatService.States[player]
                if root and state and state.Humanoid.Health > 0 then
                    local z = self:Zone(root.Position); player:SetAttribute("Zone", z.Id)
                    local now = os.clock(); local prev = self.Movement[player]
                    if prev and now > (prev.Grace or 0) then
                        local delta = Vector3.new(root.Position.X-prev.Pos.X,0,root.Position.Z-prev.Pos.Z).Magnitude
                        -- A broom rider (FlightService) may cover ground at the broom's speed.
                        local allowance = math.max(state.Humanoid.WalkSpeed, 24, state.FlySpeed or 0)*(now-prev.Time)+20
                        local b, p = Config.WorldBounds, root.Position
                        if delta > allowance or p.X < b.MinX or p.X > b.MaxX or p.Z < b.MinZ or p.Z > b.MaxZ then
                            self:Teleport(player, prev.Pos); root = self:Root(player)
                        end
                    end
                    if root.Position.Y < -20 then self:Teleport(player, Vector3.new(90,5,164)) end
                    local grace = self.Movement[player] and self.Movement[player].Grace or 0
                    self.Movement[player] = {Pos = root.Position, Time = now, Grace = grace}
                end
            end
        end
    end)
end
return W
