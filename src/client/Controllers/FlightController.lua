local Players=game:GetService("Players")
local RS=game:GetService("ReplicatedStorage")
local UIS=game:GetService("UserInputService")
local Run=game:GetService("RunService")
local Brooms=require(RS.Shared.BroomData)
-- Flies your character while the server has you on a broom (FlightService sets your Broom attribute). The stick
-- steers where the camera looks, so pushing forward climbs or dives with the camera; Space or A climbs straight up
-- and Q or L3 dives. The broom eases toward the wanted speed, banks into turns, pitches with the climb and bobs
-- gently in a hover. You own your character's physics, so the flight is smooth here and replicates to everyone.
local Fl={}
function Fl:Init(controllers) self.C=controllers; self.Player=Players.LocalPlayer end
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
    local track
    local anim=self.C.EffectsController:AnimationId("BroomRide")
    if anim then
        local a=Instance.new("Animation"); a.AnimationId=anim
        track=(hum:FindFirstChildOfClass("Animator") or hum):LoadAnimation(a)
        track.Priority=Enum.AnimationPriority.Action; track.Looped=true; track:Play(0.25)
    end
    local v=root.AssemblyLinearVelocity
    self.Flight={Broom=broom,Hum=hum,Root=root,Attach=attach,Push=push,Turn=turn,Track=track,
        Velocity=Vector3.new(v.X,math.max(v.Y,0),v.Z)*0.5,Yaw=nil,Bank=0}
end
function Fl:End()
    local f=self.Flight; self.Flight=nil
    if not f then return end
    if f.Track then f.Track:Stop(0.25) end
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
function Fl:Start()
    local function changed()
        local id=self.Player:GetAttribute("Broom")
        if id then self:Begin(id) else self:End() end
    end
    self.Player:GetAttributeChangedSignal("Broom"):Connect(changed)
    self.Player.CharacterAdded:Connect(function() self:End() end)
    Run.RenderStepped:Connect(function(dt) self:Step(math.min(dt,0.1)) end)
    if self.Player:GetAttribute("Broom") then task.defer(changed) end
end
return Fl
