local Players=game:GetService("Players")
local Lighting=game:GetService("Lighting")
local RS=game:GetService("ReplicatedStorage")
local Data=require(RS.Shared.MonsterData)
local F=require(RS.Shared.Formulas)
local Config=require(RS.Shared.Config)
local Loot=require(game:GetService("ServerStorage").LootTables)
local M={}
local function part(parent,name,size,cf,color,shape)
    local p=Instance.new("Part"); p.Name=name; p.Size=size; p.CFrame=cf; p.Color=color
    p.Anchored=true; p.CanCollide=false; p.CanTouch=false; p.TopSurface=Enum.SurfaceType.Smooth; p.BottomSurface=Enum.SurfaceType.Smooth
    if shape then p.Shape=shape end
    p.Parent=parent; return p
end
function M:Init(services) self.S=services; self.Spawns={}; self.Alive={}; self.NextId=0 end
function M:Count() local count=0; for _ in pairs(self.Alive) do count=count+1 end; return count end
function M:Spawn(id,pos,spawner,brood)
    if self:Count()>=Config.MaxMonsters then return end
    local def=Data[id]; local stat=F.Monster(def.Level,def.Rank); local size=brood and 1.7 or def.Size
    local model=Instance.new("Model"); model.Name=def.Name; local color=Color3.fromRGB(table.unpack(def.Color))
    local y=def.Flying and 6 or size/2+0.5; local position=Vector3.new(pos.X,y,pos.Z)
    local root=part(model,"HumanoidRootPart",Vector3.new(size,size,size),CFrame.new(position),color,Enum.PartType.Ball)
    model.PrimaryPart=root
    for side=-1,1,2 do
        part(model,"Eye",Vector3.new(size*0.15,size*0.17,size*0.1),CFrame.new(position+Vector3.new(side*size*0.2,size*0.1,-size*0.46)),Color3.fromRGB(249,206,113)).Material=Enum.Material.Neon
    end
    if id=="Gloomspider" or id=="MotherVexweave" then
        for side=-1,1,2 do for leg=1,4 do
            part(model,"Leg",Vector3.new(size*0.9,0.3,size*0.12),CFrame.new(position+Vector3.new(side*size*0.65,-size*0.2,(leg-2.5)*size*0.24))*CFrame.Angles(0,side*(leg-2.5)*0.3,side*0.2),color)
        end end
    elseif id=="RotbarkSentinel" then
        for side=-1,1,2 do part(model,"Branch",Vector3.new(1,size*1.2,1),CFrame.new(position+Vector3.new(side*size*0.7,1,0))*CFrame.Angles(0,0,side*0.5),color) end
    elseif id=="Lanternwisp" then root.Material=Enum.Material.Neon end
    local hum=Instance.new("Humanoid"); hum.RequiresNeck=false; hum.BreakJointsOnDeath=false; hum.DisplayDistanceType=Enum.HumanoidDisplayDistanceType.None
    hum.MaxHealth=brood and 55 or stat.HP; hum.Health=hum.MaxHealth; hum.Parent=model
    model.Parent=self.S.WorldService.Monsters
    local state=self.S.CombatService:Register(model,{MonsterId=id,Rank=def.Rank,Def=def,Stats=stat,Home=position,Size=size,
        Spawner=spawner,Threat={},Contributors={},NextAttack=0,Phase=1,Brood=brood,State="Idle",Born=os.clock()})
    model:SetAttribute("MonsterId",id); model:SetAttribute("Level",def.Level); model:SetAttribute("Rank",def.Rank)
    self.Alive[state]=true; return state
end
function M:Target(s)
    local best,bestScore=nil,-math.huge
    for _,player in ipairs(Players:GetPlayers()) do
        local target=self.S.CombatService.States[player]
        if target and target.Humanoid.Health>0 and not self.S.WorldService:Zone(target.Root.Position).Safe and not self.S.DuelService:IsBusy(player) then
            local distance=(target.Root.Position-s.Root.Position).Magnitude
            local homeDistance=(target.Root.Position-s.Home).Magnitude
            if distance<((s.Threat[player] or 0)>0 and 80 or 30) and homeDistance<90 then
                local score=(s.Threat[player] or 0)+30-distance
                if score>bestScore then best=target; bestScore=score end
            end
        end
    end
    return best
end
function M:Move(s,destination,dt,speed)
    local C=self.S.CombatService
    if C:Has(s,"Rooted") or not C:CanAct(s) then return end
    local delta=(destination-s.Root.Position)*Vector3.new(1,0,1)
    if delta.Magnitude<1 then return end
    local amount=math.min(delta.Magnitude,speed*dt*(C:Has(s,"Chilled") and 0.7 or 1))
    local dir=delta.Unit
    local params=self.S.SpellService:Params(self.S.SpellService:WorldIgnore())
    local radius=math.min(1.5,s.Size/2)
    local hit=workspace:Spherecast(s.Root.Position,radius,dir*(amount+1),params)
    if hit then
        dir=Vector3.new(-dir.Z,0,dir.X)
        if workspace:Spherecast(s.Root.Position,math.min(1.2,radius),dir*(amount+1),params) then return end
    end
    local p=s.Root.Position+dir*amount
    if s.Def.Flying then p=Vector3.new(p.X,6+math.sin(os.clock()*2)*0.6,p.Z) end
    s.Model:PivotTo(CFrame.lookAt(p,p+dir))
end
function M:Protected(player,position)
    for _,d in ipairs(self.S.SpellService.Domes) do if d.Player==player and d.Until>os.clock() and (d.Pos-position).Magnitude<10 then return true end end
    return false
end
function M:Attack(s,target)
    local C=self.S.CombatService
    local now=os.clock(); if now<s.NextAttack or not C:CanAct(s) or C:Has(s,"Silenced") then return end
    local boss=s.Rank=="Boss"; local elite=s.Rank=="Elite"
    local windup=boss and 1.15 or (elite and 1 or 0.55)
    local radius=boss and (s.Phase==3 and 12 or 8) or (elite and 13 or 5)
    local point=target.Root.Position; s.NextAttack=now+s.Def.Cooldown*(s.Phase==3 and 0.65 or 1)
    s.State="Attack"
    self.S.NetworkService.FX:FireAllClients("Telegraph",Vector3.new(point.X,0.35,point.Z),radius,windup)
    if s.MonsterId=="Lanternwisp" then self.S.NetworkService.FX:FireAllClients("Beam",s.Root.Position,point,"Enemy") end
    task.delay(windup,function()
        if not self.Alive[s] or s.Humanoid.Health<=0 or not self.S.CombatService:CanAct(s) then return end
        local ignore=self.S.SpellService:WorldIgnore()
        for player,state in pairs(self.S.CombatService.States) do
            if state.Humanoid.Health>0 and (state.Root.Position-point).Magnitude<=radius+3
                and not self.S.WorldService:Zone(state.Root.Position).Safe and not self.S.DuelService:IsBusy(player)
                and not self:Protected(player,state.Root.Position)
                and self.S.SpellService:Visible(s.Root.Position,state,ignore) then
                local damage=s.Stats.Damage
                if s.Brood then damage=8 end
                if s.MonsterId=="Moonhowler" and (Lighting.ClockTime>=18 or Lighting.ClockTime<6) then damage=damage*1.3 end
                local reflected=s.MonsterId=="Lanternwisp" and self.S.CombatService:Has(state,"Speculo")
                if reflected then
                    state.Statuses.Speculo=nil
                    self.S.CombatService:Damage(player,s,damage,nil)
                    self.S.NetworkService.FX:FireAllClients("Beam",state.Root.Position,s.Root.Position,"Speculo")
                elseif self.S.CombatService:Damage(nil,state,damage,nil) then
                    if s.Def.Status then self.S.CombatService:Status(state,s.Def.Status,2,nil) end
                    if boss and s.Phase==1 then self.S.CombatService:Status(state,"Rooted",1.2,nil) end
                    if s.MonsterId=="Lanternwisp" then state.Mana=math.max(0,state.Mana-10) end
                end
            end
        end
        self.S.NetworkService.FX:FireAllClients("Blast",point,"Enemy",radius)
        if boss and s.Phase==3 then
            self.S.NetworkService.FX:FireAllClients("Pool",Vector3.new(point.X,0.4,point.Z),radius,5)
            task.spawn(function()
                for _=1,5 do
                    task.wait(1); if not self.Alive[s] then return end
                    for player,state in pairs(self.S.CombatService.States) do
                        if (state.Root.Position-point).Magnitude<radius and not self.S.WorldService:Zone(state.Root.Position).Safe
                            and not self.S.DuelService:IsBusy(player) and not self:Protected(player,state.Root.Position) then self.S.CombatService:Damage(nil,state,8,nil) end
                    end
                end
            end)
        end
    end)
end
function M:Killed(s)
    if not self.Alive[s] then return end
    self.Alive[s]=nil; self.S.CombatService.Targets[s.Model]=nil
    if s.Spawner then s.Spawner.Next=os.clock()+(s.Rank=="Boss" and 600 or (s.Rank=="Elite" and 300 or 30)); s.Spawner.State=nil end
    if not s.Brood then
        for player,contribution in pairs(s.Contributors) do
            local d=self.S.PlayerDataService:Get(player); local root=self.S.WorldService:Root(player)
            if d and root and contribution>0 and (root.Position-s.Root.Position).Magnitude<150 then
                local drop=Loot[s.MonsterId]
                if drop and math.random()<drop.Chance then d.Inventory[drop.Item]=(d.Inventory[drop.Item] or 0)+1 end
                if drop and drop.Tome and math.random()<drop.TomeChance then d.Inventory[drop.Tome.." Tome"]=(d.Inventory[drop.Tome.." Tome"] or 0)+1 end
                if drop and drop.Wand and math.random()<drop.Wand.Chance then self.S.WandService:Reward(player,drop.Wand.Rarity) end
                if drop and drop.Named and math.random()<drop.Named.Chance then self.S.WandService:GrantNamed(player,drop.Named.Id,"A wand was left behind: %s!") end
                if s.MonsterId=="RotbarkSentinel" then d.SealDefeated=true end
                if s.MonsterId=="MotherVexweave" then d.BossDefeated=true; self.S.ProgressionService:HousePoints(player,25) end
                self.S.ProgressionService:Award(player,s.Stats.XP,s.Stats.Gilders)
                self.S.ProgressionService:Event(player,"Kill",s.MonsterId)
                self.S.NetworkService:Notice(player,"+"..s.Stats.XP.." XP   +"..s.Stats.Gilders.." Gilders")
            end
        end
    end
    self.S.NetworkService.FX:FireAllClients("Defeat",s.Root.Position)
    task.delay(0.2,function() s.Model:Destroy() end)
end
function M:Tick(dt)
    for s in pairs(self.Alive) do
        if not s.Model.Parent then self.Alive[s]=nil
        else
            local target=self:Target(s); local hp=s.Humanoid.Health/s.Humanoid.MaxHealth
            if s.Rank=="Boss" then
                s.Phase=hp>0.6 and 1 or (hp>0.25 and 2 or 3); s.Model:SetAttribute("Phase",s.Phase)
                if target and s.Phase==2 and os.clock()>(s.NextBrood or 0) then
                    s.NextBrood=os.clock()+20
                    for i=1,3 do self:Spawn("Gloomspider",s.Home+Vector3.new(i*5-10,0,12),nil,true) end
                end
            end
            if target then
                local distance=(target.Root.Position-s.Root.Position).Magnitude
                if distance>s.Def.Range then s.State="Chase"; self:Move(s,target.Root.Position,dt,s.Def.Speed*(s.Phase==3 and 1.3 or 1))
                else self:Attack(s,target) end
            elseif (s.Root.Position-s.Home).Magnitude>4 then
                s.State="Return"; self:Move(s,s.Home,dt,s.Def.Speed); s.Humanoid.Health=math.min(s.Humanoid.MaxHealth,s.Humanoid.Health+s.Humanoid.MaxHealth*dt/8)
                s.Contributors={}; s.Threat={}
            else
                s.State="Patrol"
                self:Move(s,s.Home+Vector3.new(math.sin(os.clock()/5)*3,0,math.cos(os.clock()/5)*3),dt,3)
                if s.Humanoid.Health<s.Humanoid.MaxHealth then s.Humanoid.Health=math.min(s.Humanoid.MaxHealth,s.Humanoid.Health+s.Humanoid.MaxHealth*dt/8) end
            end
            if s.Brood and os.clock()-s.Born>60 then self.Alive[s]=nil; self.S.CombatService.Targets[s.Model]=nil; s.Model:Destroy() end
        end
    end
    for _,sp in ipairs(self.Spawns) do
        if not sp.State and os.clock()>sp.Next then
            local near=false
            for _,player in ipairs(Players:GetPlayers()) do local root=self.S.WorldService:Root(player); if root and (root.Position-sp.Position).Magnitude<260 then near=true; break end end
            if near then sp.State=self:Spawn(sp.Id,sp.Position,sp,false) end
        end
    end
end
function M:Start()
    local placements={
        {"Thornimp",-365,12},{"Thornimp",-382,33},{"Thornimp",-395,5},{"Thornimp",-376,-17},
        {"Gloomspider",-440,52},{"Gloomspider",-462,70},{"Gloomspider",-437,82},
        {"Lanternwisp",-515,30},{"Lanternwisp",-531,48},{"Lanternwisp",-511,62},
        {"Moonhowler",-507,-65},{"Moonhowler",-529,-88},{"Moonhowler",-490,-84},
        {"RotbarkSentinel",-422,-87},{"MotherVexweave",-460,-183},
    }
    for _,p in ipairs(placements) do self.Spawns[#self.Spawns+1]={Id=p[1],Position=Vector3.new(p[2],0,p[3]),Next=0} end
    task.spawn(function() while true do task.wait(0.2); self:Tick(0.2) end end)
end
return M
