local Players=game:GetService("Players")
local RS=game:GetService("ReplicatedStorage")
local Tween=game:GetService("TweenService")
local Run=game:GetService("RunService")
local Debris=game:GetService("Debris")
local Lighting=game:GetService("Lighting")
local Spells=require(RS.Shared.SpellData)
local Quests=require(RS.Shared.QuestData)
local Points=require(RS.Shared.WorldPoints)
local E={}
local colors={Arcane=Color3.fromRGB(194,163,255),Fire=Color3.fromRGB(255,153,72),Frost=Color3.fromRGB(139,222,255),
    Lightning=Color3.fromRGB(255,236,134),Ward=Color3.fromRGB(246,205,118),Restoration=Color3.fromRGB(139,235,163),
    Alteration=Color3.fromRGB(110,210,189),Enemy=Color3.fromRGB(226,95,129)}
function E:Init(controllers)
    self.C=controllers; self.Pool={}; self.Flying={}; self.Labels={}; self.Zone=nil; self.Lances={}; self.Clips={}
    self.Shoulders=setmetatable({},{__mode="k"}); self.Marked=setmetatable({},{__mode="k"}); self.Tilt={0,0}
end
function E:Color(id)
    local s=Spells[id]; if not s then return colors[id] or colors.Arcane end
    return colors[s.School] or colors[s.Element] or colors.Arcane
end
function E:Part(size,cf,color,material)
    local p=Instance.new("Part"); p.Anchored=true; p.CanCollide=false; p.CanTouch=false; p.CanQuery=false
    p.Size=size; p.CFrame=cf; p.Color=color; p.Material=material or Enum.Material.Neon; p.CastShadow=false; p.Parent=self.Folder; return p
end
function E:Burst(position,id,radius)
    local d=self.C.UIController.Data
    local p=self:Part(Vector3.one*0.4,CFrame.new(position),self:Color(id)); p.Shape=Enum.PartType.Ball
    local large=(d and d.Settings.ReducedEffects) and math.min(radius or 3,2) or (radius or 3)
    p.Transparency=0.35
    Tween:Create(p,TweenInfo.new(0.3),{Size=Vector3.one*large,Transparency=1}):Play(); Debris:AddItem(p,0.4)
end
function E:Number(position,value,crit,heal)
    local p=self:Part(Vector3.one*0.1,CFrame.new(position),colors.Arcane); p.Transparency=1
    local billboard=Instance.new("BillboardGui"); billboard.Size=UDim2.fromOffset(100,45); billboard.AlwaysOnTop=true; billboard.MaxDistance=160; billboard.Parent=p
    local label=Instance.new("TextLabel"); label.Size=UDim2.fromScale(1,1); label.BackgroundTransparency=1; label.Font=Enum.Font.GothamBold
    label.Text=(heal and "+" or "")..tostring(value)..(crit and "!" or ""); label.TextSize=crit and 24 or 19
    label.TextColor3=heal and colors.Restoration or (crit and colors.Lightning or Color3.fromRGB(250,244,223)); label.TextStrokeTransparency=0.5; label.Parent=billboard
    Tween:Create(p,TweenInfo.new(0.7),{Position=position+Vector3.new(0,3,0)}):Play()
    Tween:Create(label,TweenInfo.new(0.7),{TextTransparency=1,TextStrokeTransparency=1}):Play(); Debris:AddItem(p,0.8)
end
function E:Ring(position,radius,duration,pool)
    local color=pool and colors.Enemy or Color3.fromRGB(255,126,108)
    local p=self:Part(Vector3.new(0.15,radius*2,radius*2),CFrame.new(position)*CFrame.Angles(0,0,math.pi/2),color)
    p.Shape=Enum.PartType.Cylinder; p.Transparency=pool and 0.66 or 0.72
    Tween:Create(p,TweenInfo.new(duration),{Transparency=0.9}):Play(); Debris:AddItem(p,duration)
end
function E:Beam(a,b,id)
    local length=(b-a).Magnitude; if length<0.01 then return end
    local p=self:Part(Vector3.new(0.18,0.18,length),CFrame.lookAt((a+b)/2,b),self:Color(id))
    Tween:Create(p,TweenInfo.new(0.2),{Transparency=1}):Play(); Debris:AddItem(p,0.25)
end
-- Scintara (blender/vfx/scintara.py): the meshes in ReplicatedStorage.VFX.ScintaraVFX, made Neon and tinted here.
-- Each runs along its part's Z axis with its front (-Z, the LookVector) the way the spell goes. Returns a copy and
-- the mesh's own size, or nil before the meshes are imported (blender/place_scintara.lua): then a bolt is the plain
-- ball, and a lance a plain neon rod.
local SPARK=Color3.fromRGB(240,232,255)
function E:Scintara(name)
    local kit=RS:FindFirstChild("VFX") and RS.VFX:FindFirstChild("ScintaraVFX")
    local template=kit and kit:FindFirstChild(name); if not template then return nil end
    local p=template:Clone(); p.Anchored=true; p.CanCollide=false; p.CanTouch=false; p.CanQuery=false; p.CastShadow=false
    p.Material=Enum.Material.Neon; p.Color=colors.Arcane; p.Parent=self.Folder
    return p,template.Size
end
-- Where a character's wand tip is (WandModel's Tip, welded to the hand by WandService), or nil.
function E:WandTip(character)
    local wand=character and character:FindFirstChild("RavenmoorWand"); local tip=wand and wand:FindFirstChild("Tip")
    return tip and tip.Position
end
-- A Scintara flash at the wand tip (`size` times the mesh) or splash where a spell strikes, blooming and fading.
-- The splash's sparks spray back along `dir`, toward the caster.
function E:Bloom(name,cf,size,duration)
    local p,base=self:Scintara(name); if not p then return false end
    p.Color=name=="Flash" and SPARK or colors.Arcane; p.Size=base*size; p.CFrame=cf; p.Transparency=0.05
    Tween:Create(p,TweenInfo.new(duration,Enum.EasingStyle.Quad,Enum.EasingDirection.Out),{Size=base*size*1.7,Transparency=1}):Play()
    Debris:AddItem(p,duration+0.05)
    return true
end
function E:Projectile(origin,direction,id,speed,range,caster)
    if #self.Flying>=120 then return end
    local entry={Pos=origin,Dir=direction,Speed=speed,Range=range,Travel=0,Id=id}
    if id=="Scintara" then
        local spark,sparkSize=self:Scintara("Spark"); local tail,tailSize=self:Scintara("Tail")
        if spark and tail then
            spark.Color=SPARK; spark.Size=sparkSize*1.1; tail.Transparency=0.2
            entry.Spark,entry.Tail,entry.TailSize=spark,tail,tailSize
            -- The server's bolt leaves the caster's chest; this one leaves the wand and closes onto that path.
            local tip=typeof(caster)=="Instance" and caster:IsA("Player") and self:WandTip(caster.Character)
            if tip and (tip-origin).Magnitude<6 then
                entry.Offset=tip-origin
                self:Bloom("Flash",CFrame.lookAt(tip,tip+direction),1,0.15)
            end
        elseif spark then spark:Destroy() elseif tail then tail:Destroy() end
    end
    if not entry.Spark then
        local p=table.remove(self.Pool) or self:Part(Vector3.one,CFrame.new(origin),self:Color(id))
        p.Shape=Enum.PartType.Ball; p.Size=Vector3.one*(id=="Scintara" and 0.55 or 1)
        p.Color=self:Color(id); p.Transparency=0.12; p.Position=origin
        entry.Part=p
    end
    -- Server bolts pass through allies; the server's Impact event ends the visual at a character hit.
    local ignored={self.Folder}
    for _,player in ipairs(Players:GetPlayers()) do if player.Character then ignored[#ignored+1]=player.Character end end
    local params=RaycastParams.new(); params.FilterType=Enum.RaycastFilterType.Exclude; params.FilterDescendantsInstances=ignored
    entry.Params=params
    self.Flying[#self.Flying+1]=entry
end
-- A Scintara bolt: the spark spins at the front of its tail, which grows out behind it over the first studs.
function E:Fly(p)
    if p.Part then p.Part.Position=p.Pos; return end
    local shown=p.Pos+(p.Offset or Vector3.zero)*math.max(0,1-p.Travel/12)
    local look=CFrame.lookAt(shown,shown+p.Dir); local spin=os.clock()*14
    local length=p.TailSize.Z*math.min(1,0.25+p.Travel/5)
    p.Spark.CFrame=look*CFrame.Angles(0,0,spin)
    p.Tail.Size=Vector3.new(p.TailSize.X,p.TailSize.Y,length); p.Tail.CFrame=look*CFrame.new(0,0,length/2)*CFrame.Angles(0,0,-spin*0.4)
end
function E:Retire(i)
    local p=self.Flying[i]
    if p.Part then p.Part.Transparency=1; p.Part.Position=Vector3.new(0,-1000,0); self.Pool[#self.Pool+1]=p.Part
    else p.Spark:Destroy(); p.Tail:Destroy() end
    table.remove(self.Flying,i)
    return p.Dir
end
-- Ends the visual nearest a server impact, and returns which way it was flying.
function E:Land(position,id)
    local best,bestDistance=nil,10
    for i,p in ipairs(self.Flying) do
        local distance=(p.Pos-position).Magnitude
        if p.Id==id and distance<bestDistance then best=i; bestDistance=distance end
    end
    if best then return self:Retire(best) end
end
function E:Impact(position,id)
    local dir=self:Land(position,id)
    if id=="Scintara" then
        local camera=workspace.CurrentCamera
        dir=dir or (camera and (position-camera.CFrame.Position).Unit) or Vector3.new(0,0,-1)
        if self:Bloom("Splash",CFrame.lookAt(position,position+dir),0.8,0.3) then self:Burst(position,id,2); return end
    end
    self:Burst(position,id,3)
end
-- Dodge: the DashVFX meshes (blender/vfx/dash.py) in ReplicatedStorage.VFX. The streak spans the dash, the ring
-- blooms where it began, and speed lines and a dust ring follow the landing. Without the meshes, a plain burst.
function E:Dash(to,from)
    local kit=RS:FindFirstChild("VFX") and RS.VFX:FindFirstChild("DashVFX")
    local path=typeof(from)=="Vector3" and to-from or Vector3.zero
    if not kit or path.Magnitude<0.5 then self:Burst(to,"Arcane",4); return end
    local d=self.C.UIController.Data; local reduced=d and d.Settings.ReducedEffects
    local dir,length=path.Unit,path.Magnitude
    local function piece(name,cf,size,transparency,duration,goal)
        local template=kit:FindFirstChild(name); if not template then return end
        local p=template:Clone(); p.Anchored=true; p.CanCollide=false; p.CanTouch=false; p.CanQuery=false; p.CastShadow=false
        p.Material=Enum.Material.Neon; p.Color=colors.Arcane; p.Transparency=transparency; p.Size=size; p.CFrame=cf; p.Parent=self.Folder
        goal.Transparency=1
        Tween:Create(p,TweenInfo.new(duration,Enum.EasingStyle.Quad,Enum.EasingDirection.Out),goal):Play(); Debris:AddItem(p,duration+0.05)
    end
    -- Each mesh runs along its part's Z axis, front toward the landing.
    local streak=kit:FindFirstChild("Streak")
    if streak then
        local base=streak.Size
        piece("Streak",CFrame.lookAt((from+to)/2,to),Vector3.new(base.X,base.Y,length),0.3,0.35,{Size=Vector3.new(base.X*1.4,base.Y*1.4,length)})
    end
    local ring=kit:FindFirstChild("Ring")
    if ring then piece("Ring",CFrame.lookAt(from,to),ring.Size,0.15,0.3,{Size=ring.Size*2.4}) end
    if reduced then return end
    local lines=kit:FindFirstChild("Speed lines")
    if lines then
        local cf=CFrame.lookAt(to-dir*lines.Size.Z/2,to)
        piece("Speed lines",cf,lines.Size,0.25,0.25,{CFrame=cf+dir*1.5})
    end
    if ring then
        local ignored={self.Folder}
        for _,player in ipairs(Players:GetPlayers()) do if player.Character then ignored[#ignored+1]=player.Character end end
        local params=RaycastParams.new(); params.FilterType=Enum.RaycastFilterType.Exclude; params.FilterDescendantsInstances=ignored
        local hit=workspace:Raycast(to,Vector3.new(0,-8,0),params)
        local feet=hit and hit.Position+Vector3.new(0,0.1,0) or to-Vector3.new(0,3,0)
        -- Flat on the ground: the ring's Z axis points up.
        piece("Ring",CFrame.fromMatrix(feet,Vector3.xAxis,Vector3.zAxis),ring.Size*0.8,0.35,0.4,{Size=ring.Size*3})
    end
end
-- Character clips (blender/animations/character.py) live in ReplicatedStorage.Animations: an Animation per clip,
-- whose AnimationId is the published asset. In Studio, a clip not yet published plays from its KeyframeSequence.
function E:AnimationId(name)
    local folder=RS:FindFirstChild("Animations"); local anim=folder and folder:FindFirstChild(name)
    if not anim then return nil end
    if anim.AnimationId~="" then return anim.AnimationId end
    local sequence=anim:FindFirstChildOfClass("KeyframeSequence")
    if not (sequence and Run:IsStudio()) then return nil end
    local ok,id=pcall(function() return game:GetService("KeyframeSequenceProvider"):RegisterKeyframeSequence(sequence) end)
    if ok then anim.AnimationId=id; return id end
end
-- A clip loaded on your own character, kept while that character lives; nil until the clip is in the place.
function E:Clip(name)
    local character=Players.LocalPlayer.Character; local hum=character and character:FindFirstChildOfClass("Humanoid")
    if not hum then return nil end
    if self.ClipOwner~=hum then self.ClipOwner=hum; self.Clips={} end
    if not self.Clips[name] then
        local id=self:AnimationId(name); if not id then return nil end
        local anim=Instance.new("Animation"); anim.AnimationId=id
        self.Clips[name]=(hum:FindFirstChildOfClass("Animator") or hum):LoadAnimation(anim)
    end
    return self.Clips[name]
end
-- Turn your character to face `point` across the ground, unless a broom is steering it.
function E:Face(point)
    local root=Players.LocalPlayer.Character and Players.LocalPlayer.Character:FindFirstChild("HumanoidRootPart")
    if not root or typeof(point)~="Vector3" or Players.LocalPlayer:GetAttribute("Broom") then return end
    local flat=(point-root.Position)*Vector3.new(1,0,1)
    if flat.Magnitude>0.5 then root.CFrame=CFrame.lookAt(root.Position,root.Position+flat.Unit) end
end
-- Scintara's casts on your own character (blender/animations/character.py), which Roblox shows to everyone: the
-- bolt's flick on a left click, and the lance's thrust, then its braced hold until you let go.
function E:CastBolt(aim)
    self:Face(aim)
    local track=self:Clip("ScintaraBolt"); if track then track:Play(0.05) end
end
function E:LanceStart()
    local pour={Since=os.clock(),Seen=false}; self.Pouring=pour
    local hum=Players.LocalPlayer.Character and Players.LocalPlayer.Character:FindFirstChildOfClass("Humanoid")
    if hum and not Players.LocalPlayer:GetAttribute("Broom") then hum.AutoRotate=false end
    local start,hold=self:Clip("ScintaraBeamStart"),self:Clip("ScintaraBeam")
    if start then start:Play(0.05) end
    -- The thrust is 0.2 s; the hold takes over as it ends.
    if hold then task.delay(start and 0.18 or 0,function() if self.Pouring==pour then hold:Play(0.05) end end) end
end
function E:LanceStop()
    self.Pouring=nil
    for _,name in ipairs({"ScintaraBeamStart","ScintaraBeam"}) do
        local track=self.Clips[name]; if track and track.IsPlaying then track:Stop(0.15) end
    end
    local hum=Players.LocalPlayer.Character and Players.LocalPlayer.Character:FindFirstChildOfClass("Humanoid")
    if hum and not Players.LocalPlayer:GetAttribute("Broom") then hum.AutoRotate=true end
end
-- Every other spell's wand gesture (blender/animations/casting.py): the Cast<Motion> clip SpellData gives it, played
-- on your own character when the server accepts the cast, which Roblox shows to everyone. The wand strikes at the
-- clip's Release marker, CastTime in, as the server lets the spell go, and its tip flashes there. In third person
-- you turn to face the aim and hold it through the gesture.
function E:Gesture(id)
    local spell=Spells[id]; if not (spell and spell.Motion) then return end
    local name="Cast"..spell.Motion; local track=self:Clip(name); if not track then return end
    self.Gesturing=id
    if not self.Marked[track] then
        self.Marked[track]=true
        track:GetMarkerReachedSignal("Release"):Connect(function()
            local tip=self:WandTip(Players.LocalPlayer.Character); if tip then self:Burst(tip,self.Gesturing,1.6) end
        end)
    end
    for other,playing in pairs(self.Clips) do
        if other~=name and other:sub(1,4)=="Cast" and playing.IsPlaying then playing:Stop(0.1) end
    end
    track:Play(0.08)
    -- Fade out over the clip's last fifth of a second, back to whatever the body was doing.
    local played=os.clock(); self.GesturePlayed=played
    task.delay(math.max(0,track.Length-0.2),function() if self.GesturePlayed==played and track.IsPlaying then track:Stop(0.2) end end)
    local hum=self.ClipOwner; local aim=self.C.InputController:Aim()
    if aim and not self.C.InputController:InFirstPerson() and not Players.LocalPlayer:GetAttribute("Broom") then
        self:Face(aim); hum.AutoRotate=false; self.Turned=hum
    end
end
-- Your arms while you cast, each frame before the lances are drawn from the wand. While a cast plays (a gesture or
-- one of Scintara's), the arms tilt about the shoulders toward the aim, so the wand strikes up or down at it; in
-- first person they are also lifted LIFT and turned TURN toward the middle of the view, where the camera, a stud
-- over the shoulders, would see them low (casting.py's LIFT and TURN). In first person your forearms, hands and
-- wand are always drawn, so you see every gesture; the upper arms, a stud from the camera, would fill the view.
local LIFT,TURN=math.rad(14),math.rad(8)
local SEEN={"LeftLowerArm","LeftHand","RightLowerArm","RightHand"}
function E:Arms(dt)
    local character=Players.LocalPlayer.Character
    local hum=character and character:FindFirstChildOfClass("Humanoid"); local root=character and character:FindFirstChild("HumanoidRootPart")
    if not (hum and root) then return end
    local input=self.C.InputController; local first=input:InFirstPerson()
    if first then
        for _,name in ipairs(SEEN) do local p=character:FindFirstChild(name); if p then p.LocalTransparencyModifier=0 end end
        local wand=character:FindFirstChild("RavenmoorWand")
        if wand then for _,p in ipairs(wand:GetDescendants()) do if p:IsA("BasePart") then p.LocalTransparencyModifier=0 end end end
    end
    local weight,gesture=0,false
    if self.ClipOwner==hum then
        for name,track in pairs(self.Clips) do
            local cast=name:sub(1,4)=="Cast"
            if (cast or name:sub(1,8)=="Scintara") and track.WeightCurrent>0.01 then
                weight=math.max(weight,track.WeightCurrent); gesture=gesture or (cast and track.IsPlaying)
            end
        end
    end
    local aim=weight>0 and input:Aim()
    local pitch,yaw=0,0
    if aim then
        local d=aim-(root.Position+Vector3.new(0,0.76,0))   -- from the shoulders
        pitch=math.clamp(math.atan2(d.Y,math.max(Vector3.new(d.X,0,d.Z).Magnitude,1)),-math.rad(55),math.rad(55))
        if first then pitch=pitch+LIFT; yaw=TURN end
        pitch,yaw=pitch*weight,yaw*weight
    end
    local ease=1-math.exp(-18*dt)
    self.Tilt={self.Tilt[1]+(pitch-self.Tilt[1])*ease,self.Tilt[2]+(yaw-self.Tilt[2])*ease}
    for side,turn in pairs({Right=1,Left=-1}) do
        local arm=character:FindFirstChild(side.."UpperArm"); local motor=arm and arm:FindFirstChild(side.."Shoulder")
        if motor and motor:IsA("Motor6D") then
            local rest=self.Shoulders[motor]; if not rest then rest=motor.C0; self.Shoulders[motor]=rest end
            motor.C0=rest*CFrame.Angles(self.Tilt[1],turn*self.Tilt[2],0)
        end
    end
    if self.Turned~=hum then return end
    if gesture and aim and not first then self:Face(aim); return end
    -- The gesture is over, or first person turns you with the camera: let the Humanoid turn again, unless a lance,
    -- a tumble or a broom is holding it.
    self.Turned=nil
    local tumbling=false
    for _,track in pairs(self.Tumbler==hum and self.Tumbles or {}) do tumbling=tumbling or track.IsPlaying end
    if not (self.Pouring or tumbling or Players.LocalPlayer:GetAttribute("Broom")) then hum.AutoRotate=true end
end
-- Every spark lance, each frame: from the caster's wand to where the server's ScintaraLance attribute says it ends
-- (SpellService:Pour), or for your own, to where you aim now. It opens in 0.08 s and closes in 0.15 s. The core
-- and its glow stretch to the length, the Coils tile along it and spin so the twist seems to pour out, three Rings
-- run out along it, the Flash spins at the wand and the Splash pulses where it strikes. Reduced effects keeps the
-- core, the glow and the splash.
local LANCE=Spells.Scintara.Lance
function E:NewLance()
    local lance={Open=0,Coils={},Rings={}}
    local core,coreSize=self:Scintara("Beam")
    lance.Core=core or self:Part(Vector3.one,CFrame.new(),SPARK); lance.Glow=self:Scintara("Beam") or self:Part(Vector3.one,CFrame.new(),colors.Arcane)
    lance.Core.Color=SPARK; lance.Glow.Transparency=0.6; lance.Round=coreSize~=nil
    lance.Flash,lance.FlashSize=self:Scintara("Flash")
    lance.Splash,lance.SplashSize=self:Scintara("Splash")
    if not lance.Splash then
        lance.Splash=self:Part(Vector3.one,CFrame.new(),colors.Arcane); lance.Splash.Shape=Enum.PartType.Ball; lance.SplashSize=Vector3.one*1.4
    end
    if lance.Flash then
        lance.Flash.Color=SPARK
        local light=Instance.new("PointLight"); light.Color=colors.Arcane; light.Range=12; light.Brightness=2.5; light.Parent=lance.Flash
    end
    for i=1,3 do local ring,size=self:Scintara("Ring"); if ring then ring.Color=SPARK; lance.Rings[i]=ring; lance.RingSize=size end end
    return lance
end
function E:DropLance(player)
    local lance=self.Lances[player]; if not lance then return end
    self.Lances[player]=nil
    for _,key in ipairs({"Core","Glow","Flash","Splash"}) do if lance[key] then lance[key]:Destroy() end end
    for _,p in ipairs(lance.Coils) do p:Destroy() end
    for _,p in ipairs(lance.Rings) do p:Destroy() end
end
function E:PlaceLance(player,lance,endpoint)
    local character=player.Character; local root=character and character:FindFirstChild("HumanoidRootPart")
    if not root then return end
    local from=self:WandTip(character) or root.Position+Vector3.new(0,1.2,0)
    local to,struck=nil,false
    if player==Players.LocalPlayer then
        local aim=self.C.InputController:Aim()
        if aim then
            local dir=aim-from; dir=dir.Magnitude>0.1 and dir.Unit or root.CFrame.LookVector
            local params=RaycastParams.new(); params.FilterType=Enum.RaycastFilterType.Exclude; params.FilterDescendantsInstances={character,self.Folder}
            local hit=workspace:Raycast(from,dir*LANCE.Range,params)
            local reach=hit and hit.Distance or LANCE.Range
            -- The server's lance can stop sooner, at a rival's Bastion Dome.
            if typeof(endpoint)=="Vector3" then reach=math.min(reach,(endpoint-from).Magnitude+2) end
            to=from+dir*reach; struck=reach<LANCE.Range-0.5
        end
    elseif typeof(endpoint)=="Vector3" then
        -- The attribute moves ten times a second; glide after it.
        to=lance.Shown and lance.Shown:Lerp(endpoint,0.35) or endpoint
        struck=(endpoint-root.Position).Magnitude<LANCE.Range-1
    end
    to=to or lance.Shown; if not to then return end
    lance.Shown=to
    local length=(to-from).Magnitude; if length<0.05 then return end
    local k=lance.Open; local now=os.clock(); local spin=now*9
    local d=self.C.UIController.Data; local reduced=d and d.Settings.ReducedEffects
    local look=CFrame.lookAt(from,to); local mid=look*CFrame.new(0,0,-length/2)
    local width=lance.Round and 1 or 0.8
    lance.Core.Size=Vector3.new(0.3*k*width,0.3*k*width,length); lance.Core.CFrame=mid
    lance.Glow.Size=Vector3.new(0.95*k*width,0.95*k*width,length); lance.Glow.CFrame=mid
    lance.Splash.Size=lance.SplashSize*k*(0.85+0.15*math.sin(now*25)); lance.Splash.CFrame=CFrame.lookAt(to,to+look.LookVector)*CFrame.Angles(0,0,spin)
    lance.Splash.Transparency=struck and 0.05 or 1
    if lance.Flash then
        lance.Flash.Size=lance.FlashSize*k*(1.1+0.15*math.sin(now*30)); lance.Flash.CFrame=look*CFrame.Angles(0,0,-spin*1.5)
        lance.Flash.Transparency=reduced and 1 or 0.05
    end
    local count=reduced and 0 or math.max(1,math.ceil(length/6)); local each=length/math.max(1,count)
    for i=#lance.Coils+1,count do local coil,size=self:Scintara("Coil"); if not coil then break end; coil.Transparency=0.15; lance.Coils[i]=coil; lance.CoilSize=size end
    for i,coil in ipairs(lance.Coils) do
        if i<=count then
            coil.Size=Vector3.new(lance.CoilSize.X*k,lance.CoilSize.Y*k,each); coil.Transparency=0.15
            coil.CFrame=look*CFrame.new(0,0,-each*(i-0.5))*CFrame.Angles(0,0,spin)
        else coil.Transparency=1 end
    end
    for i,ring in pairs(lance.Rings) do
        local t=(now*2+i/3)%1
        ring.Size=lance.RingSize*k*(0.8+0.6*t); ring.CFrame=look*CFrame.new(0,0,-length*t)
        ring.Transparency=reduced and 1 or 0.2+0.8*t
    end
end
function E:DrawLances(dt)
    local me=Players.LocalPlayer; local now=os.clock()
    -- Your own lance turns you to your aim, and lets go if the server has ended it (out of mana) or never lit it.
    local pour=self.Pouring
    if pour then
        local lit=me:GetAttribute("ScintaraLance")~=nil
        if lit then pour.Seen=true end
        if (pour.Seen and not lit) or (not pour.Seen and now-pour.Since>0.6) then self.C.InputController:Lance(false)
        else self:Face(self.C.InputController:Aim()) end
    end
    for _,player in ipairs(Players:GetPlayers()) do
        local endpoint=player:GetAttribute("ScintaraLance")
        local active=typeof(endpoint)=="Vector3"
        if player==me then active=self.Pouring~=nil and now-self.Pouring.Since>=0.12 end
        local lance=self.Lances[player]
        if active and not lance then lance=self:NewLance(); self.Lances[player]=lance end
        if lance then
            lance.Open=math.clamp(lance.Open+(active and dt/0.08 or -dt/0.15),0,1)
            if lance.Open<=0 and not active then self:DropLance(player) else self:PlaceLance(player,lance,endpoint) end
        end
    end
    for player in pairs(self.Lances) do if not player.Parent then self:DropLance(player) end end
end
-- The default Animate script plays "walk" up to 8 studs a second and "run" at full speed (16).
function E:Movement(character)
    local animate=character:WaitForChild("Animate",10); if not animate then return end
    for slot,clip in pairs({walk="Walk",run="Sprint"}) do
        local value=animate:WaitForChild(slot,5); local anim=value and value:FindFirstChildOfClass("Animation")
        local id=self:AnimationId(clip)
        if anim and id then anim.AnimationId=id end
    end
end
-- Your own dodge turns you to face where the camera looks and tumbles you the way you went: sideways across its
-- view, forward into it or back toward it. Without the clip it turns you to face the way you went, since the
-- server's teleport faces you north.
function E:Roll(to,from)
    local character=Players.LocalPlayer.Character; local camera=workspace.CurrentCamera
    local hum=character and character:FindFirstChildOfClass("Humanoid"); local root=character and character:FindFirstChild("HumanoidRootPart")
    if not (hum and root and camera) or typeof(from)~="Vector3" then return end
    local flat=Vector3.new(1,0,1)
    local path,look,right=(to-from)*flat,camera.CFrame.LookVector*flat,camera.CFrame.RightVector*flat
    if path.Magnitude<0.5 or look.Magnitude<0.1 or right.Magnitude<0.1 then return end
    local side,ahead=path.Unit:Dot(right.Unit),path.Unit:Dot(look.Unit)
    local clip=math.abs(side)>=math.abs(ahead) and (side>0 and "TumbleRight" or "TumbleLeft") or (ahead>0 and "TumbleForward" or "TumbleBack")
    local id=self:AnimationId(clip)
    if not id then root.CFrame=CFrame.lookAt(to,to+path.Unit); return end
    root.CFrame=CFrame.lookAt(to,to+look.Unit)
    if self.Tumbler~=hum then self.Tumbler=hum; self.Tumbles={} end
    local track=self.Tumbles[clip]
    if not track then
        local anim=Instance.new("Animation"); anim.AnimationId=id
        track=(hum:FindFirstChildOfClass("Animator") or hum):LoadAnimation(anim); track.Priority=Enum.AnimationPriority.Action
        self.Tumbles[clip]=track
    end
    -- Hold the facing through the roll; the Humanoid would otherwise turn toward the move direction.
    hum.AutoRotate=false
    track.Stopped:Once(function() hum.AutoRotate=true end)
    track:Play(0.05)
end
function E:Ward(model,duration)
    if typeof(model)~="Instance" or not model.Parent then return end
    local root=model:FindFirstChild("HumanoidRootPart"); if not root then return end
    local p=self:Part(Vector3.one*7,root.CFrame,colors.Ward,Enum.Material.ForceField); p.Shape=Enum.PartType.Ball; p.Transparency=0.6
    local c; c=Run.RenderStepped:Connect(function() if root.Parent and p.Parent then p.CFrame=root.CFrame else c:Disconnect() end end)
    task.delay(duration,function() c:Disconnect(); p:Destroy() end)
end
function E:Label(model)
    if self.Labels[model] then return end
    local root=model:WaitForChild("HumanoidRootPart",5); local hum=model:FindFirstChildOfClass("Humanoid")
    if not root or not hum then return end
    self.Labels[model]=true
    local gui=Instance.new("BillboardGui"); gui.Name="LocalHealth"; gui.Adornee=root; gui.Size=UDim2.fromOffset(150,42)
    gui.StudsOffset=Vector3.new(0,root.Size.Y/2+2,0); gui.MaxDistance=85; gui.AlwaysOnTop=true; gui.Parent=root
    local title=Instance.new("TextLabel"); title.Size=UDim2.new(1,0,0,25); title.BackgroundTransparency=1; title.TextSize=12; title.Font=Enum.Font.GothamMedium
    title.Text=model.Name.."  L"..tostring(model:GetAttribute("Level") or 1); title.TextColor3=Color3.fromRGB(241,231,212); title.TextStrokeTransparency=0.3; title.Parent=gui
    local back=Instance.new("Frame"); back.Size=UDim2.new(1,-20,0,5); back.Position=UDim2.fromOffset(10,29); back.BackgroundColor3=Color3.fromRGB(25,31,36); back.BorderSizePixel=0; back.Parent=gui
    local fill=Instance.new("Frame"); fill.Size=UDim2.fromScale(1,1); fill.BackgroundColor3=colors.Enemy; fill.BorderSizePixel=0; fill.Parent=back
    hum.HealthChanged:Connect(function(health) fill.Size=UDim2.fromScale(math.clamp(health/hum.MaxHealth,0,1),1) end)
    model.Destroying:Connect(function() self.Labels[model]=nil end)
end
function E:UpdateZone()
    local zone=Players.LocalPlayer:GetAttribute("Zone")
    if zone==self.Zone then return end; self.Zone=zone
    local forest=zone=="Whisperwood"
    Tween:Create(self.Correction,TweenInfo.new(2),{TintColor=forest and Color3.fromRGB(194,215,211) or Color3.fromRGB(255,245,227),Saturation=forest and -0.15 or 0.03}):Play()
    Tween:Create(self.Atmosphere,TweenInfo.new(2),{Density=forest and 0.4 or 0.25,Haze=forest and 2 or 1}):Play()
end
function E:Start()
    self.Folder=Instance.new("Folder"); self.Folder.Name="LocalWandboundVFX"; self.Folder.Parent=workspace
    self.Correction=Instance.new("ColorCorrectionEffect"); self.Correction.Name="WandboundZoneColor"; self.Correction.Parent=Lighting
    self.Atmosphere=Lighting:FindFirstChildOfClass("Atmosphere") or Instance.new("Atmosphere",Lighting)
    self.Waypoint=self:Part(Vector3.one*0.1,CFrame.new(0,-1000,0),colors.Ward); self.Waypoint.Transparency=1
    local gui=Instance.new("BillboardGui"); gui.Size=UDim2.fromOffset(180,58); gui.AlwaysOnTop=true; gui.MaxDistance=1000; gui.Parent=self.Waypoint
    self.WaypointLabel=Instance.new("TextLabel"); self.WaypointLabel.Size=UDim2.fromScale(1,1); self.WaypointLabel.BackgroundTransparency=1
    self.WaypointLabel.TextSize=14; self.WaypointLabel.Font=Enum.Font.GothamMedium; self.WaypointLabel.TextColor3=colors.Ward; self.WaypointLabel.TextStrokeTransparency=0.25; self.WaypointLabel.TextWrapped=true; self.WaypointLabel.Parent=gui
    RS.Remotes.FX.OnClientEvent:Connect(function(kind,a,b,c,d,e,f)
        if kind=="Projectile" then self:Projectile(a,b,c,d,e,f)
        elseif kind=="Impact" then self:Impact(a,b)
        elseif kind=="Blast" then self:Burst(a,b,c*2)
        elseif kind=="Damage" then self:Number(a,b,c,false)
        elseif kind=="Heal" then self:Number(a,b,false,true); self:Burst(a,"Restoration",3)
        elseif kind=="Ward" then self:Ward(a,b)
        elseif kind=="Dome" then local p=self:Part(Vector3.one*20,CFrame.new(a),colors.Ward,Enum.Material.ForceField); p.Shape=Enum.PartType.Ball; p.Transparency=0.7; Debris:AddItem(p,b)
        elseif kind=="Beam" then self:Beam(a,b,c)
        elseif kind=="Telegraph" then self:Ring(a,b,c,false)
        elseif kind=="Pool" then self:Ring(a,b,c,true)
        elseif kind=="Dodge" then self:Dash(a,b); if c==Players.LocalPlayer then self:Roll(a,b) end
        elseif kind=="Defeat" then self:Burst(a,"Arcane",4)
        elseif kind=="Status" then self:Burst(a,b,2) end
    end)
    -- A lance the server refuses (no mana, cooling down) lets go at once; any other cast it accepts plays its gesture.
    RS.Remotes.CastReply.OnClientEvent:Connect(function(id,ok)
        if id=="ScintaraLance" and not ok then self.C.InputController:Lance(false) end
        if ok then self:Gesture(id) end
    end)
    Players.LocalPlayer.CharacterAdded:Connect(function(character) self:Movement(character) end)
    if Players.LocalPlayer.Character then task.spawn(function() self:Movement(Players.LocalPlayer.Character) end) end
    task.spawn(function()
        local monsters=workspace:WaitForChild("Runtime"):WaitForChild("Monsters")
        monsters.ChildAdded:Connect(function(model) task.spawn(function() self:Label(model) end) end)
        for _,model in ipairs(monsters:GetChildren()) do task.spawn(function() self:Label(model) end) end
    end)
    local elapsed=0
    Run.RenderStepped:Connect(function(dt)
        for i=#self.Flying,1,-1 do
            local p=self.Flying[i]; local delta=p.Dir*p.Speed*dt
            local hit=workspace:Raycast(p.Pos,delta,p.Params)
            p.Travel=p.Travel+delta.Magnitude
            if hit or p.Travel>=p.Range then self:Retire(i)
            else p.Pos=p.Pos+delta; self:Fly(p) end
        end
        self:Arms(dt)
        self:DrawLances(dt)
        elapsed=elapsed+dt
        if elapsed>0.4 then
            elapsed=0; self:UpdateZone()
            local data=self.C.UIController.Data; local q=data and Quests[data.Quest]; local p=q and Points[q.Anchor]
            if p then
                self.Waypoint.Position=Vector3.new(p[1],p[2]+8,p[3])
                local root=Players.LocalPlayer.Character and Players.LocalPlayer.Character:FindFirstChild("HumanoidRootPart")
                self.WaypointLabel.Text="◇ "..q.Title..(root and "\n"..math.floor((root.Position-self.Waypoint.Position).Magnitude).." studs" or "")
            else self.Waypoint.Position=Vector3.new(0,-1000,0) end
        end
    end)
end
return E
