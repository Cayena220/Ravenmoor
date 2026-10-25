local Players = game:GetService("Players")
local Shared = game:GetService("ReplicatedStorage").Shared
local Config = require(Shared.Config)
local F = require(Shared.Formulas)
local Wands = require(Shared.WandData)
local C = {}
local CC = {Silenced=true,Rooted=true,Airborne=true,Asleep=true,Stunned=true}
function C:Init(services) self.S = services; self.States = {}; self.Targets = {} end
function C:Register(model, state)
    state.Model = model; state.Statuses = {}; state.LastCombat = -100; state.Shield = 0
    state.Humanoid = model:FindFirstChildOfClass("Humanoid"); state.Root = model.PrimaryPart or model:FindFirstChild("HumanoidRootPart")
    self.Targets[model] = state
    return state
end
function C:Resolve(part)
    local node = part
    while node and node ~= workspace do if self.Targets[node] then return self.Targets[node] end; node = node.Parent end
end
function C:Has(state, status)
    local value = state.Statuses[status]; return value and value.Until > os.clock()
end
function C:CanAct(state)
    return state and state.Humanoid.Health > 0 and not self:Has(state,"Asleep") and not self:Has(state,"Airborne") and not self:Has(state,"Stunned")
end
function C:Status(target, name, duration, source, dps)
    if not target or target.Humanoid.Health <= 0 or target.Rank == "Boss" and CC[name] then return end
    local now = os.clock()
    if CC[name] then
        if now < (target.ImmuneUntil or 0) then return end
        if now > (target.CCWindow or 0) then target.CCCount = 0; target.CCWindow = now+10 end
        target.CCCount = (target.CCCount or 0)+1
        duration = duration * F.CCMult(target.CCCount)
        if target.CCCount >= 3 then target.ImmuneUntil = now+duration+5 end
        if duration <= 0 then return end
    end
    target.Statuses[name] = {Until = now+duration, Source = source, Dps = dps or 0, Tick = now+1}
    if name == "Airborne" then
        if target.Player then
            target.Root:ApplyImpulse(Vector3.new(0,target.Root.AssemblyMass*35,0))
        else
            -- Keep the original ground height so overlapping lifts cannot strand a unit in the air.
            if not target.GroundY then
                target.GroundY = target.Root.Position.Y
                target.Model:PivotTo(target.Root.CFrame + Vector3.new(0,6,0))
            end
            local lift = {}; target.Lift = lift
            task.delay(duration,function()
                if target.Lift == lift and target.Model.Parent then
                    local pos=target.Root.Position
                    target.Model:PivotTo(CFrame.new(pos.X,target.GroundY,pos.Z))
                    target.Lift = nil; target.GroundY = nil
                end
            end)
        end
    end
    self.S.NetworkService.FX:FireAllClients("Status", target.Root.Position, name, duration)
end
function C:CanDamage(player, target)
    if not target or not target.Model.Parent or target.Humanoid.Health <= 0 then return false end
    if target.Player then
        if player == target.Player then return false end
        return player and self.S.DuelService:CanDamage(player, target.Player) or false
    end
    if player and self.S.DuelService:IsBusy(player) then return false end
    if target.LessonOwner and target.LessonOwner ~= player then return false end
    return true
end
function C:Damage(player, target, amount, spell, dot)
    if player and not self:CanDamage(player, target) then return false end
    if not target or target.Humanoid.Health <= 0 or os.clock() < (target.InvulnerableUntil or 0) then return false end
    if target.Dummy then
        if player then
            if target.LessonOwner then self.S.ClassService:TargetHit(player, target)
            else self.S.ProgressionService:Event(player, "Practice") end
            self.S.NetworkService.FX:FireAllClients("Damage", target.Root.Position, math.floor(amount), false)
        end
        return true
    end
    if target.Player then
        if player then amount = amount*0.7 end
        if self:Has(target, "Durassa") then amount = amount*0.7 end
        local guarded = self.S.PlayerDataService:Get(target.Player)
        if guarded then amount = amount*(1-F.Stats(guarded).Guard) end
    end
    local crit = false
    if player and spell and not dot then
        local data = self.S.PlayerDataService:Get(player); if not data then return false end
        crit = math.random() < F.Stats(data).Crit
        -- Widow's Bite: crits on a held target bite harder. Checked before damage clears Asleep below.
        local bite = Wands.Signature(data) == "VenomBite" and (self:Has(target, "Rooted") or self:Has(target, "Asleep"))
        if crit then amount = amount*(bite and 2 or 1.5) end
    end
    local blocked = math.min(target.Shield or 0, amount)
    target.Shield = math.max(0, (target.Shield or 0)-blocked); amount = math.max(0, amount-blocked)
    target.LastCombat = os.clock()
    if player and self.States[player] then self.States[player].LastCombat = os.clock() end
    if amount > 0 then target.Statuses.Asleep = nil end
    if player and target.MonsterId then
        target.Contributors[player] = (target.Contributors[player] or 0)+amount
        target.Threat[player] = (target.Threat[player] or 0)+amount
    end
    if target.Player and self.S.DuelService:IsBusy(target.Player) and target.Humanoid.Health-amount <= 1 then
        target.Humanoid.Health = 1; self.S.DuelService:Defeated(target.Player)
    elseif target.MonsterId and target.Humanoid.Health-amount <= 0 then
        target.Humanoid.Health = 0; self.S.MonsterService:Killed(target)
    else target.Humanoid.Health = math.max(0, target.Humanoid.Health-amount) end
    if player and spell and not dot then self.S.ProgressionService:Hit(player, spell.Id) end
    self.S.NetworkService.FX:FireAllClients("Damage", target.Root.Position+Vector3.new(0,3,0), math.floor(amount+0.5), crit)
    return true
end
-- Returns the health actually restored.
function C:Heal(player, target, amount)
    if not target or not target.Player or target.Humanoid.Health <= 0 then return 0 end
    if target.Player ~= player and (self.S.DuelService:IsBusy(player) or self.S.DuelService:IsBusy(target.Player)) then return 0 end
    if self.S.DuelService:IsBusy(player) then amount = amount*0.8 end
    local gain = math.min(amount, target.Humanoid.MaxHealth-target.Humanoid.Health)
    target.Humanoid.Health = target.Humanoid.Health+gain
    self.S.NetworkService.FX:FireAllClients("Heal", target.Root.Position, math.floor(gain))
    return gain
end
function C:UpdateStats(player, refill)
    local s = self.States[player]; local d = self.S.PlayerDataService:Get(player)
    if not s or not d then return end
    local stats = F.Stats(d); s.BaseSpeed = stats.Speed; s.MaxMana = stats.Mana; s.Regen = stats.ManaRegen
    s.Humanoid.MaxHealth = stats.HP
    if refill then s.Humanoid.Health = stats.HP; s.Mana = stats.Mana end
    s.Mana = math.min(s.Mana, stats.Mana)
end
function C:HouseTrim(player)
    local d=self.S.PlayerDataService:Get(player); local s=self.States[player]
    if not d or not s or d.House=="" then return end
    local torso=s.Model:FindFirstChild("UpperTorso") or s.Model:FindFirstChild("Torso")
    if not torso then return end
    local trim=s.Model:FindFirstChild("HouseSash")
    if not trim then
        trim=Instance.new("Part"); trim.Name="HouseSash"; trim.Size=Vector3.new(0.5,torso.Size.Y,0.12)
        trim.CanCollide=false; trim.CanQuery=false; trim.CanTouch=false; trim.Massless=true
        trim.CFrame=torso.CFrame*CFrame.new(0.3,0,-torso.Size.Z/2-0.09); trim.Parent=s.Model
        local weld=Instance.new("WeldConstraint"); weld.Part0=torso; weld.Part1=trim; weld.Parent=trim
    end
    trim.Color=Color3.fromRGB(table.unpack(Config.Houses[d.House].Color))
end
function C:BindPlayer(player)
    local function characterAdded(model)
        local hum = model:WaitForChild("Humanoid"); local root = model:WaitForChild("HumanoidRootPart")
        if not self.S.PlayerDataService:Get(player) then return end
        local old = self.States[player]; if old then self.Targets[old.Model] = nil end
        local s = self:Register(model, {Player=player, Mana=100, MaxMana=100, Stamina=100, Cooldowns={},
            BaseSpeed=16, Regen=4, DodgeAt=-100, InvulnerableUntil=os.clock()+5, BusyUntil=0})
        s.Root=root; s.Humanoid=hum; self.States[player]=s; self:UpdateStats(player,true); self.S.WandService:Attach(player); self:HouseTrim(player)
        local d=self.S.PlayerDataService:Get(player); local pos=Config.Waystones[d.LastWaystone] or Config.Waystones.Hollowmere
        self.S.WorldService:Teleport(player,Vector3.new(pos[1],pos[2],pos[3]))
        hum.Died:Connect(function()
            self.S.DuelService:Defeated(player); self.S.ClassService:Cancel(player)
            self.S.NetworkService.UI:FireClient(player,"Knockout",Config.RespawnTime)
            task.delay(Config.RespawnTime,function() if player.Parent and self.S.PlayerDataService:Get(player) then player:LoadCharacterAsync() end end)
        end)
    end
    player.CharacterAdded:Connect(characterAdded)
    if player.Character then task.spawn(characterAdded,player.Character) end
end
function C:Dodge(player, direction)
    local s=self.States[player]
    if not self:CanAct(s) or self:Has(s,"Rooted") or s.Stamina<35 or os.clock()-s.DodgeAt<0.8 then return end
    if typeof(direction)~="Vector3" or not F.Finite(direction.X) or not F.Finite(direction.Y) or not F.Finite(direction.Z) then return end
    local flat=Vector3.new(direction.X,0,direction.Z); if flat.Magnitude<0.1 then flat=s.Root.CFrame.LookVector*Vector3.new(1,0,1) end
    if flat.Magnitude<0.1 then return end
    flat=flat.Unit
    -- Monsters do not collide, so they must not cut a dodge short.
    local params=RaycastParams.new(); params.FilterType=Enum.RaycastFilterType.Exclude; params.FilterDescendantsInstances={s.Model,self.S.WorldService.Monsters}
    local hit=workspace:Blockcast(s.Root.CFrame,Vector3.new(2,3,2),flat*10,params)
    local distance=hit and math.max(0,hit.Distance-1) or 10
    s.Stamina=s.Stamina-35; s.DodgeAt=os.clock(); s.InvulnerableUntil=os.clock()+(self.S.DuelService:IsBusy(player) and 0.2 or 0.25)
    self.S.WorldService:Teleport(player,s.Root.Position+flat*distance)
    self.S.NetworkService.FX:FireAllClients("Dodge",s.Root.Position)
end
function C:Tick(dt)
    local now=os.clock()
    for model,s in pairs(self.Targets) do
        if not model.Parent then self.Targets[model]=nil
        elseif s.Humanoid.Health>0 then
            for name,st in pairs(s.Statuses) do
                if st.Until<=now then s.Statuses[name]=nil
                elseif name=="Burn" and now>=st.Tick then
                    st.Tick=now+1
                    if not st.Source or self.S.PlayerDataService:Get(st.Source) then self:Damage(st.Source,s,st.Dps,nil,true) end
                end
            end
            if s.Player then
                local factor=1
                if self:Has(s,"Chilled") then factor=factor*0.7 end
                if self:Has(s,"Durassa") then factor=factor*0.8 end
                if self:Has(s,"Velocis") then factor=factor*1.35 end
                if self:Has(s,"Rooted") or not self:CanAct(s) or self.S.DuelService:IsCounting(s.Player) then factor=0 end
                s.Humanoid.WalkSpeed=s.BaseSpeed*factor
                s.Humanoid.JumpPower=factor==0 and 0 or 50
                s.Humanoid.JumpHeight=factor==0 and 0 or 7.2
                s.Mana=math.min(s.MaxMana,s.Mana+dt*s.Regen*(now-s.LastCombat>5 and 2 or 1))
                if s.Light then
                    s.Mana=math.max(0,s.Mana-dt)
                    if s.Mana<1 then s.Light=false; local light=s.Root:FindFirstChild("Glimmora"); if light then light:Destroy() end end
                end
                if now-s.DodgeAt>1 then s.Stamina=math.min(100,s.Stamina+20*dt) end
                if (s.ShieldUntil or 0)<now then s.Shield=0 end
                s.Model:SetAttribute("Shield",s.Shield)
            end
        end
    end
end
function C:Start()
    self.S.NetworkService.Handlers.Dodge=function(player,direction) self:Dodge(player,direction) end
    Players.PlayerRemoving:Connect(function(player)
        local s=self.States[player]; if s then self.Targets[s.Model]=nil end; self.States[player]=nil
    end)
    task.spawn(function()
        local last=os.clock()
        while true do task.wait(0.1); local now=os.clock(); self:Tick(math.min(0.5,now-last)); last=now end
    end)
    task.spawn(function()
        while true do
            task.wait(0.25)
            for player,s in pairs(self.States) do
                if player.Parent then
                    local statuses={}; for name,st in pairs(s.Statuses) do if st.Until>os.clock() then statuses[#statuses+1]=name end end
                    local cooldowns={}; for id,t in pairs(s.Cooldowns) do if t>os.clock() then cooldowns[id]=t-os.clock() end end
                    self.S.NetworkService.State:FireClient(player,{HP=s.Humanoid.Health,MaxHP=s.Humanoid.MaxHealth,Mana=s.Mana,MaxMana=s.MaxMana,
                        Stamina=s.Stamina,Shield=s.Shield,Statuses=statuses,Cooldowns=cooldowns,
                        Class=self.S.ClassService:Schedule(),HouseTotals=self.S.ProgressionService.HouseTotals})
                end
            end
        end
    end)
end
return C
