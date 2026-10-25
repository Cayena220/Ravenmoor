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
function E:Init(controllers) self.C=controllers; self.Pool={}; self.Flying={}; self.Labels={}; self.Zone=nil end
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
function E:Projectile(origin,direction,id,speed,range)
    if #self.Flying>=120 then return end
    local p=table.remove(self.Pool) or self:Part(Vector3.one,CFrame.new(origin),self:Color(id))
    p.Shape=Enum.PartType.Ball; p.Size=Vector3.one*(id=="Scintara" and 0.55 or 1)
    p.Color=self:Color(id); p.Transparency=0.12; p.Position=origin
    -- Server bolts pass through allies; the server's Impact event ends the visual at a character hit.
    local ignored={self.Folder}
    for _,player in ipairs(Players:GetPlayers()) do if player.Character then ignored[#ignored+1]=player.Character end end
    local params=RaycastParams.new(); params.FilterType=Enum.RaycastFilterType.Exclude; params.FilterDescendantsInstances=ignored
    self.Flying[#self.Flying+1]={Part=p,Pos=origin,Dir=direction,Speed=speed,Range=range,Travel=0,Params=params,Id=id}
end
function E:Retire(i)
    local p=self.Flying[i]
    p.Part.Transparency=1; p.Part.Position=Vector3.new(0,-1000,0); self.Pool[#self.Pool+1]=p.Part; table.remove(self.Flying,i)
end
function E:Land(position,id)
    local best,bestDistance=nil,10
    for i,p in ipairs(self.Flying) do
        local distance=(p.Pos-position).Magnitude
        if p.Id==id and distance<bestDistance then best=i; bestDistance=distance end
    end
    if best then self:Retire(best) end
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
    RS.Remotes.FX.OnClientEvent:Connect(function(kind,a,b,c,d,e)
        if kind=="Projectile" then self:Projectile(a,b,c,d,e)
        elseif kind=="Impact" then self:Land(a,b); self:Burst(a,b,3)
        elseif kind=="Blast" then self:Burst(a,b,c*2)
        elseif kind=="Damage" then self:Number(a,b,c,false)
        elseif kind=="Heal" then self:Number(a,b,false,true); self:Burst(a,"Restoration",3)
        elseif kind=="Ward" then self:Ward(a,b)
        elseif kind=="Dome" then local p=self:Part(Vector3.one*20,CFrame.new(a),colors.Ward,Enum.Material.ForceField); p.Shape=Enum.PartType.Ball; p.Transparency=0.7; Debris:AddItem(p,b)
        elseif kind=="Beam" then self:Beam(a,b,c)
        elseif kind=="Telegraph" then self:Ring(a,b,c,false)
        elseif kind=="Pool" then self:Ring(a,b,c,true)
        elseif kind=="Dodge" or kind=="Defeat" then self:Burst(a,"Arcane",4)
        elseif kind=="Status" then self:Burst(a,b,2) end
    end)
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
            else p.Pos=p.Pos+delta; p.Part.Position=p.Pos end
        end
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
