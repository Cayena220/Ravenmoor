local Players=game:GetService("Players")
local RS=game:GetService("ReplicatedStorage")
local UIS=game:GetService("UserInputService")
local Run=game:GetService("RunService")
local Tween=game:GetService("TweenService")
local Debris=game:GetService("Debris")
local Brooms=require(RS.Shared.BroomData)
local Config=require(RS.Shared.Config)
-- Flies your character while the server has you on a broom (FlightService sets your Broom attribute). The stick
-- steers where the camera looks, so pushing forward climbs or dives with the camera; Space or A climbs straight up
-- and Q or L3 dives. The broom eases toward the wanted speed, banks into turns, pitches with the climb and bobs
-- gently in a hover. You own your character's physics, so the flight is smooth here and replicates to everyone.
-- Flown flat out, a rider dashes through the air: they tuck into the wind in their house's own way, and every
-- client draws the wind streaming round them in their house colour.
local Fl={}
local DASH_IN,DASH_OUT=0.8,0.6   -- of the broom's top speed: start dashing above the first, stop below the second
local WIND=Color3.fromRGB(194,163,255)   -- for riders not yet in a house: the arcane violet
function Fl:Init(controllers) self.C=controllers; self.Player=Players.LocalPlayer; self.Streams={} end
function Fl:IsFlying() return self.Flight~=nil end
function Fl:Climb()
    local pad=Enum.UserInputType.Gamepad1
    local up=UIS:IsKeyDown(Enum.KeyCode.Space) or UIS:IsGamepadButtonDown(pad,Enum.KeyCode.ButtonA)
    local down=UIS:IsKeyDown(Enum.KeyCode.Q) or UIS:IsGamepadButtonDown(pad,Enum.KeyCode.ButtonL3)
    return (up and 1 or 0)-(down and 1 or 0)
end
function Fl:Begin(id)
    self:End()
    local character=self.Player.Character; local hum=character and character:FindFirstChildOfClass("Humanoid")
    local root=character and character:FindFirstChild("HumanoidRootPart"); local broom=Brooms.Brooms[id]
    if not (hum and root and broom) then return end
    local attach=Instance.new("Attachment"); attach.Name="BroomFlight"; attach.Parent=root
    local push=Instance.new("LinearVelocity"); push.Name="BroomPush"; push.Attachment0=attach
    push.RelativeTo=Enum.ActuatorRelativeTo.World; push.VelocityConstraintMode=Enum.VelocityConstraintMode.Vector
    push.MaxForce=math.huge; push.VectorVelocity=Vector3.zero; push.Parent=root
    local turn=Instance.new("AlignOrientation"); turn.Name="BroomTurn"; turn.Mode=Enum.OrientationAlignmentMode.OneAttachment
    turn.Attachment0=attach; turn.MaxTorque=math.huge; turn.Responsiveness=12+broom.Handling*3
    local look=root.CFrame.LookVector*Vector3.new(1,0,1)
    turn.CFrame=CFrame.lookAt(Vector3.zero,look.Magnitude>0.1 and look.Unit or Vector3.new(0,0,-1)); turn.Parent=root
    hum.PlatformStand=true; hum.AutoRotate=false
    -- Each broom has a ride of its own and, for each house, a dash (blender/animations/character.py); BroomRide is
    -- the plain pose for any other broom.
    local effects,animator=self.C.EffectsController,hum:FindFirstChildOfClass("Animator") or hum
    local function load(name)
        local anim=effects:AnimationId(name); if not anim then return nil end
        local a=Instance.new("Animation"); a.AnimationId=anim
        local track=animator:LoadAnimation(a); track.Priority=Enum.AnimationPriority.Action; track.Looped=true
        return track
    end
    local track=load("BroomRide"..id) or load("BroomRide")
    local house=self.Player:GetAttribute("House")
    local dash=type(house)=="string" and house~="" and load("BroomDash"..house..id) or nil
    if track then track:Play(0.25) end
    local v=root.AssemblyLinearVelocity
    self.Flight={Broom=broom,Hum=hum,Root=root,Attach=attach,Push=push,Turn=turn,Track=track,Dash=dash,Dashing=false,
        Velocity=Vector3.new(v.X,math.max(v.Y,0),v.Z)*0.5,Yaw=nil,Bank=0}
end
function Fl:End()
    local f=self.Flight; self.Flight=nil
    if not f then return end
    if f.Track then f.Track:Stop(0.25) end
    if f.Dash then f.Dash:Stop(0.25) end
    f.Push:Destroy(); f.Turn:Destroy(); f.Attach:Destroy()
    if f.Hum.Parent then f.Hum.PlatformStand=false; f.Hum.AutoRotate=true; f.Hum:ChangeState(Enum.HumanoidStateType.Freefall) end
    if f.Root.Parent then
        -- Stand upright, facing the way you flew, and drop straight down rather than skid on.
        local look=f.Root.CFrame.LookVector*Vector3.new(1,0,1)
        if look.Magnitude>0.1 then f.Root.CFrame=CFrame.lookAt(f.Root.Position,f.Root.Position+look) end
        f.Root.AssemblyLinearVelocity=Vector3.new(0,math.min(0,f.Root.AssemblyLinearVelocity.Y),0)
    end
end
function Fl:Step(dt)
    local f=self.Flight; if not f then return end
    if not f.Root.Parent or f.Hum.Health<=0 then return self:End() end
    local camera=workspace.CurrentCamera; local b=f.Broom
    local busy=self.C.UIController:IsOpen() or UIS:GetFocusedTextBox()~=nil
    local controls=self.C.InputController.Controls
    local stick=controls and controls:GetMoveVector() or Vector3.zero
    local move=Vector3.zero
    if not busy and stick.Magnitude>0.05 then
        move=camera.CFrame.RightVector*stick.X-camera.CFrame.LookVector*stick.Z
        if move.Magnitude>1 then move=move.Unit end
    end
    local want=move*b.Speed+Vector3.new(0,(busy and 0 or self:Climb())*b.Climb,0)
    if want.Y>0 and f.Root.Position.Y>=Brooms.Ceiling then want=Vector3.new(want.X,0,want.Z) end
    f.Velocity=f.Velocity:Lerp(want,1-math.exp(-b.Handling*0.45*dt))
    -- A hover bobs gently; full speed flies level.
    local hover=1-math.min(1,f.Velocity.Magnitude/8)
    f.Push.VectorVelocity=f.Velocity+Vector3.new(0,math.cos(os.clock()*2.2)*0.9*hover,0)
    -- Flat out, the house's dash takes over from the ride. Either plays slower in a hover and quicker at speed.
    local pace=f.Velocity.Magnitude/math.max(b.Speed,1)
    local dashing=pace>=(f.Dashing and DASH_OUT or DASH_IN)
    if dashing~=f.Dashing and f.Dash then
        local from,to=dashing and f.Track or f.Dash,dashing and f.Dash or f.Track
        if from then from:Stop(0.3) end
        if to then to:Play(0.3) end
    end
    f.Dashing=dashing
    local playing=f.Dashing and f.Dash or f.Track
    if playing then playing:AdjustSpeed(0.75+0.5*math.min(1,pace)) end
    local flat=Vector3.new(f.Velocity.X,0,f.Velocity.Z)
    local facing=flat.Magnitude>3 and flat.Unit or camera.CFrame.LookVector*Vector3.new(1,0,1)
    if facing.Magnitude<0.1 then return end
    facing=facing.Unit
    -- Bank into turns, by how fast the heading swings, and pitch the nose with the climb.
    local yaw=math.atan2(-facing.X,-facing.Z)
    local swing=f.Yaw and (yaw-f.Yaw+math.pi)%(2*math.pi)-math.pi or 0; f.Yaw=yaw
    local bank=math.clamp(swing/math.max(dt,1/240)*0.22,-0.6,0.6)*math.min(1,flat.Magnitude/12)
    f.Bank=f.Bank+(bank-f.Bank)*(1-math.exp(-5*dt))
    local pitch=math.clamp(f.Velocity.Y/math.max(b.Speed,1),-0.6,0.6)*0.6
    f.Turn.CFrame=CFrame.lookAt(Vector3.zero,facing)*CFrame.Angles(pitch,0,f.Bank)
end
-- The wind round every rider dashing through the air, drawn here for each one: the dodge's Blender meshes
-- (ReplicatedStorage.VFX.DashVFX, blender/vfx/dash.py) in the rider's house colour. The streak's two ribbons wrap the
-- rider and spin, the speed lines stream past and fade, and the shock ring bursts as the dash begins.
function Fl:Wind(player,dt,kit,reduced)
    local w=self.Streams[player]
    local character=player.Character; local root=character and character:FindFirstChild("HumanoidRootPart")
    local broom=Brooms.Brooms[player:GetAttribute("Broom") or ""]
    local v=root and root.AssemblyLinearVelocity or Vector3.zero
    local pace=broom and v.Magnitude/math.max(broom.Speed,1) or 0
    if not w then
        if not (root and broom and kit and pace>=DASH_IN) then return end
        w={Level=0,Spin=0,Dashing=false,Parts={}}; self.Streams[player]=w
        for _,name in ipairs({"Streak","Speed lines"}) do
            local template=kit:FindFirstChild(name)
            if template then
                local p=template:Clone(); p.Anchored=true; p.CanCollide=false; p.CanTouch=false; p.CanQuery=false
                p.CastShadow=false; p.Material=Enum.Material.Neon; p.Transparency=1; p.Parent=self.C.EffectsController.Folder
                w.Parts[name]=p
            end
        end
    end
    w.Dashing=root~=nil and broom~=nil and pace>=(w.Dashing and DASH_OUT or DASH_IN)
    local was=w.Level
    w.Level=w.Level+((w.Dashing and 1 or 0)-w.Level)*(1-math.exp(-(w.Dashing and 6 or 4)*dt))
    if not root or not w.Dashing and w.Level<0.02 then
        for _,p in pairs(w.Parts) do p:Destroy() end
        self.Streams[player]=nil; return
    end
    local house=Config.Houses[player:GetAttribute("House") or ""]
    local color=house and Color3.fromRGB(table.unpack(house.Color)) or WIND
    local dir=v.Magnitude>1 and v.Unit or root.CFrame.LookVector
    local centre=root.Position-root.CFrame.UpVector*0.7
    w.Spin=(w.Spin+dt*(5+4*math.min(pace,1.5)))%(2*math.pi)
    local streak=w.Parts.Streak
    if streak then
        -- Round the rider and trailing well behind, its ribbons turning about the line of flight.
        local base=kit.Streak.Size
        streak.Size=Vector3.new(base.X*1.7,base.Y*1.7,12); streak.Color=color
        streak.CFrame=CFrame.lookAt(centre-dir*4,centre-dir*4+dir)*CFrame.Angles(0,0,w.Spin)
        streak.Transparency=1-w.Level*(reduced and 0.35 or 0.6)
    end
    local lines=w.Parts["Speed lines"]
    if lines then
        -- Each pass slides three studs back and fades out, then begins again ahead.
        local slide=(os.clock()*9)%3
        local base=kit["Speed lines"].Size
        lines.Size=Vector3.new(base.X*1.4,base.Y*1.4,base.Z*1.2); lines.Color=color
        lines.CFrame=CFrame.lookAt(centre-dir*(1+slide),centre-dir*slide)*CFrame.Angles(0,0,w.Spin*0.3)
        lines.Transparency=reduced and 1 or 1-w.Level*0.55*(1-slide/3)
    end
    local ring=kit:FindFirstChild("Ring")
    if ring and not reduced and was<0.3 and w.Level>=0.3 then
        local p=ring:Clone(); p.Anchored=true; p.CanCollide=false; p.CanTouch=false; p.CanQuery=false; p.CastShadow=false
        p.Material=Enum.Material.Neon; p.Color=color; p.Transparency=0.2; p.CFrame=CFrame.lookAt(centre,centre+dir)
        p.Parent=self.C.EffectsController.Folder
        Tween:Create(p,TweenInfo.new(0.4,Enum.EasingStyle.Quad,Enum.EasingDirection.Out),{Size=ring.Size*3,Transparency=1}):Play()
        Debris:AddItem(p,0.45)
    end
end
function Fl:Winds(dt)
    local kit=RS:FindFirstChild("VFX") and RS.VFX:FindFirstChild("DashVFX")
    local d=self.C.UIController.Data; local reduced=d and d.Settings.ReducedEffects
    local seen={}
    for _,player in ipairs(Players:GetPlayers()) do
        seen[player]=true
        if player:GetAttribute("Broom") or self.Streams[player] then self:Wind(player,dt,kit,reduced) end
    end
    for player,w in pairs(self.Streams) do
        if not seen[player] then for _,p in pairs(w.Parts) do p:Destroy() end; self.Streams[player]=nil end
    end
end
function Fl:Start()
    local function changed()
        local id=self.Player:GetAttribute("Broom")
        if id then self:Begin(id) else self:End() end
    end
    self.Player:GetAttributeChangedSignal("Broom"):Connect(changed)
    self.Player.CharacterAdded:Connect(function() self:End() end)
    Run.RenderStepped:Connect(function(dt) dt=math.min(dt,0.1); self:Step(dt); self:Winds(dt) end)
    if self.Player:GetAttribute("Broom") then task.defer(changed) end
end
return Fl
