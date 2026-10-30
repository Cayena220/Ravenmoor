local Players=game:GetService("Players")
local RS=game:GetService("ReplicatedStorage")
local UIS=game:GetService("UserInputService")
local CAS=game:GetService("ContextActionService")
local Run=game:GetService("RunService")
local Prompts=game:GetService("ProximityPromptService")
local I={}
function I:Init(controllers) self.C=controllers; self.Player=Players.LocalPlayer; self.Locked=true; self.Lancing=false; self.LastCast=0; self.VisiblePrompts={}; self.Taps={} end
function I:CameraMode()
    local open=self.C.UIController:IsOpen() or UIS:GetFocusedTextBox()~=nil
    if self.Controls and open~=self.ControlsPaused then
        self.ControlsPaused=open
        if open then self.Controls:Disable() else self.Controls:Enable() end
    end
    UIS.MouseBehavior=(self.Locked and not open and not UIS.TouchEnabled) and Enum.MouseBehavior.LockCenter or Enum.MouseBehavior.Default
    UIS.MouseIconEnabled=open or not self.Locked
    local character=self.Player.Character; local hum=character and character:FindFirstChildOfClass("Humanoid")
    if hum then hum.CameraOffset=not open and not self:InFirstPerson() and Vector3.new(1.6,0.5,0) or Vector3.zero end
end
-- First person: scroll all the way in, or press V to lock it on and off.
function I:InFirstPerson()
    local camera=workspace.CurrentCamera
    return self.Player.CameraMode==Enum.CameraMode.LockFirstPerson or (camera~=nil and (camera.CFrame.Position-camera.Focus.Position).Magnitude<1)
end
function I:SetFirstPerson(on)
    self.Player.CameraMode=on and Enum.CameraMode.LockFirstPerson or Enum.CameraMode.Classic
    if not on then
        -- Push the camera back out to its usual over-the-shoulder distance.
        self.Player.CameraMinZoomDistance=10
        task.delay(0.1,function() self.Player.CameraMinZoomDistance=0.5 end)
    end
end
function I:ToggleMenu(menu)
    local ui=self.C.UIController
    self:Lance(false)
    if ui.Menu==menu then ui:Close() else ui:Show(menu) end
end
function I:Aim()
    local camera=workspace.CurrentCamera; local character=self.Player.Character
    local root=character and character:FindFirstChild("HumanoidRootPart")
    if not camera or not root then return nil end
    local screen=camera.ViewportSize/2
    local ray=camera:ViewportPointToRay(screen.X,screen.Y)
    if not self.Locked and UIS:GetLastInputType()~=Enum.UserInputType.Touch
        and not tostring(UIS:GetLastInputType()):find("Gamepad") then
        local mouse=UIS:GetMouseLocation()
        ray=camera:ScreenPointToRay(mouse.X,mouse.Y)
    end
    local params=RaycastParams.new(); params.FilterType=Enum.RaycastFilterType.Exclude
    local ignored={character}; if self.C.EffectsController.Folder then ignored[#ignored+1]=self.C.EffectsController.Folder end
    params.FilterDescendantsInstances=ignored
    local result=workspace:Raycast(ray.Origin,ray.Direction*220,params)
    local point=result and result.Position or ray.Origin+ray.Direction*170
    if UIS:GetLastInputType()==Enum.UserInputType.Touch or tostring(UIS:GetLastInputType()):find("Gamepad") then
        local runtime=workspace:FindFirstChild("Runtime"); local monsters=runtime and runtime:FindFirstChild("Monsters")
        local best=math.cos(math.rad(10))
        if monsters then for _,model in ipairs(monsters:GetChildren()) do
            local target=model.PrimaryPart; local hum=model:FindFirstChildOfClass("Humanoid")
            if target and hum and hum.Health>0 then
                local delta=target.Position-ray.Origin
                if delta.Magnitude>1 and delta.Magnitude<155 then
                    local dot=delta.Unit:Dot(ray.Direction)
                    if dot>best then
                        local obstacle=workspace:Raycast(ray.Origin,delta,params)
                        if not obstacle or obstacle.Instance:IsDescendantOf(model) then best=dot; point=target.Position end
                    end
                end
            end
        end end
    end
    local delta=point-root.Position
    if delta.Magnitude>180 then point=root.Position+delta.Unit*180 end
    return point
end
function I:UseSlot(slot,direction)
    local ui=self.C.UIController
    if ui:IsOpen() or UIS:GetFocusedTextBox() then return end
    local d=ui.Data; if not d then return end
    -- A dodge or the broom ends the spark lance (as the server does); no other spell is cast while it pours.
    if self.Lancing then if slot=="Dodge" or slot=="Broom" then self:Lance(false) else return end end
    if slot=="Dodge" then
        local hum=self.Player.Character and self.Player.Character:FindFirstChildOfClass("Humanoid")
        if hum then ui:Action("Dodge",direction or hum.MoveDirection) end
        return
    end
    if slot=="Broom" then return ui:Action("Fly") end
    local id=slot=="Basic" and "Scintara" or d.Loadout[slot]
    if not id or id=="" then return ui:Toast("This slot is empty. Open the spellbook (K) to assign a spell.") end
    if not d.HasWand then return ui:Toast("Visit Oakhart in Hollowmere to receive your wand.") end
    if (ui.Cooldowns[id] or 0)>os.clock() then return end
    -- One spark bolt a click: the flick plays at once, and again only once the bolt's cooldown could be over.
    if slot=="Basic" and os.clock()-self.LastCast<0.45 then return end
    local aim=self:Aim()
    if aim then
        RS.Remotes.Cast:FireServer(id,aim); self.LastCast=os.clock()
        if slot=="Basic" then self.C.EffectsController:CastBolt(aim) end
    end
end
-- Scintara's spark lance pours while the right mouse button (LT, or the touch Lance button) is held, and stops when
-- it is let go (SpellService:Channel). The server ends it too when the mana runs out, and EffectsController stops
-- the hold when the lance's ScintaraLance attribute goes.
function I:Lance(on)
    local ui=self.C.UIController
    if not on then
        if self.Lancing then self.Lancing=false; RS.Remotes.Channel:FireServer(false); self.C.EffectsController:LanceStop() end
        return
    end
    if self.Lancing or ui:IsOpen() or UIS:GetFocusedTextBox() then return end
    local d=ui.Data; if not d then return end
    if not d.HasWand then return ui:Toast("Visit Oakhart in Hollowmere to receive your wand.") end
    if self.Player:GetAttribute("Broom") or (ui.Cooldowns.ScintaraLance or 0)>os.clock() then return end
    local aim=self:Aim(); if aim then RS.Remotes.Aim:FireServer(aim) end
    self.Lancing=true; RS.Remotes.Channel:FireServer(true); self.C.EffectsController:LanceStart()
end
-- Tap W, A, S or D twice quickly to dodge forward, left, back or right as the camera sees it.
local DOUBLE_TAP=0.3
local TAP_WAYS={[Enum.KeyCode.W]={0,1},[Enum.KeyCode.A]={-1,0},[Enum.KeyCode.S]={0,-1},[Enum.KeyCode.D]={1,0}}   -- {right, ahead}
function I:Tap(key)
    local way=TAP_WAYS[key]; local camera=workspace.CurrentCamera
    if not way or not camera or self.C.UIController:IsOpen() or UIS:GetFocusedTextBox() then return end
    if self.Player:GetAttribute("Broom") then return end   -- on a broom, W A S D steer
    local now=os.clock(); local last=self.Taps[key]
    if not (last and now-last<=DOUBLE_TAP) then self.Taps={[key]=now}; return end
    self.Taps={}
    local right=camera.CFrame.RightVector*Vector3.new(1,0,1); if right.Magnitude<0.1 then return end
    right=right.Unit
    self:UseSlot("Dodge",right*way[1]+Vector3.yAxis:Cross(right)*way[2])
end
function I:Start()
    Prompts.PromptShown:Connect(function(prompt) self.VisiblePrompts[prompt]=true end)
    Prompts.PromptHidden:Connect(function(prompt) self.VisiblePrompts[prompt]=nil end)
    task.spawn(function()
        local module=self.Player:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule",15)
        if module then self.Controls=require(module):GetControls(); self:CameraMode() end
    end)
    local bindings={
        Basic={Enum.UserInputType.MouseButton1,Enum.KeyCode.ButtonR2},
        Lance={Enum.UserInputType.MouseButton2,Enum.KeyCode.ButtonL2},
        Ward={Enum.KeyCode.R,Enum.KeyCode.ButtonR3},
        Slot1={Enum.KeyCode.One,Enum.KeyCode.ButtonX}, Slot2={Enum.KeyCode.Two,Enum.KeyCode.ButtonY},
        Slot3={Enum.KeyCode.Three,Enum.KeyCode.ButtonB}, Slot4={Enum.KeyCode.Four,Enum.KeyCode.ButtonR1},
        Dodge={Enum.KeyCode.LeftShift,Enum.KeyCode.ButtonL1},
        Broom={Enum.KeyCode.F,Enum.KeyCode.DPadDown},
    }
    for slot,keys in pairs(bindings) do
        CAS:BindActionAtPriority("Wandbound_"..slot,function(_,state,input)
            if slot=="Lance" and (state==Enum.UserInputState.End or state==Enum.UserInputState.Cancel) then self:Lance(false) end
            if self.C.UIController:IsOpen() or UIS:GetFocusedTextBox() then self:Lance(false); return Enum.ContextActionResult.Pass end
            -- Let the visible prompt receive its gamepad key instead of casting a spell.
            if tostring(input.UserInputType):find("Gamepad") then
                for prompt in pairs(self.VisiblePrompts) do
                    if prompt.Parent and prompt.Enabled and prompt.GamepadKeyCode==input.KeyCode then
                        return Enum.ContextActionResult.Pass
                    end
                end
            end
            if input.UserInputType==Enum.UserInputType.MouseButton1 then
                local pos=UIS:GetMouseLocation()
                for _,gui in ipairs(self.Player.PlayerGui:GetGuiObjectsAtPosition(pos.X,pos.Y)) do
                    if gui:IsA("GuiButton") then return Enum.ContextActionResult.Pass end
                end
            end
            if state==Enum.UserInputState.Begin then if slot=="Lance" then self:Lance(true) else self:UseSlot(slot) end end
            return Enum.ContextActionResult.Sink
        end,false,Enum.ContextActionPriority.High.Value,table.unpack(keys))
    end
    local menus={Book={"Spells",Enum.KeyCode.K,Enum.KeyCode.DPadUp},Bag={"Bag",Enum.KeyCode.B,Enum.KeyCode.DPadLeft},Map={"Map",Enum.KeyCode.M,Enum.KeyCode.DPadRight}}
    for action,entry in pairs(menus) do
        CAS:BindAction("Wandbound_"..action,function(_,state)
            if UIS:GetFocusedTextBox() then return Enum.ContextActionResult.Pass end
            if state==Enum.UserInputState.Begin then self:ToggleMenu(entry[1]) end
            return Enum.ContextActionResult.Sink
        end,false,entry[2],entry[3])
    end
    UIS.InputBegan:Connect(function(input,processed)
        if not processed and input.KeyCode==Enum.KeyCode.LeftControl then self.Locked=not self.Locked; self:CameraMode() end
        if not processed and input.KeyCode==Enum.KeyCode.V then self:SetFirstPerson(self.Player.CameraMode~=Enum.CameraMode.LockFirstPerson) end
        if not processed then self:Tap(input.KeyCode) end
    end)
    UIS.WindowFocusReleased:Connect(function() self:Lance(false) end)
    UIS.TextBoxFocused:Connect(function() self:Lance(false); self:CameraMode() end)
    UIS.TextBoxFocusReleased:Connect(function() task.defer(function() self:CameraMode() end) end)
    self.Player.CharacterAdded:Connect(function() self:Lance(false); task.delay(0.5,function() self:CameraMode() end) end)
    self.Player.CameraMinZoomDistance=0.5; self.Player.CameraMaxZoomDistance=14
    local elapsed=0
    Run:BindToRenderStep("WandboundCamera",Enum.RenderPriority.Camera.Value+1,function(dt)
        self:CameraMode(); elapsed=elapsed+dt
        if elapsed>0.12 then elapsed=0; local aim=self:Aim(); if aim then RS.Remotes.Aim:FireServer(aim) end end
    end)
end
return I
