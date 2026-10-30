local RS=game:GetService("ReplicatedStorage")
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
local Chat=game:GetService("TextChatService")
local Spells=require(RS.Shared.SpellData)
local F=require(RS.Shared.Formulas)
local Wands=require(RS.Shared.WandData)
local S={}
local function vector(v)
    return typeof(v)=="Vector3" and F.Finite(v.X) and F.Finite(v.Y) and F.Finite(v.Z)
end
function S:Init(services) self.S=services; self.Projectiles={}; self.Domes={}; self.Aims={}; self.SeenMessages={}; self.Lances={} end
function S:Reject(player,id,reason)
    if player.Parent then self.S.NetworkService.CastReply:FireClient(player,id,false,reason) end
end
function S:Params(ignore)
    local p=RaycastParams.new(); p.FilterType=Enum.RaycastFilterType.Exclude; p.FilterDescendantsInstances=ignore; return p
end
-- Units and characters never block sight lines or monster steering; only world geometry does.
function S:WorldIgnore()
    local list={self.S.WorldService.Runtime,workspace.Markers}
    for _,player in ipairs(Players:GetPlayers()) do if player.Character then list[#list+1]=player.Character end end
    return list
end
function S:Visible(from, target, ignore)
    local delta=target.Root.Position-from
    if delta.Magnitude<0.01 then return true end
    local hit=workspace:Raycast(from,delta,self:Params(ignore or {}))
    return not hit or hit.Instance:IsDescendantOf(target.Model)
end
-- Bolts and beams pass through units the caster cannot affect: allies outside a duel,
-- other students' lesson targets and defeated monsters.
function S:Trace(player,origin,direction,radius,params)
    local limit=1; for _ in pairs(self.S.CombatService.Targets) do limit=limit+1 end
    for _=1,limit do
        local hit
        if radius then hit=workspace:Spherecast(origin,radius,direction,params) else hit=workspace:Raycast(origin,direction,params) end
        local target=hit and self.S.CombatService:Resolve(hit.Instance)
        if not target or self.S.CombatService:CanDamage(player,target) then return hit end
        local ignore=params.FilterDescendantsInstances; ignore[#ignore+1]=target.Model; params.FilterDescendantsInstances=ignore
    end
end
-- `lance` marks a spark lance's strike (Pour): Mirror Ward reflects only bolts, and only bolts feed Stormfork's Static.
function S:Impact(player,target,spell,spoken,scale,position,lance)
    local C=self.S.CombatService
    if not C:CanDamage(player,target) then return end
    if player and self.S.DuelService:IsCounting(player) then return end
    if spell.Type=="Projectile" and not lance and C:Has(target,"Speculo") and target.Player and player then
        target.Statuses.Speculo=nil
        local caster=C.States[player]
        if caster then self:Projectile(target.Player,spell,target.Root.Position+Vector3.new(0,1,0),(caster.Root.Position-target.Root.Position).Unit,spoken,true) end
        return
    end
    local data=self.S.PlayerDataService:Get(player); if not data then return end
    local amount=F.Power(spell.Damage,data,spell,spoken)*(scale or 1)
    local combo
    if spell.Element=="Lightning" and C:Has(target,"Wet") then amount=amount*1.3; combo="Conduct" end
    if spell.Id=="Tonitra" and C:Has(target,"Chilled") then amount=amount*1.5; combo="Shatter"; C:Status(target,"Stunned",0.5,player) end
    if spell.School=="Hex" and C:Has(target,"Airborne") then amount=amount*1.25; combo="Juggle" end
    if spell.Id=="Ruptara" and C:Has(target,"Rooted") then amount=amount*1.2; combo="Anchored" end
    if spell.Element=="Fire" and target.MonsterId=="RotbarkSentinel" then amount=amount*1.5 end
    if not C:Damage(player,target,amount,spell) then return end
    if combo then self.S.ProgressionService:Combo(player,combo) end
    if spell.Id=="Scintara" and not lance and target.MonsterId and Wands.Signature(data)=="Static" then self:Static(player,target,amount) end
    if target.Humanoid.Health<=0 or target.Dummy then return end
    if spell.Status then C:Status(target,spell.Status,F.Duration(spell,data),player,spell.Dps and F.Power(spell.Dps,data,spell,spoken) or 0) end
    if spell.Id=="Ruptara" and not C:Has(target,"Rooted") and target.Rank~="Boss" then self:Displace(target,position,-8) end
    if spell.Id=="Tractum" and target.Rank~="Boss" then
        local caster=C.States[player]; if caster then self:Displace(target,caster.Root.Position,15) end
    end
end
-- Stormfork: every 4th Spark Bolt hit on a monster arcs once to the nearest other monster within 12 studs, for half the hit.
-- The arc is damage over time to CombatService, so it cannot crit or add Mastery.
function S:Static(player,target,amount)
    local C=self.S.CombatService; local s=C.States[player]; if not s then return end
    s.StaticHits=(s.StaticHits or 0)+1
    if s.StaticHits<4 then return end
    s.StaticHits=0
    local nextTarget,best=nil,12; local ignore=self:WorldIgnore()
    for _,candidate in pairs(C.Targets) do
        local d=(candidate.Root.Position-target.Root.Position).Magnitude
        if candidate~=target and candidate.MonsterId and C:CanDamage(player,candidate) and d<best
            and self:Visible(target.Root.Position,candidate,ignore) then best=d; nextTarget=candidate end
    end
    if not nextTarget then return end
    self.S.NetworkService.FX:FireAllClients("Beam",target.Root.Position,nextTarget.Root.Position,"Lightning")
    C:Damage(player,nextTarget,amount*0.5,Spells.Scintara,true)
end
function S:Displace(target,origin,distance)
    local delta=(origin-target.Root.Position)*Vector3.new(1,0,1)
    if delta.Magnitude<0.1 then return end
    local displacement=delta.Unit*math.min(math.abs(distance),delta.Magnitude)*(distance<0 and -1 or 1)
    local hit=workspace:Blockcast(target.Root.CFrame,Vector3.new(2,3,2),displacement,self:Params({target.Model}))
    if hit then displacement=displacement.Unit*math.max(0,hit.Distance-1) end
    local pos=target.Root.Position+displacement
    if target.Player then self.S.WorldService:Teleport(target.Player,pos) else target.Model:PivotTo(CFrame.new(pos)) end
end
function S:Blast(player,spell,spoken,position)
    local burning=false
    for _,target in pairs(self.S.CombatService.Targets) do
        if self.S.CombatService:CanDamage(player,target) and (target.Root.Position-position).Magnitude<=spell.Blast
            and self.S.CombatService:Has(target,"Burn") then burning=true end
    end
    local ignore=self:WorldIgnore()
    for _,target in pairs(self.S.CombatService.Targets) do
        if self.S.CombatService:CanDamage(player,target) and (target.Root.Position-position).Magnitude<=spell.Blast
            and self:Visible(position+Vector3.new(0,1,0),target,ignore) then
            self:Impact(player,target,spell,spoken,1,position)
            if burning and not target.Dummy then self.S.CombatService:Status(target,"Burn",3,player,4); self.S.ProgressionService:Combo(player,"Combust") end
        end
    end
    self.S.NetworkService.FX:FireAllClients("Blast",position,spell.Id,spell.Blast)
end
function S:Projectile(player,spell,origin,direction,spoken,reflected)
    local state=self.S.CombatService.States[player]; if not state then return end
    local params=self:Params({state.Model,workspace.Markers})
    local p={Player=player,Spell=spell,Pos=origin,Dir=direction,Distance=0,Spoken=spoken,Params=params,Reflected=reflected,State=state}
    self.Projectiles[#self.Projectiles+1]=p
    self.S.NetworkService.FX:FireAllClients("Projectile",origin,direction,spell.Id,spell.Speed,spell.Range,player)
end
function S:HitProjectile(p,part,position)
    if p.Spell.Blast then self:Blast(p.Player,p.Spell,p.Spoken,position)
    else
        local target=self.S.CombatService:Resolve(part)
        if target then
            if p.Reflected and self.S.CombatService:Has(target,"Speculo") then target.Statuses.Speculo=nil
            else self:Impact(p.Player,target,p.Spell,p.Spoken,1,position) end
        end
    end
    self.S.NetworkService.FX:FireAllClients("Impact",position,p.Spell.Id)
end
-- Spark lance: Scintara held on the right mouse button (InputController). Lighting it costs Lance.Ignite mana and
-- holding it drains Lance.Drain a second, both lowered by mana-cost bonuses as the bolt's cost is. Every Lance.Tick
-- it strikes the first thing along the caster's aim (the Aim updates), up to Lance.Range studs, for Lance.Damage at
-- the bolt's power. The player's ScintaraLance attribute is where the lance ends, so every client can draw it
-- (EffectsController); it is nil while no lance pours.
function S:Channel(player,on)
    local C=self.S.CombatService; local s=C.States[player]
    if not s then return end
    if on~=true then if s.Lance then self:EndLance(player,s) end; return end
    if s.Lance then return end
    local spell=Spells.Scintara; local data=self.S.PlayerDataService:Get(player)
    if not data or not data.HasWand or not data.Spells.Scintara then return self:Reject(player,"ScintaraLance","Learn this spell first.") end
    if not C:CanAct(s) or C:Has(s,"Silenced") or s.FlySpeed or self.S.DuelService:IsCounting(player) then
        return self:Reject(player,"ScintaraLance","You cannot cast right now.")
    end
    local now=os.clock()
    if now<s.BusyUntil or now<(s.Cooldowns.ScintaraLance or 0) then return self:Reject(player,"ScintaraLance","Cooling down") end
    local scale=player:GetAttribute("FreeCast") and 0 or F.ManaCost(spell,data)/spell.ManaCost
    local ignite=spell.Lance.Ignite*scale
    if s.Mana<ignite then return self:Reject(player,"ScintaraLance","Not enough mana") end
    s.Mana=s.Mana-ignite; s.InvulnerableUntil=0
    s.Lance={Scale=scale,Since=now,Look=0,Strike=now+spell.Lance.Tick}
    self.Lances[player]=s
end
function S:EndLance(player,s,reason)
    s.Lance=nil; self.Lances[player]=nil
    player:SetAttribute("ScintaraLance",nil)
    local cooldown=player:GetAttribute("FreeCast") and 0 or Spells.Scintara.Lance.Cooldown
    s.Cooldowns.ScintaraLance=os.clock()+cooldown
    if player.Parent then
        self.S.NetworkService.CastReply:FireClient(player,"ScintaraLance",true,cooldown)
        if reason then self:Reject(player,"ScintaraLance",reason) end
    end
end
-- Each frame: drain the mana. Ten times a second: trace the aim and move the lance's end. Every Lance.Tick: strike.
function S:Pour(player,s,dt,now)
    local C=self.S.CombatService; local spell=Spells.Scintara; local lance=spell.Lance
    if C.States[player]~=s or not player.Parent or not self.S.PlayerDataService:Get(player) or not C:CanAct(s)
        or C:Has(s,"Silenced") or s.FlySpeed or s.DodgeAt>s.Lance.Since or self.S.DuelService:IsCounting(player) then
        return self:EndLance(player,s)
    end
    local cost=lance.Drain*dt*s.Lance.Scale
    if s.Mana<cost then return self:EndLance(player,s,"Out of mana") end
    s.Mana=s.Mana-cost
    if now<s.Lance.Look then return end
    s.Lance.Look=now+0.1
    local origin=s.Root.Position+Vector3.new(0,1.2,0)
    local update=self.Aims[player]
    local delta=update and update.Position-origin or Vector3.zero
    local dir=delta.Magnitude>0.01 and delta.Unit or s.Root.CFrame.LookVector
    local hit=self:Trace(player,origin,dir*lance.Range,lance.Radius,self:Params({s.Model,workspace.Markers}))
    local reach=hit and (hit.Position-origin).Magnitude or lance.Range
    -- A rival duellist's Bastion Dome stops the lance at its edge, as it stops bolts.
    local blocked=false
    for _,d in ipairs(self.Domes) do
        if d.Player~=player and self.S.DuelService:CanDamage(player,d.Player) then
            local along=(d.Pos-origin):Dot(dir); local miss=(origin+dir*along-d.Pos).Magnitude
            local half=miss<10 and math.sqrt(100-miss*miss)
            -- Where the lance enters the dome; a dome wholly behind the caster does not count.
            if half and along+half>0 and along-half<reach then reach=math.max(0,along-half); blocked=true end
        end
    end
    local endpoint=origin+dir*reach
    player:SetAttribute("ScintaraLance",endpoint)
    if now<s.Lance.Strike then return end
    s.Lance.Strike=math.max(now,s.Lance.Strike+lance.Tick)
    local target=not blocked and hit and C:Resolve(hit.Instance)
    if target then self:Impact(player,target,spell,false,lance.Damage/spell.Damage,endpoint,true) end
end
function S:Step(dt)
    local now=os.clock()
    for player,s in pairs(self.Lances) do self:Pour(player,s,dt,now) end
    for i=#self.Domes,1,-1 do if now>self.Domes[i].Until or not self.Domes[i].Player.Parent then table.remove(self.Domes,i) end end
    for i=#self.Projectiles,1,-1 do
        local p=self.Projectiles[i]
        if self.S.CombatService.States[p.Player]~=p.State or p.State.Humanoid.Health<=0 or not self.S.PlayerDataService:Get(p.Player) then table.remove(self.Projectiles,i)
        else
            local step=math.min(p.Spell.Speed*dt,p.Spell.Range-p.Distance)
            local nextPos=p.Pos+p.Dir*step; local blocked=false
            for _,d in ipairs(self.Domes) do
                if d.Player~=p.Player and self.S.DuelService:CanDamage(p.Player,d.Player) then
                    local segment=nextPos-p.Pos
                    local t=math.clamp((d.Pos-p.Pos):Dot(segment)/math.max(0.001,segment:Dot(segment)),0,1)
                    if (p.Pos+segment*t-d.Pos).Magnitude<10 then blocked=true; break end
                end
            end
            local hit=not blocked and self:Trace(p.Player,p.Pos,p.Dir*math.max(step,0.001),p.Spell.Radius,p.Params) or nil
            -- Spherecast excludes initial overlaps. Check the initial volume too.
            if not blocked and p.Distance==0 and not hit then
                local overlap=OverlapParams.new(); overlap.FilterType=Enum.RaycastFilterType.Exclude; overlap.FilterDescendantsInstances=p.Params.FilterDescendantsInstances
                for _,part in ipairs(workspace:GetPartBoundsInRadius(p.Pos,p.Spell.Radius,overlap)) do
                    local target=self.S.CombatService:Resolve(part)
                    if target and self.S.CombatService:CanDamage(p.Player,target) then hit={Instance=part,Position=p.Pos}; break end
                end
            end
            if hit then self:HitProjectile(p,hit.Instance,hit.Position); table.remove(self.Projectiles,i)
            elseif blocked or p.Distance+step>=p.Spell.Range then table.remove(self.Projectiles,i)
            else p.Pos=nextPos; p.Distance=p.Distance+step end
        end
    end
end
function S:Execute(player,spell,aim,spoken)
    local C=self.S.CombatService; local s=C.States[player]; local data=self.S.PlayerDataService:Get(player)
    if not data or not C:CanAct(s) or C:Has(s,"Silenced") then return end
    local origin=s.Root.Position+Vector3.new(0,1.2,0)
    local delta=aim-origin; local dir=delta.Magnitude>0.01 and delta.Unit or s.Root.CFrame.LookVector
    if spell.Type=="Projectile" then self:Projectile(player,spell,origin,dir,spoken); return end
    if spell.Id=="Aegara" then
        s.Shield=F.Power(40,data,spell,spoken); s.ShieldUntil=os.clock()+2
        self.S.NetworkService.FX:FireAllClients("Ward",s.Model,2)
    elseif spell.Id=="Speculo" or spell.Id=="Durassa" or spell.Id=="Velocis" then
        C:Status(s,spell.Id,F.Duration(spell,data),player)
        if spell.Id=="Speculo" then self.S.NetworkService.FX:FireAllClients("Ward",s.Model,0.6) end
    elseif spell.Id=="Glimmora" then
        s.Light=not s.Light; local old=s.Root:FindFirstChild("Glimmora"); if old then old:Destroy() end
        if s.Light then local light=Instance.new("PointLight"); light.Name="Glimmora"; light.Range=24; light.Brightness=2; light.Color=Color3.fromRGB(199,180,255); light.Parent=s.Root end
    elseif spell.Id=="Murallis" then
        self.Domes[#self.Domes+1]={Player=player,Pos=s.Root.Position,Until=os.clock()+4}
        self.S.NetworkService.FX:FireAllClients("Dome",s.Root.Position,4)
    elseif spell.Id=="Vitara" or spell.Id=="Purgo" then
        local hit=workspace:Raycast(origin,dir*spell.Range,self:Params({s.Model,workspace.Markers}))
        local target=hit and C:Resolve(hit.Instance) or s
        if not target or not target.Player or (target.Player~=player and (self.S.DuelService:IsBusy(player) or self.S.DuelService:IsBusy(target.Player))) then target=s end
        if spell.Id=="Vitara" then
            -- Hearthroot's Sapflow: a Mend that restores health refunds 6 mana.
            if C:Heal(player,target,F.Power(25,data,spell,spoken))>0 and Wands.Signature(data)=="Sapflow" then
                s.Mana=math.min(s.MaxMana,s.Mana+6)
                if target~=s then self.S.NetworkService.FX:FireAllClients("Beam",target.Root.Position,s.Root.Position,"Restoration") end
                self.S.NetworkService.FX:FireAllClients("Status",s.Root.Position,"Restoration")
            end
        else for _,name in ipairs({"Burn","Chilled","Silenced","Rooted","Asleep"}) do target.Statuses[name]=nil end; self.S.NetworkService.FX:FireAllClients("Heal",target.Root.Position,0) end
    elseif spell.Id=="Resero" then
        local hit=workspace:Raycast(origin,dir*35,self:Params({s.Model,workspace.Markers}))
        if hit then self.S.InteractionService:Unseal(player,hit.Instance) end
    elseif spell.Type=="Beam" then
        local hit=self:Trace(player,origin,dir*spell.Range,nil,self:Params({s.Model,workspace.Markers}))
        local endpoint=hit and hit.Position or origin+dir*spell.Range
        self.S.NetworkService.FX:FireAllClients("Beam",origin,endpoint,spell.Id)
        local target=hit and C:Resolve(hit.Instance)
        if target then
            self:Impact(player,target,spell,spoken,1,endpoint)
            if spell.Id=="Tonitra" then
                local seen={[target]=true}; local last=target; local ignore=self:WorldIgnore()
                for jump=1,2 do
                    local nextTarget,best=nil,25
                    for _,candidate in pairs(C.Targets) do
                        local d=(candidate.Root.Position-last.Root.Position).Magnitude
                        if not seen[candidate] and C:CanDamage(player,candidate) and d<best
                            and self:Visible(last.Root.Position,candidate,ignore) then best=d; nextTarget=candidate end
                    end
                    if not nextTarget then break end
                    self.S.NetworkService.FX:FireAllClients("Beam",last.Root.Position,nextTarget.Root.Position,spell.Id)
                    self:Impact(player,nextTarget,spell,spoken,0.75^jump,nextTarget.Root.Position)
                    seen[nextTarget]=true; last=nextTarget
                end
            end
        end
    end
end
function S:Cast(player,id,aim,spoken)
    if type(id)~="string" or #id>32 or not vector(aim) then return end
    local spell=Spells[id]; local data=self.S.PlayerDataService:Get(player); local s=self.S.CombatService.States[player]
    if not spell or not spell.Implemented or not data or not data.HasWand or not data.Spells[id] then return self:Reject(player,id,"Learn this spell first.") end
    local C=self.S.CombatService
    if not C:CanAct(s) or C:Has(s,"Silenced") or self.S.DuelService:IsCounting(player) then return self:Reject(player,id,"You cannot cast right now.") end
    if s.Lance or (aim-s.Root.Position).Magnitude>1000 then return end
    if not spoken then
        local equipped=id=="Scintara"
        for _,value in pairs(data.Loadout) do if value==id then equipped=true end end
        if not equipped then return end
    elseif not data.Settings.SpokenCasting then return end
    local now=os.clock()
    if now<s.BusyUntil or now<(s.Cooldowns[id] or 0) then return self:Reject(player,id,"Cooling down") end
    local cost=F.ManaCost(spell,data); local cooldown=F.Cooldown(spell,data)
    -- Admin testing: the server sets FreeCast, so clients cannot grant it to themselves.
    if player:GetAttribute("FreeCast") then cost,cooldown=0,0 end
    if s.Mana<cost then return self:Reject(player,id,"Not enough mana") end
    local castTime=spell.CastTime+(spoken and 0.3 or 0)
    s.Mana=s.Mana-cost; s.Cooldowns[id]=now+cooldown
    s.BusyUntil=now+castTime; s.InvulnerableUntil=0
    self.S.NetworkService.CastReply:FireClient(player,id,true,cooldown)
    task.delay(castTime,function()
        if C.States[player]==s and player.Parent then self:Execute(player,spell,aim,spoken) end
    end)
end
function S:Spoken(player,text)
    if type(text)~="string" or #text>64 or not self.S.NetworkService:Allow(player,"Spoken",3,5) then return end
    text=text:lower():gsub("^%s+",""):gsub("%s+$","")
    local state=self.S.CombatService.States[player]; if not state then return end
    local update=self.Aims[player]
    local aim=update and os.clock()-update.Time<1 and update.Position or state.Root.Position+state.Root.CFrame.LookVector*120
    for id in pairs(Spells) do if text==id:lower() then self:Cast(player,id,aim,true); break end end
end
function S:Start()
    self.S.NetworkService:Bind("Cast",10,12,function(player,id,aim) self:Cast(player,id,aim,false) end)
    self.S.NetworkService:Bind("Channel",6,8,function(player,on) self:Channel(player,on) end)
    self.S.NetworkService:Bind("Aim",12,15,function(player,aim)
        local root=self.S.WorldService:Root(player)
        if root and vector(aim) and (aim-root.Position).Magnitude<=500 then self.Aims[player]={Position=aim,Time=os.clock()} end
    end)
    RunService.Heartbeat:Connect(function(dt) self:Step(math.min(dt,0.15)) end)
    local command=Instance.new("TextChatCommand"); command.Name="WandboundCast"; command.PrimaryAlias="/cast"; command.Parent=Chat
    command.Triggered:Connect(function(source,text)
        local player=Players:GetPlayerByUserId(source.UserId)
        if player then self:Spoken(player,text:gsub("^%S+%s*","")) end
    end)
    -- Delivery callbacks run once per recipient. Deduplicate by MessageId before casting.
    task.spawn(function()
        local channels=Chat:WaitForChild("TextChannels",15); local general=channels and channels:WaitForChild("RBXGeneral",15)
        if not general then return end
        general.ShouldDeliverCallback=function(message)
            local id=message.MessageId
            if message.TextSource and id~="" and not self.SeenMessages[id] then
                self.SeenMessages[id]=os.clock()
                local player=Players:GetPlayerByUserId(message.TextSource.UserId)
                if player then task.defer(function() self:Spoken(player,message.Text) end) end
            end
            return true
        end
    end)
    task.spawn(function() while true do task.wait(30); for id,t in pairs(self.SeenMessages) do if os.clock()-t>30 then self.SeenMessages[id]=nil end end end end)
    Players.PlayerRemoving:Connect(function(player) self.Aims[player]=nil; self.Lances[player]=nil end)
end
return S
