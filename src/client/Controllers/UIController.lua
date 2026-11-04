local Players=game:GetService("Players")
local RS=game:GetService("ReplicatedStorage")
local UIS=game:GetService("UserInputService")
local GuiService=game:GetService("GuiService")
local Run=game:GetService("RunService")
local Tween=game:GetService("TweenService")
local TextService=game:GetService("TextService")
local Config=require(RS.Shared.Config)
local Spells=require(RS.Shared.SpellData)
local Quests=require(RS.Shared.QuestData)
local F=require(RS.Shared.Formulas)
local Gesture=require(RS.Shared.Gesture)
local Wands=require(RS.Shared.WandData)
local WandModel=require(RS.Shared.WandModel)
local Skills=require(RS.Shared.SkillData)
local Brooms=require(RS.Shared.BroomData)
local Points=require(RS.Shared.WorldPoints)
local Icons=require(script.Parent:WaitForChild("HudIcons"))
local U={}
local function num(x) return string.format("%g",math.floor(x*10+0.5)/10) end
-- Dark glass, pale silver lines and a little gold: the HUD and every menu share these.
local palette={Ink=Color3.fromRGB(20,23,28),Panel=Color3.fromRGB(20,23,28),Gold=Color3.fromRGB(226,197,138),
    Muted=Color3.fromRGB(150,144,132),White=Color3.fromRGB(247,242,232),Line=Color3.fromRGB(244,239,228),
    Text=Color3.fromRGB(247,242,232),TextDim=Color3.fromRGB(191,182,164),Card=Color3.fromRGB(255,255,255),
    Teal=Color3.fromRGB(159,225,203),Arrow=Color3.fromRGB(207,195,255),HP=Color3.fromRGB(111,191,74),
    Mana=Color3.fromRGB(78,143,216),Stamina=Color3.fromRGB(234,223,180),Boss=Color3.fromRGB(192,79,134)}
local SLOTS={"Slot1","Slot2","Slot3","Slot4"}
local PAD={Slot1="X",Slot2="Y",Slot3="B",Slot4="RB"}
local NUMBER_KEYS={[Enum.KeyCode.One]=1,[Enum.KeyCode.Two]=2,[Enum.KeyCode.Three]=3,[Enum.KeyCode.Four]=4,[Enum.KeyCode.Five]=5,
    [Enum.KeyCode.Six]=6,[Enum.KeyCode.Seven]=7,[Enum.KeyCode.Eight]=8,[Enum.KeyCode.Nine]=9}
local MAP_RANGE=250   -- studs from the minimap's centre to its rim
local CARDINALS={N=Vector2.new(0,-1),E=Vector2.new(1,0),S=Vector2.new(0,1),W=Vector2.new(-1,0)}   -- world X, Z
local DRAUGHT="Health Draught"
local function make(class,parent,props)
    local inst=Instance.new(class); for k,v in pairs(props or {}) do inst[k]=v end; inst.Parent=parent; return inst
end
local function corner(frame,radius) make("UICorner",frame,{CornerRadius=UDim.new(0,radius or 8)}) end
local function round(frame) make("UICorner",frame,{CornerRadius=UDim.new(0.5,0)}) end
local function stroke(frame,color,transparency,thickness)
    return make("UIStroke",frame,{Color=color or palette.Gold,Thickness=thickness or 1,Transparency=transparency or 0,ApplyStrokeMode=Enum.ApplyStrokeMode.Border})
end
local function text(parent,txt,size,color,props)
    local p={Text=txt,TextSize=size or 16,TextColor3=color or palette.Text,Font=Enum.Font.Gotham,
        TextXAlignment=Enum.TextXAlignment.Left,TextYAlignment=Enum.TextYAlignment.Center,BackgroundTransparency=1,Size=UDim2.new(1,0,0,30)}
    for k,v in pairs(props or {}) do p[k]=v end; return make("TextLabel",parent,p)
end
-- HUD text sits on the open world, so it carries a soft dark outline.
local function hud(parent,txt,size,props)
    local p={TextStrokeTransparency=0.55,TextStrokeColor3=Color3.new(0,0,0)}
    for k,v in pairs(props or {}) do p[k]=v end; return text(parent,txt,size,palette.Text,p)
end
-- Spaced capitals for names and titles.
local function spaced(s)
    local out={}; for _,c in utf8.codes(string.upper(s)) do out[#out+1]=utf8.char(c) end; return table.concat(out," ")
end
-- A glass button whose outline turns gold under the pointer. A gold background makes it the primary action.
local function button(parent,txt,callback,props)
    local p={Text=txt,TextSize=15,TextColor3=palette.Text,Font=Enum.Font.GothamMedium,BackgroundColor3=palette.Panel,BackgroundTransparency=0.35,
        BorderSizePixel=0,Size=UDim2.new(1,0,0,48),AutoButtonColor=false,Selectable=true,TextWrapped=true}
    for k,v in pairs(props or {}) do p[k]=v end
    if p.BackgroundColor3==palette.Gold then
        p.TextColor3=props.TextColor3 or palette.Ink; p.BackgroundTransparency=props.BackgroundTransparency or 0
    end
    local b=make("TextButton",parent,p); corner(b,3)
    local line=stroke(b,palette.Line,0.6)
    local function lit(on) line.Color=on and palette.Gold or palette.Line; line.Transparency=on and 0.05 or 0.6 end
    b.MouseEnter:Connect(function() lit(true) end); b.MouseLeave:Connect(function() lit(false) end)
    b.SelectionGained:Connect(function() lit(true) end); b.SelectionLost:Connect(function() lit(false) end)
    b.Activated:Connect(callback); return b
end
-- A small turned square: a bullet, a bar's end cap or a map marker.
local function pip(parent,size,color,hollow,props)
    local p={AnchorPoint=Vector2.new(0.5,0.5),Size=UDim2.fromOffset(size,size),Rotation=45,BackgroundColor3=color or palette.Line,BorderSizePixel=0}
    for k,v in pairs(props or {}) do p[k]=v end
    local f=make("Frame",parent,p); if hollow then f.BackgroundTransparency=1; stroke(f,color or palette.Line) end; return f
end
-- Line, gold pip, line.
local function rule(parent,width,props)
    local p={Size=UDim2.fromOffset(width,9),BackgroundTransparency=1}
    for k,v in pairs(props or {}) do p[k]=v end
    local r=make("Frame",parent,p)
    for _,side in ipairs({0,1}) do
        make("Frame",r,{AnchorPoint=Vector2.new(side,0.5),Position=UDim2.fromScale(side,0.5),Size=UDim2.new(0.5,-10,0,1),BackgroundColor3=palette.Gold,BackgroundTransparency=0.35,BorderSizePixel=0})
    end
    pip(r,6,palette.Gold,false,{Position=UDim2.fromScale(0.5,0.5)}); return r
end
-- A round number badge, as on the spell slots and the minimap's rim.
local function badge(parent,txt,props)
    local p={AnchorPoint=Vector2.new(0.5,0.5),Size=UDim2.fromOffset(22,22),BackgroundColor3=palette.Ink,BorderSizePixel=0,ZIndex=6}
    for k,v in pairs(props or {}) do p[k]=v end
    local b=make("Frame",parent,p); round(b); stroke(b,palette.Line)
    return b,text(b,txt,12,palette.Text,{Size=UDim2.fromScale(1,1),TextXAlignment=Enum.TextXAlignment.Center,Font=Enum.Font.GothamMedium,ZIndex=p.ZIndex})
end
-- An outlined key name. Returns the chip and a function that changes its key.
local function keycap(parent,txt,props)
    local p={Size=UDim2.fromOffset(20,20),BackgroundColor3=palette.Ink,BackgroundTransparency=0.35,BorderSizePixel=0}
    for k,v in pairs(props or {}) do p[k]=v end
    local cap=make("Frame",parent,p); corner(cap,3); stroke(cap,palette.Line)
    local label=text(cap,txt,12,palette.Text,{Size=UDim2.fromScale(1,1),TextXAlignment=Enum.TextXAlignment.Center,Font=Enum.Font.GothamMedium,ZIndex=cap.ZIndex})
    local function set(t) label.Text=t; cap.Size=UDim2.fromOffset(math.max(20,#t*7+10),20) end
    set(txt); return cap,set
end
-- A diamond button: an unrotated holder (it takes the clicks and carries the icon and label) around a turned
-- square with a thin double outline. Rotated frames can't clip, so the cooldown is a gradient over a second square.
local function diamond(parent,size,props)
    local span=math.ceil(size*math.sqrt(2))+10
    local p={Size=UDim2.fromOffset(span,span),BackgroundTransparency=1,Text="",AutoButtonColor=false,Selectable=true}
    for k,v in pairs(props or {}) do p[k]=v end
    local holder=make("TextButton",parent,p)
    local function square(grow,z)
        return make("Frame",holder,{AnchorPoint=Vector2.new(0.5,0.5),Position=UDim2.fromScale(0.5,0.5),Size=UDim2.fromOffset(size+grow,size+grow),Rotation=45,BorderSizePixel=0,ZIndex=z})
    end
    local ring=square(8,1); ring.BackgroundTransparency=1; local ringLine=stroke(ring,palette.Line,0.55)
    local shape=square(0,2); shape.BackgroundColor3=palette.Ink; shape.BackgroundTransparency=0.4; stroke(shape,palette.Line,0,1.5)
    local cool=square(0,3); cool.BackgroundColor3=Color3.new(0,0,0); cool.BackgroundTransparency=0.3; cool.Visible=false
    -- Turned 45° against the square's own turn, the gradient runs from the top tip down to the bottom tip.
    local gradient=make("UIGradient",cool,{Rotation=45})
    local inner=math.floor(size*0.62)
    local icon=make("Frame",holder,{AnchorPoint=Vector2.new(0.5,0.5),Position=UDim2.fromScale(0.5,0.5),Size=UDim2.fromOffset(inner,inner),BackgroundTransparency=1,ZIndex=4})
    local label=text(holder,"",math.max(12,math.floor(size*0.3)),palette.Text,{Size=UDim2.fromScale(1,1),TextXAlignment=Enum.TextXAlignment.Center,
        Font=Enum.Font.GothamBold,ZIndex=5,TextStrokeTransparency=0.35})
    local function lit(on) ringLine.Color=on and palette.Gold or palette.Line; ringLine.Transparency=on and 0.05 or 0.55 end
    holder.MouseEnter:Connect(function() lit(true) end); holder.MouseLeave:Connect(function() lit(false) end)
    holder.SelectionGained:Connect(function() lit(true) end); holder.SelectionLost:Connect(function() lit(false) end)
    return {Holder=holder,Ring=ring,Shape=shape,Cool=cool,Gradient=gradient,Icon=icon,Label=label}
end
-- Darkens the top `remaining/total` of a diamond, so it clears from the bottom up as the cooldown ends.
local function cooling(view,remaining,total)
    if remaining<=0 then view.Cool.Visible=false; return end
    local share=math.clamp(remaining/math.max(total or remaining,0.01),0,1)
    -- The gradient spans the square's side, not its tip-to-tip height: map the share of the height onto it.
    local cut=math.clamp((share-0.1464)/0.7071,0.002,0.996)
    view.Cool.Visible=true
    view.Gradient.Transparency=NumberSequence.new({NumberSequenceKeypoint.new(0,0),NumberSequenceKeypoint.new(cut,0),
        NumberSequenceKeypoint.new(cut+0.002,1),NumberSequenceKeypoint.new(1,1)})
end
local function bar(parent,position,width,height,color)
    local track=make("Frame",parent,{Position=position,Size=UDim2.fromOffset(width,height),BackgroundColor3=palette.Ink,BackgroundTransparency=0.4,BorderSizePixel=0})
    stroke(track,palette.Line,0.45)
    return track,make("Frame",track,{Size=UDim2.fromScale(1,1),BackgroundColor3=color,BorderSizePixel=0})
end
-- Shared with other controllers (the admin panel) so their menus match this one.
U.Kit={make=make,corner=corner,stroke=stroke,text=text,button=button,pip=pip,rule=rule,badge=badge,keycap=keycap,diamond=diamond,palette=palette}
function U:Init(controllers)
    self.C=controllers; self.Player=Players.LocalPlayer; self.Remotes=RS.Remotes; self.Data=nil; self.State={}; self.Cooldowns={}; self.CooldownTotals={}; self.Menu=nil
    self.Buttons={}; self.Slots={}; self.TraceConnections={}
end
function U:Action(action,a,b) self.Remotes.Action:FireServer(action,a,b) end
function U:IsOpen() return self.Panel.Visible or self.TalkGui.Enabled end
function U:Toast(message)
    self.ToastToken=(self.ToastToken or 0)+1; local token=self.ToastToken
    self.ToastLabel.Text=message; self.ToastFrame.Visible=true
    task.delay(4,function() if self.ToastToken==token then self.ToastFrame.Visible=false end end)
end
function U:Close()
    for _,connection in ipairs(self.TraceConnections) do connection:Disconnect() end; self.TraceConnections={}
    self.Panel.Visible=false; self.Backdrop.Visible=false; self.TalkGui.Enabled=false; self.HUD.Visible=true; self.Menu=nil; GuiService.SelectedObject=nil
    if self.C.InputController then self.C.InputController:CameraMode() end
end
function U:Open(title,menu)
    self:Close(); if self.C.InputController then self.C.InputController:Lance(false) end; self.Menu=menu; self.Panel.Visible=true; self.Backdrop.Visible=true
    self.PanelTitle.Text=utf8.len(title)<=26 and spaced(title) or title
    for _,child in ipairs(self.Body:GetChildren()) do if not child:IsA("UIListLayout") and not child:IsA("UIPadding") then child:Destroy() end end
    self.Body.CanvasPosition=Vector2.zero
    if self.C.InputController then self.C.InputController:CameraMode() end
    if UIS.GamepadEnabled then GuiService.SelectedObject=self.CloseButton end
end
-- `height` is the least the paragraph takes; it grows to fit its text on a narrow screen.
function U:Paragraph(content,height)
    return text(self.Body,content,16,palette.Text,{Size=UDim2.new(1,-12,0,height or 64),TextWrapped=true,TextYAlignment=Enum.TextYAlignment.Top,
        AutomaticSize=Enum.AutomaticSize.Y})
end
function U:Row(height)
    return make("Frame",self.Body,{BackgroundTransparency=1,Size=UDim2.new(1,-12,0,height or 50)})
end
-- The backing of a list row: a faint glass card with a coloured edge on the left.
function U:Card(row,accent)
    local card=make("Frame",row,{BackgroundColor3=palette.Card,BackgroundTransparency=0.95,BorderSizePixel=0,Size=UDim2.fromScale(1,1)})
    if accent then make("Frame",row,{BackgroundColor3=accent,BorderSizePixel=0,Size=UDim2.new(0,2,1,0)}) end
    return card
end
function U:SpellColor(id) return self.C.EffectsController:Color(id) end
function U:Tabs()
    local row=self:Row(38)
    local tabs={"Spells","Skills","Journal","Bag","House","Settings"}
    make("Frame",row,{AnchorPoint=Vector2.new(0,1),Position=UDim2.fromScale(0,1),Size=UDim2.new(1,0,0,1),BackgroundColor3=palette.Line,BackgroundTransparency=0.85,BorderSizePixel=0})
    for i,name in ipairs(tabs) do
        local active=self.Menu==name
        local tab=make("TextButton",row,{Text=name,TextSize=15,Font=active and Enum.Font.GothamMedium or Enum.Font.Gotham,TextColor3=active and palette.Text or palette.TextDim,
            BackgroundTransparency=1,Position=UDim2.fromScale((i-1)/#tabs,0),Size=UDim2.new(1/#tabs,0,1,-3),AutoButtonColor=false,Selectable=true})
        tab.Activated:Connect(function() self:Show(name) end)
        if active then
            make("Frame",tab,{AnchorPoint=Vector2.new(0.5,1),Position=UDim2.new(0.5,0,1,2),Size=UDim2.fromOffset(56,2),BackgroundColor3=palette.Gold,BorderSizePixel=0})
        else
            tab.MouseEnter:Connect(function() tab.TextColor3=palette.Text end); tab.MouseLeave:Connect(function() tab.TextColor3=palette.TextDim end)
        end
    end
end
function U:WandRow(index,wand,equipped)
    local row=self:Row(98)
    self:Card(row,equipped and palette.Gold or nil)
    local view=make("ViewportFrame",row,{Position=UDim2.fromOffset(8,8),Size=UDim2.fromOffset(112,82),BackgroundColor3=palette.Ink,BorderSizePixel=0,
        Ambient=Color3.fromRGB(170,170,180),LightColor=Color3.fromRGB(255,244,224),LightDirection=Vector3.new(-1,-1,-0.5)}); corner(view,3)
    local at=CFrame.Angles(0.3,0,0); local center=(at*CFrame.new(0,0,(0.65-Wands.Length(wand))/2)).Position
    WandModel.Build(wand,at,true).Parent=view
    view.CurrentCamera=make("Camera",view,{FieldOfView=40,CFrame=CFrame.lookAt(center+Vector3.new(3.3,0.6,0),center)})
    local name=Wands.Name(wand)
    local selection={Name=name,Revision=self.Data.WandRevision or 0}
    text(row,name,18,palette.Text,{Position=UDim2.fromOffset(130,4),Size=UDim2.new(1,-138,0,24),Font=Enum.Font.Garamond,TextTruncate=Enum.TextTruncate.AtEnd})
    text(row,Wands.Describe(wand),13,palette.TextDim,{Position=UDim2.fromOffset(130,28),Size=UDim2.new(1,-138,0,32),TextWrapped=true,TextYAlignment=Enum.TextYAlignment.Top})
    if equipped then
        text(row,"EQUIPPED",12,palette.Gold,{Position=UDim2.fromOffset(130,62),Size=UDim2.fromOffset(120,30),Font=Enum.Font.GothamBold})
        return
    end
    button(row,"Equip",function() self:Action("EquipWand",index,selection) end,{Position=UDim2.fromOffset(130,62),Size=UDim2.fromOffset(84,30),TextSize=13,BackgroundColor3=palette.Gold})
    local armed,discard=false,nil
    discard=button(row,"Discard",function()
        if armed then self:Action("DiscardWand",index,selection) else armed=true; discard.Text="Confirm?" end
    end,{Position=UDim2.fromOffset(222,62),Size=UDim2.fromOffset(84,30),TextSize=13})
end
function U:SkillTree()
    local d=self.Data; local available=Skills.Points(d.Level)-Skills.Spent(d.Talents)
    self:Paragraph("SKILL TREE · "..available.." point"..(available==1 and "" or "s").." to spend\nYou earn one skill point per level. Deeper skills need points in the same school. Reset once per day at the Restricted Shelf.",82)
    for _,school in ipairs(Skills.Schools) do
        local spent=Skills.Spent(d.Talents,school)
        self:Paragraph(string.upper(school).."  ·  "..spent.." point"..(spent==1 and "" or "s"),30)
        for _,id in ipairs(Skills.Order[school]) do
            local t=Skills.Talents[id]; local rank=d.Talents[id] or 0
            local row=self:Row(72)
            self:Card(row,rank>0 and palette.Gold or nil)
            text(row,t.Name.."  ·  "..rank.." / "..t.MaxRank,18,palette.Text,{Font=Enum.Font.Garamond,Position=UDim2.fromOffset(14,4),Size=UDim2.new(1,-92,0,26)})
            local note=spent<t.Requires and "  Needs "..t.Requires.." points in "..school.."." or ""
            text(row,t.Text..note,13,palette.TextDim,{Position=UDim2.fromOffset(14,30),Size=UDim2.new(1,-92,0,38),TextWrapped=true,TextYAlignment=Enum.TextYAlignment.Top})
            if Skills.CanLearn(d,id) then
                button(row,"+1",function() self:Action("Talent",id) end,{AnchorPoint=Vector2.new(1,0.5),Position=UDim2.new(1,-10,0.5,0),Size=UDim2.fromOffset(60,40),BackgroundColor3=palette.Gold})
            end
        end
    end
end
function U:Spellbook()
    self:Open("THE RAVENMOOR SPELLBOOK", "Spells"); self:Tabs()
    self:Paragraph("Select a learned spell, then choose a slot. The Ward button assigns your R / R3 slot. Scintara is always on the left mouse button: click for a spark bolt, or hold the right mouse button to pour a spark lance. Type a learned incantation in chat for +10% power.",76)
    local list={}; for _,s in pairs(Spells) do list[#list+1]=s end
    table.sort(list,function(a,b) if a.UnlockLevel==b.UnlockLevel then return a.Id<b.Id end return a.UnlockLevel<b.UnlockLevel end)
    for _,s in ipairs(list) do
        local learned=self.Data and self.Data.Spells[s.Id]
        local row=self:Row(learned and 104 or 75)
        self:Card(row,learned and self:SpellColor(s.Id) or palette.Muted)
        text(row,s.DisplayName..'  <font size="13" color="#A9A090">/ '..s.Id..'</font>',20,learned and palette.Text or palette.TextDim,
            {Font=Enum.Font.Garamond,RichText=true,Position=UDim2.fromOffset(14,4),Size=UDim2.new(1,-28,0,25)})
        local detail=learned and (s.School.." · "..num(F.ManaCost(s,self.Data)).." mana · "..num(F.Cooldown(s,self.Data)).."s · Mastery "..learned.Mastery.." ("..learned.Hits.." hits)")
            or ("Level "..s.UnlockLevel.." · "..s.Source..(not s.Implemented and " · Planned content" or ""))
        text(row,detail,13,palette.TextDim,{Position=UDim2.fromOffset(14,31),Size=UDim2.new(1,-28,0,30),TextWrapped=true})
        if learned and s.Id~="Scintara" then
            for i,slot in ipairs(SLOTS) do
                local view=diamond(row,22,{Position=UDim2.fromOffset(8+(i-1)*42,61)})
                view.Label.Text=tostring(i); view.Label.TextSize=13
                if self.Data.Loadout[slot]==s.Id then
                    view.Shape.BackgroundColor3=palette.Gold; view.Shape.BackgroundTransparency=0; view.Label.TextColor3=palette.Ink; view.Label.TextStrokeTransparency=1
                end
                view.Holder.Activated:Connect(function() self:Action("Loadout",slot,s.Id) end)
            end
            if s.School=="Ward" then
                button(row,"Ward",function() self:Action("Loadout","Ward",s.Id) end,{Size=UDim2.fromOffset(64,28),Position=UDim2.fromOffset(182,68),TextSize=13,
                    BackgroundColor3=self.Data.Loadout.Ward==s.Id and palette.Gold or palette.Panel})
            end
        end
    end
end
function U:Show(menu)
    if not self.Data then return self:Toast("Opening your student record…") end
    if menu=="Spells" then return self:Spellbook() end
    if menu=="Map" then return self:Map() end
    if menu=="Admin" then return self.C.AdminController and self.C.AdminController:Render() end
    self:Open(string.upper(menu),menu); self:Tabs()
    local d=self.Data
    if menu=="Skills" then self:SkillTree()
    elseif menu=="Journal" then
        self:Paragraph("Year "..math.min(7,math.ceil(d.Level/7)).." · Level "..d.Level.." · "..d.XP.." / "..F.XP(d.Level).." XP",38)
        local q=Quests[d.Quest]
        self:Paragraph(q and (q.Title.."\n"..q.Hint.."\nProgress: "..d.QuestProgress.." / "..q.Need) or "The first seal is safe. Your alpha story is complete!",95)
        local dailyKills=d.Daily.Day==math.floor(os.time()/86400) and d.Daily.Kills or 0
        self:Paragraph("Daily: Defeat 15 woodland enemies  ·  "..dailyKills.." / 15\nReward: 600 XP, 120 Gilders and 10 House Points.",64)
        self:Paragraph("ATTRIBUTES · "..d.Attributes.Unspent.." unspent points",34)
        for _,name in ipairs({"Power","Focus","Vitality","Agility"}) do
            button(self.Body,name.."  "..d.Attributes[name].."    + 1 point",function() self:Action("Attribute",name) end,{Size=UDim2.new(1,-12,0,44)})
        end
        self:Paragraph("DISCOVERED COMBOS",32)
        local any=false; for combo in pairs(d.Combos) do self:Paragraph("• "..combo,30); any=true end
        if not any then self:Paragraph("Try frost followed by lightning. New combinations are recorded here.",60) end
    elseif menu=="Bag" then
        local equipped=d.Wands[d.EquippedWand]
        self:Paragraph("Carried: "..d.Gilders.." Gilders    ·    Bank: "..d.BankGilders.."\nWand: "..(equipped and Wands.Name(equipped) or "Visit Oakhart"),72)
        self:Paragraph("WAND CASE · "..#d.Wands.." / "..Wands.Capacity.."\nWood and core each grant a bonus. Oakhart commissions new wands, and strong foes sometimes leave one behind.",64)
        for i,wand in ipairs(d.Wands) do self:WandRow(i,wand,i==d.EquippedWand) end
        if #d.WandsHeld>0 then self:Paragraph("Oakhart is keeping "..#d.WandsHeld.." wand"..(#d.WandsHeld==1 and "" or "s").." for you. Make room in your case, then visit the Wandery.",52) end
        self:Paragraph("BROOMS · F takes off and lands · Space climbs · Q dives\nFly anywhere but Whisperwood, whose wards pull brooms down. A hit knocks you off.",64)
        for _,id in ipairs(Brooms.Order) do
            local broom=Brooms.Brooms[id]; local riding=d.Broom==id
            local state=riding and "YOUR BROOM" or (Brooms.Unlocked(d,id) and "Ride this one" or "Level "..broom.Level)
            button(self.Body,broom.Title.."  ·  "..Brooms.Stats(id).."  ·  "..state.."\n"..broom.Note,function() self:Action("ChooseBroom",id) end,
                {Size=UDim2.new(1,-12,0,58),BackgroundColor3=riding and palette.Gold or palette.Panel})
        end
        self:Paragraph("ITEMS",30)
        local ids={}; for id,count in pairs(d.Inventory) do if count>0 then ids[#ids+1]=id end end; table.sort(ids)
        if #ids==0 then self:Paragraph("Your bag is empty. Woodland creatures drop ingredients and rare spell tomes.",75) end
        for _,id in ipairs(ids) do
            if id==DRAUGHT or id=="Frigora Tome" or id=="Somnara Tome" then
                button(self.Body,id.." ×"..d.Inventory[id].."  ·  Use"..(id==DRAUGHT and " (H)" or ""),function() self:Action("UseItem",id) end)
            else self:Paragraph(id.." ×"..d.Inventory[id].."  ·  Crafting material",38) end
        end
    elseif menu=="House" then
        self:Paragraph((d.House~="" and d.House or "Unsorted").."\nPersonal contribution: "..d.HousePoints.." House Points",66)
        self:Paragraph("THIS SERVER'S STANDINGS\nGlobal weekly Cups are planned for a later build.",60)
        for _,house in ipairs(Config.HouseOrder) do
            self:Paragraph(house.."  ·  "..tostring((self.State.HouseTotals or {})[house] or 0).." points\n"..Config.Houses[house].Perk,62)
        end
    elseif menu=="Settings" then
        button(self.Body,"Spoken casting: "..(d.Settings.SpokenCasting and "ON" or "OFF"),function() self:Action("Setting","SpokenCasting",not self.Data.Settings.SpokenCasting) end)
        button(self.Body,"Reduced visual effects: "..(d.Settings.ReducedEffects and "ON" or "OFF"),function() self:Action("Setting","ReducedEffects",not self.Data.Settings.ReducedEffects) end)
        button(self.Body,"Music: "..(d.Settings.Music~=false and "ON" or "OFF"),function() self:Action("Setting","Music",self.Data.Settings.Music==false) end)
        button(self.Body,"Open PvP: "..(d.Settings.PvP and "ON" or "OFF"),function() self:Action("Setting","PvP",not self.Data.Settings.PvP) end)
        self:Paragraph("With open PvP on, you can fight every student outside your house who has it on too, on foot or on a broom, anywhere but within "
            ..Config.Sanctuary.." studs of a Waystone. Within "..Config.PvPLockout.." seconds of combat you can't switch it off or start a duel.",62)
        self:Paragraph("PC: LMB bolt · hold RMB lance · R ward · 1–4 spells · Shift or double-tap WASD dodge\nK spellbook · B bag · M map · H Health Draught · Ctrl cursor lock · V first person\nF broom · Space climbs · Q dives · 1–9 pick a reply in conversation\nGamepad: RT bolt · hold LT lance · R3 ward · X/Y/B/RB slots · LB dodge\nD-pad Up book · Left bag · Right map · Down broom · A jump or climb · L3 dive",146)
        self:Paragraph(self.Player:GetAttribute("SessionOnly") and "STUDIO PRACTICE · Progress resets when you stop. Enable StudioSaves in Config only for a separate test experience."
            or "Progress autosaves every minute and when you leave.",75)
    elseif menu=="Bank" then
        self:Paragraph("VAULTKEEP\nCarried: "..d.Gilders.."    ·    Banked: "..d.BankGilders,65)
        for _,amount in ipairs({100,500}) do
            button(self.Body,"Deposit "..amount,function() self:Action("Bank","Deposit",amount) end)
            button(self.Body,"Withdraw "..amount,function() self:Action("Bank","Withdraw",amount) end)
        end
        button(self.Body,"Deposit all carried Gilders",function() self:Action("Bank","Deposit",math.min(self.Data.Gilders,1000000)) end)
    elseif menu=="Shop" then
        self:Paragraph("THE HOLLOWMERE APOTHECARY\nHealth Draught restores 40% of your health over 4 seconds. Shared potion cooldown: 30 seconds. Press H to drink one.",85)
        button(self.Body,"Buy Health Draught · 50 Gilders",function() self:Action("Shop","BuyHealth") end)
        button(self.Body,"Brew Health Draught · 1 Thorn Barb + 1 Spider Silk",function() self:Action("Shop","BrewHealth") end)
    elseif menu=="Library" then
        self:Paragraph("THE RESTRICTED SHELF\nTractum is taught at level 14. Your attributes and your skills can each be reset here once per UTC day.",85)
        button(self.Body,"Reset all attribute points",function() self:Action("Respec") end)
        button(self.Body,"Reset all skill points",function() self:Action("TalentReset") end)
    elseif menu=="Wandery" then
        self:Paragraph("ODRIC OAKHART'S WANDERY\nEvery wand is unique. Its wood and its core each grant a small bonus, and rarer wands grant larger ones.",85)
        local odds={}; for _,id in ipairs(Wands.RarityOrder) do if Wands.Rarities[id].Weight>0 then odds[#odds+1]=id.." "..Wands.Rarities[id].Weight.."%" end end
        self:Paragraph("Odds: "..table.concat(odds,"  ·  ").."\nWand case: "..#d.Wands.." / "..Wands.Capacity.."    ·    Carried: "..d.Gilders.." Gilders",60)
        button(self.Body,"Commission a wand · "..Wands.Price.." Gilders",function() self:Action("BuyWand") end,{BackgroundColor3=palette.Gold})
        for _,id in ipairs(Wands.NamedOrder) do
            local recipe=Wands.Named[id].Recipe
            if recipe then
                local cost={}; for item,need in pairs(recipe.Items) do cost[#cost+1]=item.." ×"..need.." ("..(d.Inventory[item] or 0).." carried)" end
                if recipe.Gilders>0 then cost[#cost+1]=recipe.Gilders.." Gilders" end
                local label=(recipe.Gilders>0 and "Commission " or "Forge ")..Wands.Named[id].Title.." · "..table.concat(cost," + ")
                if d.Level<recipe.Level then label=label.." · level "..recipe.Level end
                button(self.Body,label,function() self:Action("CommissionWand",id) end)
            end
        end
        button(self.Body,"Open your wand case",function() self:Show("Bag") end)
    elseif menu=="Duels" then
        self:Paragraph("Friendly 1v1 · no item loss · three-minute limit\nBoth students must be near Duelmaster Vey. Best of one. Stats retain your current level; these are unranked duels.",95)
        local count=0
        for _,p in ipairs(Players:GetPlayers()) do if p~=self.Player then
            count=count+1; button(self.Body,"Challenge "..p.DisplayName,function() self:Action("DuelInvite",p.UserId) end)
        end end
        if count==0 then self:Paragraph("Bring a friend, or start a two-player Studio test to try dueling.",65) end
    end
end
function U:Map()
    self:Open("RAVENMOOR & THE SURROUNDING WOODS","Map")
    self:Paragraph("North: Academy and classrooms\nEast: Training Yard and Dueling Club\nWest: Whisperwood and Vexweave's Grotto\nSouth: Hollowmere Village and the sky-ferry",115)
    local map=self:Row(240)
    make("Frame",map,{Size=UDim2.fromScale(1,1),BackgroundColor3=palette.Card,BackgroundTransparency=0.95,BorderSizePixel=0})
    local zones={{"WHISPERWOOD",0.03,0.08,0.43,0.82,Color3.fromRGB(75,104,83)},{"ACADEMY",0.5,0.05,0.46,0.28,Color3.fromRGB(94,105,128)},
        {"GROUNDS",0.5,0.38,0.46,0.22,Color3.fromRGB(130,148,104)},{"HOLLOWMERE",0.5,0.65,0.46,0.28,Color3.fromRGB(157,120,83)}}
    for _,z in ipairs(zones) do
        local region=make("Frame",map,{Position=UDim2.fromScale(z[2],z[3]),Size=UDim2.fromScale(z[4],z[5]),BackgroundColor3=z[6],BackgroundTransparency=0.25,BorderSizePixel=0})
        corner(region,3); stroke(region,palette.Line,0.6)
        text(region,spaced(z[1]),14,palette.Text,{Font=Enum.Font.Garamond,Size=UDim2.fromScale(1,1),TextXAlignment=Enum.TextXAlignment.Center,TextWrapped=true})
    end
    self:Paragraph("Waystone travel costs 25 Gilders. Attune a stone by touching its prompt. Travel starts beside any Waystone, outside combat.",70)
    for _,id in ipairs({"Hollowmere","Castle","Whisperwood"}) do
        button(self.Body,(self.Data.Waystones[id] and "Travel to " or "Undiscovered: ")..id,function() self:Action("Travel",id) end)
    end
end
-- One reply in a conversation: a pip, the reply and an optional note under it. Number keys pick replies too.
function U:TalkChoice(index,choice)
    local b=make("TextButton",self.TalkChoices,{Size=UDim2.new(1,0,0,0),AutomaticSize=Enum.AutomaticSize.Y,BackgroundColor3=palette.Card,BackgroundTransparency=1,
        BorderSizePixel=0,Text="",AutoButtonColor=false,Selectable=true,LayoutOrder=index})
    local edge=make("Frame",b,{Size=UDim2.new(0,2,1,0),BackgroundColor3=palette.Gold,BorderSizePixel=0,Visible=false})
    make("Frame",b,{AnchorPoint=Vector2.new(0,1),Position=UDim2.fromScale(0,1),Size=UDim2.new(1,0,0,1),BackgroundColor3=palette.Line,BackgroundTransparency=0.78,BorderSizePixel=0})
    local mark=pip(b,9,palette.Line,true,{Position=UDim2.new(0,20,0.5,0)}); local markLine=mark:FindFirstChildOfClass("UIStroke")
    local body=make("Frame",b,{Position=UDim2.fromOffset(40,0),Size=UDim2.new(1,-76,0,0),AutomaticSize=Enum.AutomaticSize.Y,BackgroundTransparency=1})
    make("UIListLayout",body,{SortOrder=Enum.SortOrder.LayoutOrder,Padding=UDim.new(0,2)})
    make("UIPadding",body,{PaddingTop=UDim.new(0,12),PaddingBottom=UDim.new(0,12)})
    hud(body,choice.Label,19,{Size=UDim2.new(1,0,0,0),AutomaticSize=Enum.AutomaticSize.Y,TextWrapped=true,LayoutOrder=1})
    if choice.Note then hud(body,choice.Note,14,{TextColor3=palette.TextDim,Size=UDim2.new(1,0,0,0),AutomaticSize=Enum.AutomaticSize.Y,TextWrapped=true,LayoutOrder=2}) end
    if index<=9 and not UIS.TouchEnabled then
        hud(b,tostring(index),14,{TextColor3=palette.TextDim,AnchorPoint=Vector2.new(1,0.5),Position=UDim2.new(1,-12,0.5,0),Size=UDim2.fromOffset(20,20),TextXAlignment=Enum.TextXAlignment.Right})
    end
    local function lit(on)
        b.BackgroundTransparency=on and 0.86 or 1; edge.Visible=on
        mark.BackgroundTransparency=on and 0 or 1; mark.BackgroundColor3=palette.Gold; markLine.Color=on and palette.Gold or palette.Line
    end
    b.MouseEnter:Connect(function() lit(true) end); b.MouseLeave:Connect(function() lit(false) end)
    b.SelectionGained:Connect(function() lit(true) end); b.SelectionLost:Connect(function() lit(false) end)
    b.Activated:Connect(choice.Run)
    return b
end
-- A conversation: letterbox bars, the speaker and their line along the bottom, replies stacked on the right.
-- Each choice is {Label=, Note=?, Run=function}. The HUD steps aside until it closes.
function U:Dialogue(speaker,line,choices)
    local continuing=self.TalkGui.Enabled
    self:Close(); if self.C.InputController then self.C.InputController:Lance(false) end
    self.Menu="Dialogue"; self.TalkGui.Enabled=true; self.HUD.Visible=false
    self.TalkName.Text=spaced(speaker)
    local width=TextService:GetTextSize(self.TalkName.Text,15,Enum.Font.GothamMedium,Vector2.new(4000,40)).X
    self.TalkNameLines[1].Position=UDim2.new(0.5,-width/2-14,0.5,0); self.TalkNameLines[2].Position=UDim2.new(0.5,width/2+14,0.5,0)
    self.TalkLine.Text=line; self.TalkLine.MaxVisibleGraphemes=0
    for _,child in ipairs(self.TalkChoices:GetChildren()) do if child:IsA("GuiButton") then child:Destroy() end end
    local buttons={}; for i,choice in ipairs(choices) do buttons[i]=self:TalkChoice(i,choice) end
    local ease=TweenInfo.new(0.35,Enum.EasingStyle.Quad,Enum.EasingDirection.Out)
    for _,b in ipairs(self.TalkBars) do
        if continuing then b.Size=UDim2.fromScale(1,0.08) else b.Size=UDim2.fromScale(1,0); Tween:Create(b,ease,{Size=UDim2.fromScale(1,0.08)}):Play() end
    end
    if continuing then self.TalkShade.BackgroundTransparency=0.72 else self.TalkShade.BackgroundTransparency=1; Tween:Create(self.TalkShade,ease,{BackgroundTransparency=0.72}):Play() end
    -- The line types itself out; a click, a tap or Space shows the rest at once.
    local count=utf8.len(line) or #line; local shown=0
    self.TraceConnections[#self.TraceConnections+1]=Run.RenderStepped:Connect(function(dt)
        if self.TalkLine.MaxVisibleGraphemes<0 then return end
        shown=shown+dt*math.max(60,count/0.7)
        self.TalkLine.MaxVisibleGraphemes=shown>=count and -1 or math.floor(shown)
    end)
    self.TraceConnections[#self.TraceConnections+1]=UIS.InputBegan:Connect(function(input)
        if UIS:GetFocusedTextBox() then return end
        if input.KeyCode==Enum.KeyCode.Space or input.UserInputType==Enum.UserInputType.MouseButton1 or input.UserInputType==Enum.UserInputType.Touch then
            self.TalkLine.MaxVisibleGraphemes=-1
        end
        local index=NUMBER_KEYS[input.KeyCode]
        if index and choices[index] then choices[index].Run() end
    end)
    if self.C.InputController then self.C.InputController:CameraMode() end
    if UIS.GamepadEnabled and buttons[1] then GuiService.SelectedObject=buttons[1] end
end
function U:Sorting()
    self.SortAnswers={}; self:SortingQuestion(1)
end
function U:SortingQuestion(index)
    local question=Config.SortingQuestions[index]
    local choices={}
    if question then
        for i,answer in ipairs(question.A) do choices[i]={Label=answer,Run=function() self.SortAnswers[index]=i; self:SortingQuestion(index+1) end} end
        return self:Dialogue("The Mirror of Choosing","Question "..index.." of "..#Config.SortingQuestions..". "..question.Q,choices)
    end
    local scores={0,0,0,0}; for _,answer in ipairs(self.SortAnswers) do scores[answer]=scores[answer]+1 end
    local best=1; for i=2,4 do if scores[i]>scores[best] then best=i end end
    for i,house in ipairs(Config.HouseOrder) do
        choices[i]={Label=house.." · "..Config.Houses[house].Trait,Note=Config.Houses[house].Perk,Run=function() self:Action("Sort",self.SortAnswers,house); self:Close() end}
    end
    self:Dialogue("The Mirror of Choosing","The mirror sees "..Config.HouseOrder[best].." in you. The choice is yours. Select the house you want to join.",choices)
end
function U:Lesson(info)
    self:Open("A LESSON WITH "..string.upper(info.Teacher),"Lesson")
    self:Paragraph("Learning "..info.Spell..". Trace from START to END in one stroke. Score 70% or better, then hit five targets. Mouse / touch: drag. Gamepad: hold RT + left stick; X submits.",84)
    local canvas=make("Frame",self.Body,{Size=UDim2.new(1,-12,0,220),BackgroundColor3=Color3.fromRGB(34,45,52),BorderSizePixel=0,ClipsDescendants=true,Active=true})
    corner(canvas,3); stroke(canvas,palette.Line,0.7); local ink=make("Frame",canvas,{Size=UDim2.fromScale(1,1),BackgroundTransparency=1})
    for _,point in ipairs(Gesture.Resample(info.Path,32)) do
        local dot=make("Frame",canvas,{Size=UDim2.fromOffset(7,7),AnchorPoint=Vector2.new(0.5,0.5),Position=UDim2.fromScale(point[1],point[2]),BackgroundColor3=palette.Gold,BorderSizePixel=0}); corner(dot,10)
    end
    text(canvas,"START",11,palette.White,{Position=UDim2.new(info.Path[1][1],-20,info.Path[1][2],-27),Size=UDim2.fromOffset(60,20)})
    local final=info.Path[#info.Path]; text(canvas,"END",11,palette.White,{Position=UDim2.new(final[1],-12,final[2],10),Size=UDim2.fromOffset(50,20)})
    local points,dragging,last={},false,nil; local touchInput=nil; local padPos=Vector2.new(0.5,0.5); local padAxis=Vector2.zero
    local cursor=make("Frame",canvas,{Size=UDim2.fromOffset(10,10),AnchorPoint=Vector2.new(0.5,0.5),Position=UDim2.fromScale(0.5,0.5),BackgroundColor3=palette.White,BorderSizePixel=0,Visible=UIS.GamepadEnabled}); corner(cursor)
    local function clear() points={}; last=nil; for _,child in ipairs(ink:GetChildren()) do child:Destroy() end end
    local function add(x,y)
        if x<0 or x>1 or y<0 or y>1 or #points>=160 then return end
        local p=Vector2.new(x,y); if last and (p-last).Magnitude<0.008 then return end
        points[#points+1]={x,y}; last=p
        local dot=make("Frame",ink,{Size=UDim2.fromOffset(6,6),AnchorPoint=Vector2.new(0.5,0.5),Position=UDim2.fromScale(x,y),BackgroundColor3=Color3.fromRGB(133,233,220),BorderSizePixel=0}); corner(dot,10)
    end
    local function pointer(position)
        local p=Vector2.new(position.X,position.Y)-canvas.AbsolutePosition
        add(p.X/canvas.AbsoluteSize.X,p.Y/canvas.AbsoluteSize.Y)
    end
    self.TraceConnections[#self.TraceConnections+1]=canvas.InputBegan:Connect(function(input)
        if input.UserInputType==Enum.UserInputType.MouseButton1 or input.UserInputType==Enum.UserInputType.Touch then clear(); dragging=true; touchInput=input.UserInputType==Enum.UserInputType.Touch and input or nil; pointer(input.Position) end
    end)
    self.TraceConnections[#self.TraceConnections+1]=UIS.InputChanged:Connect(function(input)
        if input.KeyCode==Enum.KeyCode.Thumbstick1 then padAxis=Vector2.new(input.Position.X,-input.Position.Y) end
        if dragging and (input.UserInputType==Enum.UserInputType.MouseMovement or input==touchInput) then pointer(input.Position) end
    end)
    self.TraceConnections[#self.TraceConnections+1]=UIS.InputBegan:Connect(function(input)
        if input.KeyCode==Enum.KeyCode.ButtonR2 then clear(); dragging=true end
        if input.KeyCode==Enum.KeyCode.ButtonX then self.Remotes.Gesture:FireServer(info.Token,points) end
    end)
    self.TraceConnections[#self.TraceConnections+1]=UIS.InputEnded:Connect(function(input)
        if input.UserInputType==Enum.UserInputType.MouseButton1 or input==touchInput or input.KeyCode==Enum.KeyCode.ButtonR2 then dragging=false end
    end)
    self.TraceConnections[#self.TraceConnections+1]=Run.RenderStepped:Connect(function(dt)
        if UIS.GamepadEnabled then padPos=Vector2.new(math.clamp(padPos.X+padAxis.X*dt*0.45,0,1),math.clamp(padPos.Y+padAxis.Y*dt*0.65,0,1)); cursor.Position=UDim2.fromScale(padPos.X,padPos.Y); if dragging then add(padPos.X,padPos.Y) end end
    end)
    button(self.Body,"Submit gesture",function() self.Remotes.Gesture:FireServer(info.Token,points) end,{BackgroundColor3=palette.Gold})
    button(self.Body,"Clear and try again",clear)
end
function U:UseDraught()
    if self:IsOpen() or not self.Data then return end
    if (self.Data.Inventory[DRAUGHT] or 0)<1 then return self:Toast("You have no Health Draughts. Buy one at the Apothecary, or brew one from a Thorn Barb and Spider Silk.") end
    if (self.Cooldowns[DRAUGHT] or 0)>os.clock() then return end
    self:Action("UseItem",DRAUGHT)
end
function U:Build()
    local playerGui=self.Player:WaitForChild("PlayerGui")
    self.Gui=make("ScreenGui",playerGui,{Name="WandboundHUD",ResetOnSpawn=false,IgnoreGuiInset=false,ZIndexBehavior=Enum.ZIndexBehavior.Sibling})
    self.Root=make("Frame",self.Gui,{Size=UDim2.fromScale(1,1),BackgroundTransparency=1})
    self.HUD=make("Frame",self.Root,{Size=UDim2.fromScale(1,1),BackgroundTransparency=1})
    self.Clusters={}
    local function cluster(name,anchor,position,size)
        local frame=make("Frame",self.HUD,{Name=name,AnchorPoint=anchor,Position=position,Size=size,BackgroundTransparency=1})
        self.Clusters[name]={Frame=frame,Scale=make("UIScale",frame)}; return frame
    end
    -- Upper left: a compass minimap that turns with the camera, then where you are.
    local map=cluster("Map",Vector2.zero,UDim2.fromOffset(24,14),UDim2.fromOffset(330,234))
    local ring=make("Frame",map,{AnchorPoint=Vector2.new(0.5,0.5),Position=UDim2.fromOffset(92,92),Size=UDim2.fromOffset(166,166),BackgroundTransparency=1}); round(ring); stroke(ring,palette.Line,0.55)
    local mini=make("Frame",map,{AnchorPoint=Vector2.new(0.5,0.5),Position=UDim2.fromOffset(92,92),Size=UDim2.fromOffset(150,150),BackgroundColor3=palette.Ink,BackgroundTransparency=0.45,BorderSizePixel=0})
    round(mini); stroke(mini,palette.Line,0,1.5)
    self.MapRadius=75; self.MapWaystones={}
    for _,id in ipairs({"Hollowmere","Castle","Whisperwood"}) do
        local w=make("Frame",mini,{AnchorPoint=Vector2.new(0.5,0.5),Size=UDim2.fromOffset(11,11),BackgroundTransparency=1,Visible=false}); round(w); stroke(w,palette.Teal,0,1.5)
        self.MapWaystones[id]=w
    end
    self.MapBoss=pip(mini,11,palette.Boss,false,{Visible=false}); stroke(self.MapBoss,palette.Ink)
    self.MapQuest=pip(mini,12,palette.Gold,false,{Visible=false}); stroke(self.MapQuest,palette.Ink)
    self.MapArrow=make("Frame",mini,{AnchorPoint=Vector2.new(0.5,0.5),Position=UDim2.fromScale(0.5,0.5),Size=UDim2.fromOffset(20,20),BackgroundTransparency=1})
    Icons.Draw("arrow",self.MapArrow,20,palette.Arrow)
    self.Cardinals={}
    for letter in pairs(CARDINALS) do
        local b,label=badge(mini,letter,{Size=UDim2.fromOffset(24,24)})
        if letter=="N" then label.TextColor3=palette.Gold end
        self.Cardinals[letter]=b
    end
    self.ZoneLabel=hud(map,"Hollowmere",22,{Font=Enum.Font.Garamond,Position=UDim2.fromOffset(0,186),Size=UDim2.new(1,0,0,26)})
    self.ZoneDetail=hud(map,"",15,{Position=UDim2.fromOffset(0,212),Size=UDim2.new(1,0,0,20)})
    -- Top centre: a boss you are close to.
    local boss=cluster("Boss",Vector2.new(0.5,0),UDim2.new(0.5,0,0,14),UDim2.fromOffset(420,64)); boss.Visible=false; self.BossFrame=boss
    self.BossLabel=hud(boss,"",18,{Font=Enum.Font.Garamond,Size=UDim2.new(1,0,0,22),TextXAlignment=Enum.TextXAlignment.Center})
    pip(boss,9,palette.Line,true,{Position=UDim2.fromOffset(24,32)}); pip(boss,9,palette.Line,true,{Position=UDim2.fromOffset(396,32)})
    local _,bossFill=bar(boss,UDim2.fromOffset(34,29),352,6,palette.Boss); self.BossFill=bossFill
    self.BossPhase=hud(boss,"",13,{Position=UDim2.fromOffset(0,40),Size=UDim2.new(1,0,0,20),TextXAlignment=Enum.TextXAlignment.Center})
    -- Upper right: the quest tracker and the next class. Other controllers may add to the end of this list.
    local quest=cluster("Quest",Vector2.new(1,0),UDim2.new(1,-24,0,14),UDim2.fromOffset(380,0)); quest.AutomaticSize=Enum.AutomaticSize.Y
    make("UIListLayout",quest,{HorizontalAlignment=Enum.HorizontalAlignment.Right,Padding=UDim.new(0,3),SortOrder=Enum.SortOrder.LayoutOrder})
    self.QuestList=quest
    self.QuestHeader=hud(quest,"CURRENT QUEST",14,{Font=Enum.Font.GothamMedium,TextColor3=palette.Gold,Size=UDim2.new(1,0,0,16),TextXAlignment=Enum.TextXAlignment.Right,LayoutOrder=1})
    local titleRow=make("Frame",quest,{Size=UDim2.new(1,0,0,30),BackgroundTransparency=1,LayoutOrder=2})
    self.QuestTitle=hud(titleRow,"",24,{Font=Enum.Font.Garamond,Size=UDim2.new(1,-22,1,0),TextXAlignment=Enum.TextXAlignment.Right,TextTruncate=Enum.TextTruncate.AtEnd})
    pip(titleRow,9,palette.Gold,false,{Position=UDim2.new(1,-5,0.5,0)})
    self.QuestHint=hud(quest,"Opening your record…",16,{Size=UDim2.new(1,0,0,0),AutomaticSize=Enum.AutomaticSize.Y,TextWrapped=true,TextXAlignment=Enum.TextXAlignment.Right,LayoutOrder=3})
    local ruleRow=make("Frame",quest,{Size=UDim2.new(1,0,0,9),BackgroundTransparency=1,LayoutOrder=4})
    make("Frame",ruleRow,{AnchorPoint=Vector2.new(1,0.5),Position=UDim2.fromScale(1,0.5),Size=UDim2.fromOffset(150,1),BackgroundColor3=palette.Line,BackgroundTransparency=0.4,BorderSizePixel=0})
    self.ClassLabel=hud(quest,"",15,{Size=UDim2.new(1,0,0,20),TextXAlignment=Enum.TextXAlignment.Right,LayoutOrder=5})
    self.Crosshair=make("Frame",self.HUD,{AnchorPoint=Vector2.new(0.5,0.5),Position=UDim2.fromScale(0.5,0.5),Size=UDim2.fromOffset(18,18),BackgroundTransparency=1})
    round(self.Crosshair); stroke(self.Crosshair,palette.Line,0.3)
    local dot=make("Frame",self.Crosshair,{AnchorPoint=Vector2.new(0.5,0.5),Position=UDim2.fromScale(0.5,0.5),Size=UDim2.fromOffset(4,4),BackgroundColor3=palette.Line,BorderSizePixel=0}); round(dot)
    -- Lower left: your bag, your broom and a Health Draught.
    local kit=cluster("Kit",Vector2.new(0,1),UDim2.new(0,24,1,-18),UDim2.fromOffset(250,98))
    local function tool(name,icon,x,key,callback)
        local view=diamond(kit,46,{Position=UDim2.fromOffset(x,22)})
        view.Glyph=Icons.Draw(icon,view.Icon,26); view.Holder.Activated:Connect(callback)
        view.Cap,view.SetKey=keycap(kit,key,{Position=UDim2.fromOffset(x+50,6),ZIndex=6})
        self.Slots[name]=view; self.Buttons[name]=view.Holder; return view
    end
    tool("Bag","bag",0,"B",function() if self.C.InputController then self.C.InputController:ToggleMenu("Bag") end end)
    tool("Broom","broom",84,"F",function() if self.C.InputController then self.C.InputController:UseSlot("Broom") end end)
    local draught=tool("Draught","flask",168,"H",function() self:UseDraught() end)
    draught.Badge,draught.Count=badge(kit,"0",{Position=UDim2.fromOffset(230,84)})
    -- Lower right: key hints, four spell diamonds, then your bars and Scintara.
    local spells=cluster("Spells",Vector2.new(1,1),UDim2.new(1,-24,1,-16),UDim2.fromOffset(430,196))
    self.HintRow=make("Frame",spells,{Size=UDim2.new(1,-12,0,24),BackgroundTransparency=1})
    make("UIListLayout",self.HintRow,{FillDirection=Enum.FillDirection.Horizontal,HorizontalAlignment=Enum.HorizontalAlignment.Right,
        VerticalAlignment=Enum.VerticalAlignment.Center,Padding=UDim.new(0,16),SortOrder=Enum.SortOrder.LayoutOrder})
    self.Hints={}
    local function hint(name,icon,key,order,callback)
        local item=make("TextButton",self.HintRow,{Size=UDim2.fromScale(0,1),AutomaticSize=Enum.AutomaticSize.X,BackgroundTransparency=1,Text="",AutoButtonColor=false,LayoutOrder=order})
        make("UIListLayout",item,{FillDirection=Enum.FillDirection.Horizontal,VerticalAlignment=Enum.VerticalAlignment.Center,Padding=UDim.new(0,6),SortOrder=Enum.SortOrder.LayoutOrder})
        local glyph=make("Frame",item,{Size=UDim2.fromOffset(20,20),BackgroundTransparency=1,LayoutOrder=1})
        local view={Item=item,Glyph=glyph,Scale=make("UIScale",glyph),Icon=Icons.Draw(icon,glyph,18)}
        view.Cap,view.SetKey=keycap(item,key,{LayoutOrder=2})
        view.Timer=hud(item,"",13,{Size=UDim2.fromOffset(0,20),AutomaticSize=Enum.AutomaticSize.X,LayoutOrder=3,Visible=false})
        item.Activated:Connect(callback); self.Hints[name]=view
    end
    hint("Ward","shield","R",1,function() if self.C.InputController then self.C.InputController:UseSlot("Ward") end end)
    hint("Dodge","dodge","Shift",2,function() if self.C.InputController then self.C.InputController:UseSlot("Dodge") end end)
    hint("Book","book","K",3,function() if self.C.InputController then self.C.InputController:ToggleMenu("Spells") end end)
    for i,slot in ipairs(SLOTS) do
        local view=diamond(spells,58,{Position=UDim2.fromOffset(66+(i-1)*86,30)})
        view.Badge,view.Number=badge(spells,tostring(i),{Position=UDim2.fromOffset(87+(i-1)*86,51)})
        view.Holder.Activated:Connect(function()
            local id=self.Data and self.Data.Loadout[slot]
            if not id or id=="" then return self:Show("Spells") end
            if self.C.InputController then self.C.InputController:UseSlot(slot) end
        end)
        self.Slots[slot]=view; self.Buttons[slot]=view.Holder
    end
    self.Bars={}
    local function stat(name,x,y,w,h,color)
        local track,fill=bar(spells,UDim2.fromOffset(x,y),w,h,color); self.Bars[name]={Track=track,Fill=fill,Shown=-1}; return track
    end
    stat("MANA",50,140,140,6,palette.Mana); stat("STAMINA",198,140,140,6,palette.Stamina)
    local hpTrack=stat("HP",50,155,288,8,palette.HP)
    self.ShieldFill=make("Frame",hpTrack,{Size=UDim2.fromScale(0,1),BackgroundColor3=palette.Line,BorderSizePixel=0})
    pip(spells,9,palette.Line,true,{Position=UDim2.fromOffset(40,159)}); pip(spells,9,palette.Line,true,{Position=UDim2.fromOffset(348,159)})
    local basic=diamond(spells,34,{Position=UDim2.fromOffset(371,130)}); Icons.Draw("spark",basic.Icon,20)
    basic.Holder.Activated:Connect(function() if self.C.InputController then self.C.InputController:UseSlot("Basic") end end)
    self.Slots.Basic=basic; self.Buttons.Basic=basic.Holder
    -- Touch screens have no right mouse button: this diamond pours the spark lance while it is held.
    local lance=diamond(spells,46,{Position=UDim2.fromOffset(354,36),Visible=false}); Icons.Draw("lance",lance.Icon,26)
    lance.Holder.InputBegan:Connect(function(input)
        if input.UserInputType==Enum.UserInputType.Touch or input.UserInputType==Enum.UserInputType.MouseButton1 then self.C.InputController:Lance(true) end
    end)
    lance.Holder.InputEnded:Connect(function(input)
        if input.UserInputType==Enum.UserInputType.Touch or input.UserInputType==Enum.UserInputType.MouseButton1 then self.C.InputController:Lance(false) end
    end)
    self.Slots.Lance=lance; self.Buttons.Lance=lance.Holder
    -- Notices: a glass strip under the zone name. It stays up while you talk, so it lives outside the HUD.
    self.ToastFrame=make("Frame",self.Root,{Position=UDim2.fromOffset(24,254),Size=UDim2.fromOffset(360,0),AutomaticSize=Enum.AutomaticSize.Y,BackgroundColor3=palette.Ink,
        BackgroundTransparency=0.45,BorderSizePixel=0,Visible=false,ZIndex=7})
    self.ToastScale=make("UIScale",self.ToastFrame)
    for _,side in ipairs({0,1}) do
        make("Frame",self.ToastFrame,{AnchorPoint=Vector2.new(0,side),Position=UDim2.fromScale(0,side),Size=UDim2.new(1,0,0,1),BackgroundColor3=palette.Line,BackgroundTransparency=0.45,BorderSizePixel=0})
    end
    pip(self.ToastFrame,9,palette.Gold,false,{Position=UDim2.new(0,18,0.5,0)})
    self.ToastLabel=hud(self.ToastFrame,"",16,{Position=UDim2.fromOffset(34,0),Size=UDim2.new(1,-46,0,0),AutomaticSize=Enum.AutomaticSize.Y,TextWrapped=true})
    make("UIPadding",self.ToastLabel,{PaddingTop=UDim.new(0,9),PaddingBottom=UDim.new(0,9)})
    -- Menus and popups: dark glass with a gold double line, over a dimmed screen.
    self.Backdrop=make("TextButton",self.Root,{Size=UDim2.fromScale(1,1),BackgroundColor3=palette.Ink,BackgroundTransparency=0.45,BorderSizePixel=0,Text="",
        AutoButtonColor=false,Selectable=false,Visible=false,ZIndex=19})
    self.Panel=make("Frame",self.Root,{AnchorPoint=Vector2.new(0.5,0.5),Position=UDim2.fromScale(0.5,0.5),Size=UDim2.fromOffset(760,570),BackgroundColor3=palette.Ink,
        BorderSizePixel=0,Visible=false,ZIndex=20}); corner(self.Panel,2); stroke(self.Panel,palette.Gold,0.15)
    local inset=make("Frame",self.Panel,{Position=UDim2.fromOffset(6,6),Size=UDim2.new(1,-12,1,-12),BackgroundTransparency=1}); stroke(inset,palette.Gold,0.72)
    for _,at in ipairs({{0,0},{1,0},{0,1},{1,1}}) do pip(self.Panel,10,palette.Gold,false,{Position=UDim2.fromScale(at[1],at[2])}) end
    self.PanelTitle=text(self.Panel,"",24,palette.Text,{Font=Enum.Font.Garamond,AnchorPoint=Vector2.new(0.5,0),Position=UDim2.new(0.5,0,0,14),Size=UDim2.new(1,-130,0,34),
        TextXAlignment=Enum.TextXAlignment.Center,TextScaled=true})
    make("UITextSizeConstraint",self.PanelTitle,{MaxTextSize=24})
    rule(self.Panel,280,{AnchorPoint=Vector2.new(0.5,0),Position=UDim2.new(0.5,0,0,52)})
    local close=diamond(self.Panel,24,{AnchorPoint=Vector2.new(1,0),Position=UDim2.new(1,-10,0,8)}); close.Label.Text="×"; close.Label.TextSize=20; close.Label.Font=Enum.Font.Gotham
    close.Holder.Activated:Connect(function() self:Close() end); self.CloseButton=close.Holder
    self.Body=make("ScrollingFrame",self.Panel,{Position=UDim2.fromOffset(22,72),Size=UDim2.new(1,-38,1,-90),BackgroundTransparency=1,BorderSizePixel=0,ScrollBarThickness=4,
        ScrollBarImageColor3=palette.Gold,CanvasSize=UDim2.new(),AutomaticCanvasSize=Enum.AutomaticSize.Y})
    self.BodyList=make("UIListLayout",self.Body,{Padding=UDim.new(0,9),SortOrder=Enum.SortOrder.LayoutOrder})
    self.BodyList:GetPropertyChangedSignal("AbsoluteContentSize"):Connect(function() self:FitPanel() end)
    -- Conversations get a screen of their own, over the top bar too, for the letterbox.
    self.TalkGui=make("ScreenGui",playerGui,{Name="WandboundTalk",ResetOnSpawn=false,IgnoreGuiInset=true,DisplayOrder=5,Enabled=false,ZIndexBehavior=Enum.ZIndexBehavior.Sibling})
    self.TalkShade=make("Frame",self.TalkGui,{Size=UDim2.fromScale(1,1),BackgroundColor3=Color3.new(0,0,0),BackgroundTransparency=1,BorderSizePixel=0})
    self.TalkBars={}
    for i,side in ipairs({0,1}) do
        self.TalkBars[i]=make("Frame",self.TalkGui,{AnchorPoint=Vector2.new(0,side),Position=UDim2.fromScale(0,side),Size=UDim2.fromScale(1,0),BackgroundColor3=Color3.fromRGB(8,9,11),BorderSizePixel=0})
    end
    local caption=make("Frame",self.TalkGui,{AnchorPoint=Vector2.new(0.5,1),Position=UDim2.new(0.5,0,0.92,-16),Size=UDim2.new(0.62,0,0,0),AutomaticSize=Enum.AutomaticSize.Y,BackgroundTransparency=1})
    make("UIListLayout",caption,{HorizontalAlignment=Enum.HorizontalAlignment.Center,Padding=UDim.new(0,8),SortOrder=Enum.SortOrder.LayoutOrder})
    local nameRow=make("Frame",caption,{Size=UDim2.new(1,0,0,20),BackgroundTransparency=1,LayoutOrder=1})
    self.TalkName=hud(nameRow,"",15,{Font=Enum.Font.GothamMedium,TextColor3=palette.Gold,Size=UDim2.fromScale(1,1),TextXAlignment=Enum.TextXAlignment.Center})
    self.TalkNameLines={}
    for i,side in ipairs({1,0}) do
        self.TalkNameLines[i]=make("Frame",nameRow,{AnchorPoint=Vector2.new(side,0.5),Position=UDim2.fromScale(0.5,0.5),Size=UDim2.fromOffset(70,1),BackgroundColor3=palette.Gold,BackgroundTransparency=0.25,BorderSizePixel=0})
    end
    self.TalkLine=hud(caption,"",21,{Size=UDim2.new(1,0,0,0),AutomaticSize=Enum.AutomaticSize.Y,TextWrapped=true,TextXAlignment=Enum.TextXAlignment.Center,LayoutOrder=2,TextStrokeTransparency=0.45})
    self.TalkChoices=make("Frame",self.TalkGui,{AnchorPoint=Vector2.new(1,0.5),Position=UDim2.new(1,-64,0.45,0),Size=UDim2.fromOffset(420,0),AutomaticSize=Enum.AutomaticSize.Y,BackgroundTransparency=1})
    make("UIListLayout",self.TalkChoices,{SortOrder=Enum.SortOrder.LayoutOrder})
    self.TalkScales={make("UIScale",caption),make("UIScale",self.TalkChoices)}
end
function U:Layout()
    local size=self.Root.AbsoluteSize; local touch=UIS.TouchEnabled; local small=math.min(size.X,size.Y)<=500
    -- Below about three quarters the smallest HUD text stops being readable.
    local scale=math.clamp(size.Y/1000,0.75,1)
    for _,c in pairs(self.Clusters) do c.Scale.Scale=scale end
    -- Thumbs need bigger targets, clear of Roblox's jump button and thumbstick.
    if touch then
        local reach=math.max(scale,small and 0.8 or 0.95)
        self.Clusters.Spells.Scale.Scale=reach; self.Clusters.Kit.Scale.Scale=reach
    end
    self.Clusters.Spells.Frame.Position=UDim2.new(1,-20,1,touch and (small and -92 or -184) or -16)
    self.Clusters.Kit.Frame.Position=touch and UDim2.new(0,small and 130 or 200,1,-16) or UDim2.new(0,24,1,-18)
    for i,slot in ipairs(SLOTS) do
        local x=(touch and 0 or 66)+(i-1)*86
        self.Slots[slot].Holder.Position=UDim2.fromOffset(x,30); self.Slots[slot].Badge.Position=UDim2.fromOffset(x+21,51)
    end
    self.Slots.Lance.Holder.Visible=touch
    self.HintRow.Size=UDim2.new(1,-12,0,touch and 40 or 24); self.HintRow.Position=UDim2.fromOffset(0,touch and -18 or 0)
    for _,view in pairs(self.Hints) do view.Scale.Scale=touch and 1.7 or 1; view.Cap.Visible=not touch end
    self.ToastScale.Scale=scale; self.ToastFrame.Position=UDim2.fromOffset(24,14+240*scale)
    for _,s in ipairs(self.TalkScales) do s.Scale=math.clamp(size.Y/1000,0.75,1) end
    self.PanelRoom=Vector2.new(math.min(800,size.X-26),math.min(600,size.Y-26)); self:FitPanel()
end
-- The panel is as tall as its content, up to the room the screen has.
function U:FitPanel()
    local room=self.PanelRoom or Vector2.new(800,600)
    self.Panel.Size=UDim2.fromOffset(room.X,math.min(room.Y,math.max(220,self.BodyList.AbsoluteContentSize.Y+100)))
end
-- Moves a bar's fill (and, for health, the shield past it) with a short tween.
function U:SetBar(bar,share)
    share=math.clamp(share,0,1)
    if math.abs(share-bar.Shown)<0.002 then return end
    bar.Shown=share; Tween:Create(bar.Fill,TweenInfo.new(0.15),{Size=UDim2.fromScale(share,1)}):Play()
end
function U:UpdateHUD()
    local d=self.Data; local s=self.State
    self.HUD.Visible=not self.TalkGui.Enabled
    local pad=tostring(UIS:GetLastInputType()):find("Gamepad")~=nil
    local showKeys=pad or not UIS.TouchEnabled
    if d then
        local q=Quests[d.Quest]
        self.QuestHeader.Text=q and "CURRENT QUEST" or "THE STORY SO FAR"
        self.QuestTitle.Text=q and q.Title or "The first seal is safe"
        self.QuestHint.Text=q and (q.Hint.."  ·  "..d.QuestProgress.." / "..q.Need) or "Explore, master your spells, and duel with friends."
        local root=self.Player.Character and self.Player.Character:FindFirstChild("HumanoidRootPart")
        local sanctuary=d.Settings.PvP and root and F.Sanctuary(root.Position)
        self.ZoneLabel.Text=self.Player:GetAttribute("Zone") or "Hollowmere"
        self.ZoneDetail.Text="Level "..d.Level.."  ·  "..d.Gilders.." Gilders"..(sanctuary and "  ·  Sanctuary" or "")
        for i,slot in ipairs(SLOTS) do
            local view=self.Slots[slot]; local id=d.Loadout[slot]; if id=="" then id=nil end
            if view.Shown~=(id or "") then
                view.Shown=id or ""; local spell=id and Spells[id]
                for _,child in ipairs(view.Icon:GetChildren()) do child:Destroy() end
                Icons.Draw(spell and Icons.ForSpell(spell) or "plus",view.Icon,spell and 30 or 20,spell and palette.Line or palette.TextDim,spell and spell.DisplayName:sub(1,1))
                view.Shape.BackgroundColor3=spell and self:SpellColor(id):Lerp(Color3.new(),0.3) or palette.Ink
                view.Shape.BackgroundTransparency=spell and 0.05 or 0.55
            end
            view.Number.Text=pad and PAD[slot] or tostring(i)
        end
        local flying=self.Player:GetAttribute("Broom")~=nil
        local broom=self.Slots.Broom
        if broom.Flying~=flying then
            broom.Flying=flying
            broom.Shape.BackgroundColor3=flying and palette.Gold or palette.Ink; broom.Shape.BackgroundTransparency=flying and 0.05 or 0.4
            Icons.Tint(broom.Glyph,flying and palette.Ink or palette.Line)
        end
        broom.SetKey((pad and "D-Down" or "F")..(flying and "  Land" or ""))
        local draught=self.Slots.Draught; local count=d.Inventory[DRAUGHT] or 0
        draught.Count.Text=tostring(count); draught.Shape.BackgroundTransparency=count>0 and 0.4 or 0.7
        Icons.Tint(draught.Glyph,count>0 and palette.Line or palette.Muted)
        self.Slots.Bag.SetKey(pad and "D-Left" or "B"); draught.Cap.Visible=showKeys and not pad
        self.Slots.Bag.Cap.Visible=showKeys; broom.Cap.Visible=showKeys
        self.Hints.Ward.SetKey(pad and "R3" or "R"); self.Hints.Dodge.SetKey(pad and "LB" or "Shift"); self.Hints.Book.SetKey(pad and "D-Up" or "K")
        local lancing=self.C.InputController and self.C.InputController.Lancing
        self.Slots.Basic.Shape.BackgroundColor3=lancing and palette.Gold or palette.Ink
    end
    local hp,maxHp=s.HP or 0,math.max(1,s.MaxHP or 110)
    self:SetBar(self.Bars.HP,hp/maxHp); self:SetBar(self.Bars.MANA,(s.Mana or 0)/math.max(1,s.MaxMana or 102)); self:SetBar(self.Bars.STAMINA,(s.Stamina or 0)/100)
    local share=math.clamp(hp/maxHp,0,1)
    self.ShieldFill.Position=UDim2.fromScale(share,0); self.ShieldFill.Size=UDim2.fromScale(math.min((s.Shield or 0)/maxHp,1-share),1)
    if s.Class then local t=s.Class.Seconds; self.ClassLabel.Text="Next class · "..s.Class.Subject.." in "..string.format("%d:%02d",math.floor(t/60),t%60) end
    local root=self.Player.Character and self.Player.Character:FindFirstChild("HumanoidRootPart")
    local boss=nil; local runtime=workspace:FindFirstChild("Runtime"); local folder=runtime and runtime:FindFirstChild("Monsters")
    if root and folder then
        for _,model in ipairs(folder:GetChildren()) do
            local r=model.PrimaryPart; if r and model:GetAttribute("Rank")=="Boss" and (r.Position-root.Position).Magnitude<130 then boss=model; break end
        end
    end
    self.BossRoot=boss and boss.PrimaryPart
    self.BossFrame.Visible=boss~=nil and not self:IsOpen()
    if boss then
        local hum=boss:FindFirstChildOfClass("Humanoid")
        if hum then
            self.BossLabel.Text=spaced(boss.Name); self.BossPhase.Text="Phase "..tostring(boss:GetAttribute("Phase") or 1)
            self.BossFill.Size=UDim2.fromScale(math.clamp(hum.Health/hum.MaxHealth,0,1),1)
        end
    end
    self.Crosshair.Visible=not self:IsOpen() and (not self.C.InputController or self.C.InputController.Locked)
end
-- Every frame: the minimap turns with the camera (your arrow points the way you face), and cooldowns drain.
-- The academy interior stands 1,500 studs above the grounds (blender/install_worldplan.lua). A quest point on the
-- other side of its door is shown at the door.
function U:Guide(point)
    local root=self.Player.Character and self.Player.Character:FindFirstChild("HumanoidRootPart")
    if not point or not root then return point end
    local inside=root.Position.Y>1000
    if (point[2]>1000)~=inside then return Points[inside and "AcademyExit" or "AcademyEntrance"] end
    return point
end
function U:UpdateFrame()
    if not self.HUD.Visible then return end
    local camera=workspace.CurrentCamera; local root=self.Player.Character and self.Player.Character:FindFirstChild("HumanoidRootPart")
    if camera and root then
        local look=camera.CFrame.LookVector; local f=Vector2.new(look.X,look.Z)
        if f.Magnitude<0.01 then local up=camera.CFrame.UpVector; f=Vector2.new(up.X,up.Z) end
        f=f.Unit; local r=Vector2.new(-f.Y,f.X); local radius=self.MapRadius; local pos=root.Position
        local function place(gui,dx,dz,pin)
            local d=Vector2.new(dx,dz); local p=Vector2.new(d:Dot(r),-d:Dot(f))*(radius/MAP_RANGE)
            if p.Magnitude>radius-8 then
                if not pin then gui.Visible=false; return end
                p=p.Unit*(radius-8)
            end
            gui.Visible=true; gui.Position=UDim2.new(0.5,p.X,0.5,p.Y)
        end
        for letter,way in pairs(CARDINALS) do self.Cardinals[letter].Position=UDim2.new(0.5,way:Dot(r)*radius,0.5,-way:Dot(f)*radius) end
        local d=self.Data; local q=d and Quests[d.Quest]; local point=q and self:Guide(Points[q.Anchor])
        if point then place(self.MapQuest,point[1]-pos.X,point[3]-pos.Z,true) else self.MapQuest.Visible=false end
        for id,ring in pairs(self.MapWaystones) do
            local at=Points["Waystone_"..id]
            if d and d.Waystones[id] and at then place(ring,at[1]-pos.X,at[3]-pos.Z,false) else ring.Visible=false end
        end
        local boss=self.BossRoot
        if boss and boss.Parent then place(self.MapBoss,boss.Position.X-pos.X,boss.Position.Z-pos.Z,true) else self.MapBoss.Visible=false end
        local facing=root.CFrame.LookVector; local c=Vector2.new(facing.X,facing.Z)
        if c.Magnitude>0.01 then c=c.Unit; self.MapArrow.Rotation=math.deg(math.atan2(c:Dot(r),c:Dot(f))) end
    end
    local d=self.Data; if not d then return end
    local now=os.clock()
    -- While the seconds count down, they take the icon's place.
    local function show(view,id,quiet)
        local remaining=math.max(0,(id and self.Cooldowns[id] or 0)-now)
        cooling(view,remaining,id and self.CooldownTotals[id])
        local counting=remaining>0 and not quiet
        view.Icon.Visible=not counting
        view.Label.Text=counting and (remaining<10 and string.format("%.1f",remaining) or tostring(math.ceil(remaining))) or ""
    end
    for _,slot in ipairs(SLOTS) do local id=d.Loadout[slot]; show(self.Slots[slot],id~="" and id or nil) end
    show(self.Slots.Basic,"Scintara",true); show(self.Slots.Lance,"ScintaraLance",true); show(self.Slots.Draught,DRAUGHT)
    local ward=d.Loadout.Ward; local left=math.max(0,(ward and ward~="" and self.Cooldowns[ward] or 0)-now)
    self.Hints.Ward.Timer.Visible=left>0; if left>0 then self.Hints.Ward.Timer.Text=string.format("%.1f",left) end
end
function U:Welcome()
    self:Open("WANDBOUND · RAVENMOOR ACADEMY","Welcome")
    self:Paragraph("A lantern flickers in the tower.\nSomething beneath Ravenmoor is waking.",50)
    self:Paragraph("Begin at Oakhart's Wandery in Hollowmere. Receive your wand, choose a house, attend your first class, and follow Tobb into Whisperwood.",50)
    self:Paragraph("Approach a named character and use the interaction prompt. Follow the gold marker on your minimap and the quest in the upper right. Red ground circles warn you where enemies will strike.",50)
    self:Paragraph("LMB casts Spark Bolt · hold RMB for its lance · R raises your ward · Shift or double-tap WASD dodges · F flies your broom · H drinks a Health Draught\nUse the on-screen diamonds on touch devices. K opens your spellbook.",70)
    button(self.Body,"BEGIN YOUR FIRST YEAR",function() self:Close() end,{BackgroundColor3=palette.Gold,Size=UDim2.new(1,-12,0,56)})
end
function U:Start()
    self:Build(); self:Layout(); self.Root:GetPropertyChangedSignal("AbsoluteSize"):Connect(function() self:Layout() end)
    self.Remotes.Profile.OnClientEvent:Connect(function(data)
        -- One fewer draught means you drank one: show the server's shared 30-second potion cooldown.
        local before=self.Data and self.Data.Inventory[DRAUGHT] or 0
        if (data.Inventory[DRAUGHT] or 0)<before then self.Cooldowns[DRAUGHT]=os.clock()+30; self.CooldownTotals[DRAUGHT]=30 end
        self.Data=data
        if self.Menu and ({Spells=true,Skills=true,Journal=true,Bag=true,Settings=true,Bank=true,Shop=true,House=true,Library=true,Wandery=true,Admin=true})[self.Menu] then
            -- Re-render in place: keep the scroll position once the new layout has been measured.
            local menu=self.Menu; local scroll=self.Body.CanvasPosition; self:Show(menu)
            task.spawn(function() Run.RenderStepped:Wait(); if self.Menu==menu then self.Body.CanvasPosition=scroll end end)
        end
    end)
    self.Remotes.State.OnClientEvent:Connect(function(state)
        local now=os.clock(); local old=self.Cooldowns
        self.State=state; self.Cooldowns={[DRAUGHT]=old[DRAUGHT]}
        for id,left in pairs(state.Cooldowns) do
            if (old[id] or 0)<=now or left>(self.CooldownTotals[id] or 0) then self.CooldownTotals[id]=left end
            self.Cooldowns[id]=now+left
        end
    end)
    self.Remotes.CastReply.OnClientEvent:Connect(function(id,ok,value)
        if ok then self.Cooldowns[id]=os.clock()+value; self.CooldownTotals[id]=value elseif value~="Cooling down" then self:Toast(value) end
    end)
    self.Remotes.UI.OnClientEvent:Connect(function(kind,info)
        if kind=="Toast" then self:Toast(info)
        elseif kind=="Dialogue" then
            local choices={}
            for i,choice in ipairs(info.Choices) do
                choices[i]={Label=choice.Label,Run=function()
                    self:Close(); if self.C.InputController then self.C.InputController:PausePrompts() end
                    self:Action("Interact",info.Anchor,choice.Id)
                end}
            end
            choices[#choices+1]={Label="Goodbye",Run=function() self:Close() end}
            self:Dialogue(info.Name,info.Text,choices)
        elseif kind=="Sorting" then self:Sorting()
        elseif kind=="Lesson" then self:Lesson(info)
        elseif kind=="GestureResult" then if info.Pass then self:Close() else self:Toast("Rune accuracy: "..info.Score.."%. Clear the canvas and try again.") end
        elseif kind=="DuelInvite" then
            self:Dialogue(info.Name,info.Name.." challenges you to a friendly duel. No items are lost.",{
                {Label="Accept duel",Run=function() self:Action("DuelRespond",true); self:Close() end},
                {Label="Decline",Run=function() self:Action("DuelRespond",false); self:Close() end}})
        elseif kind=="DuelStart" then self:Close(); self:Toast("Bow. Ready in "..info.." seconds…")
        elseif kind=="Knockout" then
            self:Close(); self:Toast((info.By and "Knocked out by "..info.By or "Knocked out").." · returning to your Waystone in "..info.Seconds.." seconds. Nothing lost.")
        elseif kind=="Lift" then self.C.EffectsController:Lift()
        else self:Show(kind) end
    end)
    self:Welcome()
    task.spawn(function()
        for _=1,10 do if self.Data then break end; self:Action("Ready"); task.wait(1) end
    end)
    local elapsed=0
    Run.RenderStepped:Connect(function(dt)
        self:UpdateFrame()
        elapsed=elapsed+dt; if elapsed>0.1 then elapsed=0; self:UpdateHUD() end
    end)
end
return U
