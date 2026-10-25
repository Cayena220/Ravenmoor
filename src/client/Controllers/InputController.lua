local Players=game:GetService("Players")
local RS=game:GetService("ReplicatedStorage")
local UIS=game:GetService("UserInputService")
local CAS=game:GetService("ContextActionService")
local Run=game:GetService("RunService")
local I={}
function I:Init(controllers) self.C=controllers; self.Player=Players.LocalPlayer; self.Locked=true; self.Holding=false; self.LastCast=0 end
function I:CameraMode()
    local open=self.C.UIController:IsOpen() or UIS:GetFocusedTextBox()~=nil
    if self.Controls and open~=self.ControlsPaused then
        self.ControlsPaused=open
        if open then self.Controls:Disable() else self.Controls:Enable() end
    end
    UIS.MouseBehavior=(self.Locked and not open and not UIS.TouchEnabled) and Enum.MouseBehavior.LockCenter or Enum.MouseBehavior.Default
    UIS.MouseIconEnabled=open or not self.Locked
    local character=self.Player.Character; local hum=character and character:FindFirstChildOfClass("Humanoid")
    if hum then hum.CameraOffset=not open and Vector3.new(1.6,0.5,0) or Vector3.zero end
end
function I:ToggleMenu(menu)
    local ui=self.C.UIController
    self.Holding=false
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
function I:UseSlot(slot)
    local ui=self.C.UIController
    if ui:IsOpen() or UIS:GetFocusedTextBox() then return end
    local d=ui.Data; if not d then return end
    if slot=="Dodge" then
        local hum=self.Player.Character and self.Player.Character:FindFirstChildOfClass("Humanoid")
        if hum then ui:Action("Dodge",hum.MoveDirection) end
        return
    end
    local id=slot=="Basic" and "Scintara" or d.Loadout[slot]
    if not id or id=="" then return ui:Toast("This slot is empty. Open the spellbook (K) to assign a spell.") end
    if not d.HasWand then return ui:Toast("Visit Oakhart in Hollowmere to receive your wand.") end
    if (ui.Cooldowns[id] or 0)>os.clock() then return end
    local aim=self:Aim(); if aim then RS.Remotes.Cast:FireServer(id,aim); self.LastCast=os.clock() end
end
function I:Start()
    task.spawn(function()
        local module=self.Player:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule",15)
        if module then self.Controls=require(module):GetControls(); self:CameraMode() end
    end)
    local bindings={
        Basic={Enum.UserInputType.MouseButton1,Enum.KeyCode.ButtonR2},
        Ward={Enum.UserInputType.MouseButton2,Enum.KeyCode.ButtonL2},
        Slot1={Enum.KeyCode.One,Enum.KeyCode.ButtonX}, Slot2={Enum.KeyCode.Two,Enum.KeyCode.ButtonY},
        Slot3={Enum.KeyCode.Three,Enum.KeyCode.ButtonB}, Slot4={Enum.KeyCode.Four,Enum.KeyCode.ButtonR1},
        Dodge={Enum.KeyCode.LeftShift,Enum.KeyCode.ButtonL1},
    }
    for slot,keys in pairs(bindings) do
        CAS:BindActionAtPriority("Wandbound_"..slot,function(_,state,input)
            if slot=="Basic" and (state==Enum.UserInputState.End or state==Enum.UserInputState.Cancel) then self.Holding=false end
            if self.C.UIController:IsOpen() or UIS:GetFocusedTextBox() then self.Holding=false; return Enum.ContextActionResult.Pass end
            if input.UserInputType==Enum.UserInputType.MouseButton1 then
                local pos=UIS:GetMouseLocation()
                for _,gui in ipairs(self.Player.PlayerGui:GetGuiObjectsAtPosition(pos.X,pos.Y)) do
                    if gui:IsA("GuiButton") then return Enum.ContextActionResult.Pass end
                end
            end
            if slot=="Basic" and state==Enum.UserInputState.Begin then self.Holding=true end
            if state==Enum.UserInputState.Begin then self:UseSlot(slot) end
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
    end)
    UIS.WindowFocusReleased:Connect(function() self.Holding=false end)
    UIS.TextBoxFocused:Connect(function() self.Holding=false; self:CameraMode() end)
    UIS.TextBoxFocusReleased:Connect(function() task.defer(function() self:CameraMode() end) end)
    self.Player.CharacterAdded:Connect(function() self.Holding=false; task.delay(0.5,function() self:CameraMode() end) end)
    self.Player.CameraMinZoomDistance=5; self.Player.CameraMaxZoomDistance=14
    local elapsed=0
    Run:BindToRenderStep("WandboundCamera",Enum.RenderPriority.Camera.Value+1,function(dt)
        self:CameraMode(); elapsed=elapsed+dt
        if self.Holding and os.clock()-self.LastCast>0.62 then self:UseSlot("Basic") end
        if elapsed>0.12 then elapsed=0; local aim=self:Aim(); if aim then RS.Remotes.Aim:FireServer(aim) end end
    end)
end
return I
