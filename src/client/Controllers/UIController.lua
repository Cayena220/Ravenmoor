local Players=game:GetService("Players")
local RS=game:GetService("ReplicatedStorage")
local UIS=game:GetService("UserInputService")
local GuiService=game:GetService("GuiService")
local Run=game:GetService("RunService")
local Config=require(RS.Shared.Config)
local Spells=require(RS.Shared.SpellData)
local Quests=require(RS.Shared.QuestData)
local F=require(RS.Shared.Formulas)
local Gesture=require(RS.Shared.Gesture)
local Wands=require(RS.Shared.WandData)
local WandModel=require(RS.Shared.WandModel)
local Skills=require(RS.Shared.SkillData)
local Brooms=require(RS.Shared.BroomData)
local U={}
local function num(x) return string.format("%g",math.floor(x*10+0.5)/10) end
local palette={Ink=Color3.fromRGB(23,29,36),Panel=Color3.fromRGB(242,232,207),Gold=Color3.fromRGB(183,145,79),
    Muted=Color3.fromRGB(161,169,177),White=Color3.fromRGB(246,240,223),Line=Color3.fromRGB(78,81,85)}
local function make(class,parent,props)
    local inst=Instance.new(class); for k,v in pairs(props or {}) do inst[k]=v end; inst.Parent=parent; return inst
end
local function corner(frame,radius) make("UICorner",frame,{CornerRadius=UDim.new(0,radius or 8)}) end
local function stroke(frame,color,transparency) make("UIStroke",frame,{Color=color or palette.Gold,Thickness=1,Transparency=transparency or 0}) end
local function text(parent,txt,size,color,props)
    local p={Text=txt,TextSize=size or 16,TextColor3=color or palette.White,Font=Enum.Font.Gotham,
        TextXAlignment=Enum.TextXAlignment.Left,TextYAlignment=Enum.TextYAlignment.Center,BackgroundTransparency=1,Size=UDim2.new(1,0,0,30)}
    for k,v in pairs(props or {}) do p[k]=v end; return make("TextLabel",parent,p)
end
local function button(parent,txt,callback,props)
    local p={Text=txt,TextSize=15,TextColor3=palette.Ink,Font=Enum.Font.GothamMedium,BackgroundColor3=palette.Panel,
        BorderSizePixel=0,Size=UDim2.new(1,0,0,48),AutoButtonColor=true,Selectable=true,TextWrapped=true}
    for k,v in pairs(props or {}) do p[k]=v end
    local b=make("TextButton",parent,p); corner(b,7); b.Activated:Connect(callback); return b
end
-- Shared with other controllers (the admin panel) so their menus match this one.
U.Kit={make=make,corner=corner,stroke=stroke,text=text,button=button,palette=palette}
function U:Init(controllers)
    self.C=controllers; self.Player=Players.LocalPlayer; self.Remotes=RS.Remotes; self.Data=nil; self.State={}; self.Cooldowns={}; self.Menu=nil
    self.SpellSlots={"Basic","Lance","Slot1","Slot2","Slot3","Slot4","Ward","Dodge","Broom"}; self.Buttons={}; self.TraceConnections={}
end
function U:Action(action,a,b) self.Remotes.Action:FireServer(action,a,b) end
function U:IsOpen() return self.Panel.Visible end
function U:Toast(message)
    self.ToastToken=(self.ToastToken or 0)+1; local token=self.ToastToken
    self.ToastLabel.Text=message; self.ToastFrame.Visible=true
    task.delay(4,function() if self.ToastToken==token then self.ToastFrame.Visible=false end end)
end
function U:Close()
    for _,connection in ipairs(self.TraceConnections) do connection:Disconnect() end; self.TraceConnections={}
    self.Panel.Visible=false; self.Menu=nil; GuiService.SelectedObject=nil
    if self.C.InputController then self.C.InputController:CameraMode() end
end
function U:Open(title,menu)
    self:Close(); if self.C.InputController then self.C.InputController:Lance(false) end; self.Menu=menu; self.Panel.Visible=true; self.PanelTitle.Text=title
    for _,child in ipairs(self.Body:GetChildren()) do if not child:IsA("UIListLayout") and not child:IsA("UIPadding") then child:Destroy() end end
    self.Body.CanvasPosition=Vector2.zero
    if self.C.InputController then self.C.InputController:CameraMode() end
    if UIS.GamepadEnabled then GuiService.SelectedObject=self.CloseButton end
end
function U:Paragraph(content,height)
    return text(self.Body,content,16,palette.Ink,{Size=UDim2.new(1,-12,0,height or 64),TextWrapped=true,TextYAlignment=Enum.TextYAlignment.Top})
end
function U:Row(height)
    return make("Frame",self.Body,{BackgroundTransparency=1,Size=UDim2.new(1,-12,0,height or 50)})
end
function U:Tabs()
    local row=self:Row(42)
    local tabs={"Spells","Skills","Journal","Bag","House","Settings"}
    for i,name in ipairs(tabs) do button(row,name,function() self:Show(name) end,{Position=UDim2.new((i-1)/#tabs,3,0,0),Size=UDim2.new(1/#tabs,-6,1,0),TextSize=13,BackgroundColor3=Color3.fromRGB(223,210,181)}) end
end
function U:WandRow(index,wand,equipped)
    local row=self:Row(98)
    make("Frame",row,{BackgroundColor3=equipped and Color3.fromRGB(236,219,176) or Color3.fromRGB(226,215,192),BorderSizePixel=0,Size=UDim2.fromScale(1,1)})
    local view=make("ViewportFrame",row,{Position=UDim2.fromOffset(8,8),Size=UDim2.fromOffset(112,82),BackgroundColor3=palette.Ink,BorderSizePixel=0,
        Ambient=Color3.fromRGB(170,170,180),LightColor=Color3.fromRGB(255,244,224),LightDirection=Vector3.new(-1,-1,-0.5)}); corner(view)
    local at=CFrame.Angles(0.3,0,0); local center=(at*CFrame.new(0,0,(0.65-Wands.Length(wand))/2)).Position
    WandModel.Build(wand,at,true).Parent=view
    view.CurrentCamera=make("Camera",view,{FieldOfView=40,CFrame=CFrame.lookAt(center+Vector3.new(3.3,0.6,0),center)})
    local name=Wands.Name(wand)
    local selection={Name=name,Revision=self.Data.WandRevision or 0}
    text(row,name,15,palette.Ink,{Position=UDim2.fromOffset(130,4),Size=UDim2.new(1,-138,0,24),Font=Enum.Font.GothamMedium,TextTruncate=Enum.TextTruncate.AtEnd})
    text(row,Wands.Describe(wand),13,Color3.fromRGB(94,87,73),{Position=UDim2.fromOffset(130,28),Size=UDim2.new(1,-138,0,32),TextWrapped=true,TextYAlignment=Enum.TextYAlignment.Top})
    if equipped then
        text(row,"EQUIPPED",12,palette.Gold,{Position=UDim2.fromOffset(130,62),Size=UDim2.fromOffset(120,30),Font=Enum.Font.GothamBold})
        return
    end
    button(row,"Equip",function() self:Action("EquipWand",index,selection) end,{Position=UDim2.fromOffset(130,62),Size=UDim2.fromOffset(84,30),TextSize=13,BackgroundColor3=palette.Gold})
    local armed,discard=false,nil
    discard=button(row,"Discard",function()
        if armed then self:Action("DiscardWand",index,selection) else armed=true; discard.Text="Confirm?" end
    end,{Position=UDim2.fromOffset(222,62),Size=UDim2.fromOffset(84,30),TextSize=13,BackgroundColor3=Color3.fromRGB(224,212,187)})
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
            make("Frame",row,{BackgroundColor3=rank>0 and Color3.fromRGB(236,219,176) or Color3.fromRGB(226,215,192),BorderSizePixel=0,Size=UDim2.fromScale(1,1)})
            text(row,t.Name.."  ·  "..rank.." / "..t.MaxRank,16,palette.Ink,{Position=UDim2.fromOffset(12,4),Size=UDim2.new(1,-90,0,26)})
            local note=spent<t.Requires and "  Needs "..t.Requires.." points in "..school.."." or ""
            text(row,t.Text..note,13,Color3.fromRGB(94,87,73),{Position=UDim2.fromOffset(12,30),Size=UDim2.new(1,-90,0,38),TextWrapped=true,TextYAlignment=Enum.TextYAlignment.Top})
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
        make("Frame",row,{BackgroundColor3=Color3.fromRGB(226,215,192),BorderSizePixel=0,Size=UDim2.fromScale(1,1)})
        text(row,s.DisplayName.."  /  "..s.Id,17,palette.Ink,{Position=UDim2.fromOffset(12,4),Size=UDim2.new(1,-24,0,25)})
        local detail=learned and (s.School.." · "..num(F.ManaCost(s,self.Data)).." mana · "..num(F.Cooldown(s,self.Data)).."s · Mastery "..learned.Mastery.." ("..learned.Hits.." hits)")
            or ("Level "..s.UnlockLevel.." · "..s.Source..(not s.Implemented and " · Planned content" or ""))
        text(row,detail,13,Color3.fromRGB(94,87,73),{Position=UDim2.fromOffset(12,31),Size=UDim2.new(1,-24,0,36),TextWrapped=true})
        if learned and s.Id~="Scintara" then
            local slots={"Slot1","Slot2","Slot3","Slot4"}; if s.School=="Ward" then slots[#slots+1]="Ward" end
            for i,slot in ipairs(slots) do
                button(row,slot=="Ward" and "Ward" or tostring(i),function() self:Action("Loadout",slot,s.Id) end,
                    {Size=UDim2.fromOffset(45,30),Position=UDim2.fromOffset(12+(i-1)*52,68),BackgroundColor3=self.Data.Loadout[slot]==s.Id and Color3.fromRGB(148,190,148) or palette.Gold})
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
            if id=="Health Draught" or id=="Frigora Tome" or id=="Somnara Tome" then
                button(self.Body,id.." ×"..d.Inventory[id].."  ·  Use",function() self:Action("UseItem",id) end)
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
        self:Paragraph("PC: LMB cast · RMB ward · 1–4 spells · Shift or double-tap WASD dodge\nK spellbook · B bag · M map · Ctrl cursor lock · V first person\nF broom · Space climbs · Q dives\nGamepad: RT cast · LT ward · X/Y/B/RB slots · LB dodge\nD-pad Up book · Left bag · Right map · Down broom · A jump or climb · L3 dive",146)
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
        self:Paragraph("THE HOLLOWMERE APOTHECARY\nHealth Draught restores 40% of your health over 4 seconds. Shared potion cooldown: 30 seconds.",85)
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
    make("Frame",map,{Size=UDim2.fromScale(1,1),BackgroundColor3=Color3.fromRGB(208,211,187),BorderSizePixel=0})
    local zones={{"WHISPERWOOD",0.03,0.08,0.43,0.82,Color3.fromRGB(75,104,83)},{"ACADEMY",0.5,0.05,0.46,0.28,Color3.fromRGB(94,105,128)},
        {"GROUNDS",0.5,0.38,0.46,0.22,Color3.fromRGB(130,148,104)},{"HOLLOWMERE",0.5,0.65,0.46,0.28,Color3.fromRGB(157,120,83)}}
    for _,z in ipairs(zones) do
        local region=make("Frame",map,{Position=UDim2.fromScale(z[2],z[3]),Size=UDim2.fromScale(z[4],z[5]),BackgroundColor3=z[6],BorderSizePixel=0}); corner(region)
        text(region,z[1],14,palette.White,{Size=UDim2.fromScale(1,1),TextXAlignment=Enum.TextXAlignment.Center,TextWrapped=true})
    end
    self:Paragraph("Waystone travel costs 25 Gilders. Attune a stone by touching its prompt. Travel starts beside any Waystone, outside combat.",70)
    for _,id in ipairs({"Hollowmere","Castle","Whisperwood"}) do
        button(self.Body,(self.Data.Waystones[id] and "Travel to " or "Undiscovered: ")..id,function() self:Action("Travel",id) end)
    end
end
function U:Sorting()
    self.SortAnswers={}; self:SortingQuestion(1)
end
function U:SortingQuestion(index)
    self:Open("THE MIRROR OF CHOOSING","Sorting")
    local question=Config.SortingQuestions[index]
    if question then
        self:Paragraph("Question "..index.." of 5\n"..question.Q,90)
        for i,answer in ipairs(question.A) do button(self.Body,answer,function() self.SortAnswers[index]=i; self:SortingQuestion(index+1) end) end
    else
        local scores={0,0,0,0}; for _,answer in ipairs(self.SortAnswers) do scores[answer]=scores[answer]+1 end
        local best=1; for i=2,4 do if scores[i]>scores[best] then best=i end end
        self:Paragraph("The mirror sees "..Config.HouseOrder[best].." in you.\nThe choice is yours. Select the house you want to join.",85)
        for _,house in ipairs(Config.HouseOrder) do
            button(self.Body,house.." · "..Config.Houses[house].Trait.."\n"..Config.Houses[house].Perk,function() self:Action("Sort",self.SortAnswers,house); self:Close() end,{Size=UDim2.new(1,-12,0,58)})
        end
    end
end
function U:Lesson(info)
    self:Open("A LESSON WITH "..string.upper(info.Teacher),"Lesson")
    self:Paragraph("Learning "..info.Spell..". Trace from START to END in one stroke. Score 70% or better, then hit five targets. Mouse / touch: drag. Gamepad: hold RT + left stick; X submits.",84)
    local canvas=make("Frame",self.Body,{Size=UDim2.new(1,-12,0,220),BackgroundColor3=Color3.fromRGB(34,45,52),BorderSizePixel=0,ClipsDescendants=true,Active=true})
    corner(canvas); local ink=make("Frame",canvas,{Size=UDim2.fromScale(1,1),BackgroundTransparency=1})
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
    button(self.Body,"Submit gesture",function() self.Remotes.Gesture:FireServer(info.Token,points) end)
    button(self.Body,"Clear and try again",clear,{BackgroundColor3=Color3.fromRGB(224,212,187)})
end
function U:Build()
    self.Gui=make("ScreenGui",self.Player:WaitForChild("PlayerGui"),{Name="WandboundHUD",ResetOnSpawn=false,IgnoreGuiInset=false,ZIndexBehavior=Enum.ZIndexBehavior.Sibling})
    self.Root=make("Frame",self.Gui,{Size=UDim2.fromScale(1,1),BackgroundTransparency=1})
    self.Brand=text(self.Root,"WANDBOUND",23,palette.White,{Position=UDim2.fromOffset(22,8),Font=Enum.Font.Garamond,Size=UDim2.fromOffset(280,32)})
    self.Subtitle=text(self.Root,"R A V E N M O O R   A C A D E M Y",10,palette.Gold,{Position=UDim2.fromOffset(23,38),Size=UDim2.fromOffset(300,20)})
    self.Location=text(self.Root,"Hollowmere Village",15,palette.White,{Position=UDim2.fromOffset(23,63),Size=UDim2.fromOffset(310,28)})
    self.ClassLabel=text(self.Root,"Next class",14,palette.White,{AnchorPoint=Vector2.new(1,0),Position=UDim2.new(1,-20,0,9),Size=UDim2.fromOffset(240,40),TextXAlignment=Enum.TextXAlignment.Right,TextWrapped=true})
    self.MenuButton=button(self.Root,"K  SPELLBOOK",function() self:Show("Spells") end,{AnchorPoint=Vector2.new(1,0),Position=UDim2.new(1,-20,0,57),Size=UDim2.fromOffset(155,42),TextSize=13,BackgroundColor3=palette.Ink,TextColor3=palette.White})
    stroke(self.MenuButton,palette.Gold)
    self.QuestFrame=make("Frame",self.Root,{Position=UDim2.fromOffset(22,104),Size=UDim2.fromOffset(265,129),BackgroundColor3=palette.Ink,BackgroundTransparency=0.15,BorderSizePixel=0}); corner(self.QuestFrame); stroke(self.QuestFrame,palette.Gold,0.55)
    text(self.QuestFrame,"YOUR NEXT CHAPTER",10,palette.Gold,{Position=UDim2.fromOffset(12,5),Size=UDim2.new(1,-24,0,22)})
    self.QuestLabel=text(self.QuestFrame,"Opening your record…",14,palette.White,{Position=UDim2.fromOffset(12,30),Size=UDim2.new(1,-24,1,-38),TextWrapped=true,TextYAlignment=Enum.TextYAlignment.Top})
    self.Crosshair=text(self.Root,"+",26,palette.White,{AnchorPoint=Vector2.new(0.5,0.5),Position=UDim2.fromScale(0.5,0.5),Size=UDim2.fromOffset(32,32),TextXAlignment=Enum.TextXAlignment.Center})
    self.StatFrame=make("Frame",self.Root,{BackgroundTransparency=1,Position=UDim2.new(0,22,1,-130),Size=UDim2.fromOffset(250,105)})
    self.Bars={}
    for i,name in ipairs({"HP","MANA","STAMINA"}) do
        local color=({Color3.fromRGB(165,70,72),Color3.fromRGB(85,124,195),Color3.fromRGB(170,148,80)})[i]
        local frame=make("Frame",self.StatFrame,{Position=UDim2.fromOffset(0,(i-1)*31),Size=UDim2.new(1,0,0,24),BackgroundColor3=palette.Ink,BorderSizePixel=0}); corner(frame,4)
        local fill=make("Frame",frame,{Size=UDim2.fromScale(1,1),BackgroundColor3=color,BorderSizePixel=0}); corner(fill,4)
        local label=text(frame,name,12,palette.White,{Position=UDim2.fromOffset(8,0),Size=UDim2.new(1,-16,1,0)})
        self.Bars[name]={Fill=fill,Label=label}
    end
    self.Hotbar=make("Frame",self.Root,{BackgroundTransparency=1,AnchorPoint=Vector2.new(0.5,1),Position=UDim2.new(0.5,0,1,-18),Size=UDim2.fromOffset(#self.SpellSlots*80,72)})
    for i,slot in ipairs(self.SpellSlots) do
        local b=button(self.Hotbar,slot,function() if self.C.InputController and slot~="Lance" then self.C.InputController:UseSlot(slot) end end,
            {Size=UDim2.fromOffset(72,68),Position=UDim2.fromOffset((i-1)*80,0),BackgroundColor3=palette.Ink,TextColor3=palette.White,TextSize=12})
        stroke(b,palette.Gold,0.35); self.Buttons[slot]=b
        -- The lance pours while the button is held, as the right mouse button does.
        if slot=="Lance" then
            b.InputBegan:Connect(function(input)
                if input.UserInputType==Enum.UserInputType.Touch or input.UserInputType==Enum.UserInputType.MouseButton1 then self.C.InputController:Lance(true) end
            end)
            b.InputEnded:Connect(function(input)
                if input.UserInputType==Enum.UserInputType.Touch or input.UserInputType==Enum.UserInputType.MouseButton1 then self.C.InputController:Lance(false) end
            end)
        end
    end
    self.ToastFrame=make("Frame",self.Root,{AnchorPoint=Vector2.new(0.5,0),Position=UDim2.new(0.5,0,0,64),Size=UDim2.new(0.6,0,0,56),BackgroundColor3=palette.Ink,BorderSizePixel=0,Visible=false,ZIndex=7}); corner(self.ToastFrame); stroke(self.ToastFrame)
    self.ToastLabel=text(self.ToastFrame,"",15,palette.White,{Size=UDim2.new(1,-20,1,0),Position=UDim2.fromOffset(10,0),TextXAlignment=Enum.TextXAlignment.Center,TextWrapped=true,ZIndex=8})
    self.BossFrame=make("Frame",self.Root,{AnchorPoint=Vector2.new(0.5,0),Position=UDim2.new(0.5,0,0,128),Size=UDim2.new(0.4,0,0,47),BackgroundColor3=palette.Ink,BorderSizePixel=0,Visible=false}); corner(self.BossFrame)
    self.BossLabel=text(self.BossFrame,"",14,palette.White,{Size=UDim2.new(1,-16,0,29),Position=UDim2.fromOffset(8,0),TextXAlignment=Enum.TextXAlignment.Center})
    self.BossFill=make("Frame",self.BossFrame,{Position=UDim2.fromOffset(6,33),Size=UDim2.new(1,-12,0,7),BackgroundColor3=Color3.fromRGB(168,70,116),BorderSizePixel=0})
    self.Panel=make("Frame",self.Root,{AnchorPoint=Vector2.new(0.5,0.5),Position=UDim2.fromScale(0.5,0.5),Size=UDim2.fromOffset(760,570),BackgroundColor3=palette.Panel,BorderSizePixel=0,Visible=false,ZIndex=20}); corner(self.Panel,12); stroke(self.Panel)
    self.PanelTitle=text(self.Panel,"",22,palette.Ink,{Font=Enum.Font.Garamond,Position=UDim2.fromOffset(22,9),Size=UDim2.new(1,-100,0,39),ZIndex=21,TextWrapped=true})
    self.CloseButton=button(self.Panel,"×",function() self:Close() end,{Position=UDim2.new(1,-54,0,8),Size=UDim2.fromOffset(42,42),TextSize=25,ZIndex=22,BackgroundColor3=Color3.fromRGB(221,207,177)})
    self.Body=make("ScrollingFrame",self.Panel,{Position=UDim2.fromOffset(20,60),Size=UDim2.new(1,-34,1,-78),BackgroundTransparency=1,BorderSizePixel=0,ScrollBarThickness=4,ScrollBarImageColor3=palette.Gold,CanvasSize=UDim2.new(),AutomaticCanvasSize=Enum.AutomaticSize.Y,ZIndex=21})
    make("UIListLayout",self.Body,{Padding=UDim.new(0,9),SortOrder=Enum.SortOrder.LayoutOrder})
    self.Body.DescendantAdded:Connect(function(inst) if inst:IsA("GuiObject") then inst.ZIndex=22 end end)
end
function U:Layout()
    local size=self.Root.AbsoluteSize; local mobile=UIS.TouchEnabled and size.X<1050
    self.Panel.Size=UDim2.fromOffset(math.min(800,size.X-26),math.min(600,size.Y-26))
    self.ClassLabel.Size=UDim2.fromOffset(size.X<600 and 160 or 240,42)
    self.Brand.TextSize=size.X<600 and 20 or 23
    self.Subtitle.Visible=size.X>=600
    self.MenuButton.Text=mobile and "SPELLBOOK" or "K  SPELLBOOK"
    self.MenuButton.Size=UDim2.fromOffset(mobile and 135 or 155,mobile and 54 or 42)
    self.QuestFrame.Size=UDim2.fromOffset(size.X<600 and 210 or 265,120)
    self.StatFrame.Size=UDim2.fromOffset(mobile and 180 or 235,95)
    self.StatFrame.Position=UDim2.new(0,22,1,mobile and -270 or -200)
    if mobile then
        self.Hotbar.Size=UDim2.fromOffset(292,math.ceil(#self.SpellSlots/4)*74-4); self.Hotbar.Position=UDim2.new(1,-14,1,-83); self.Hotbar.AnchorPoint=Vector2.new(1,1)
        for i,slot in ipairs(self.SpellSlots) do self.Buttons[slot].Size=UDim2.fromOffset(66,66); self.Buttons[slot].Position=UDim2.fromOffset(((i-1)%4)*74,math.floor((i-1)/4)*74) end
    else
        self.Hotbar.Size=UDim2.fromOffset(#self.SpellSlots*80,72); self.Hotbar.Position=UDim2.new(0.5,0,1,-18); self.Hotbar.AnchorPoint=Vector2.new(0.5,1)
        for i,slot in ipairs(self.SpellSlots) do self.Buttons[slot].Size=UDim2.fromOffset(72,68); self.Buttons[slot].Position=UDim2.fromOffset((i-1)*80,0) end
    end
end
function U:UpdateHUD()
    local d=self.Data; local s=self.State
    if d then
        local q=Quests[d.Quest]
        self.QuestLabel.Text=q and (q.Title.."  "..d.QuestProgress.."/"..q.Need.."\n"..q.Hint) or "The first seal is safe. Explore, master your spells, and duel with friends."
        self.Location.Text=(self.Player:GetAttribute("Zone") or "Hollowmere").."  ·  Lv "..d.Level.."  ·  "..d.Gilders.." G"
        local keys={Basic="LMB",Lance="RMB",Slot1="1",Slot2="2",Slot3="3",Slot4="4",Ward="R",Dodge="SHIFT",Broom="F"}
        if tostring(UIS:GetLastInputType()):find("Gamepad") then keys={Basic="RT",Lance="LT",Slot1="X",Slot2="Y",Slot3="B",Slot4="RB",Ward="R3",Dodge="LB",Broom="DOWN"} end
        local flying=self.Player:GetAttribute("Broom")~=nil
        for _,slot in ipairs(self.SpellSlots) do
            local id=slot=="Basic" and "Scintara" or slot=="Lance" and "ScintaraLance" or d.Loadout[slot]
            local remaining=math.max(0,(id and self.Cooldowns[id] or 0)-os.clock())
            local name=slot=="Dodge" and "Dodge" or slot=="Broom" and (flying and "Land" or "Broom") or slot=="Lance" and "Lance"
                or (id and id~="" and id or "Empty")
            self.Buttons[slot].Text=(UIS.TouchEnabled and "" or keys[slot].."\n")..name..(remaining>0 and string.format("\n%.1fs",remaining) or "")
            self.Buttons[slot].TextColor3=remaining>0 and palette.Muted or palette.White
        end
    end
    for name,bar in pairs(self.Bars) do
        local value=name=="HP" and (s.HP or 0) or (name=="MANA" and (s.Mana or 0) or (s.Stamina or 0))
        local maximum=name=="HP" and (s.MaxHP or 110) or (name=="MANA" and (s.MaxMana or 102) or 100)
        bar.Fill.Size=UDim2.fromScale(math.clamp(value/math.max(1,maximum),0,1),1)
        bar.Label.Text=name.."   "..math.ceil(value).." / "..math.floor(maximum)..(name=="HP" and (s.Shield or 0)>0 and "  +"..math.floor(s.Shield).." shield" or "")
    end
    if s.Class then local t=s.Class.Seconds; self.ClassLabel.Text="NEXT CLASS · "..s.Class.Subject.."\n"..string.format("%d:%02d",math.floor(t/60),t%60).."  ·  Practice anytime" end
    local root=self.Player.Character and self.Player.Character:FindFirstChild("HumanoidRootPart")
    local boss=nil; local runtime=workspace:FindFirstChild("Runtime"); local folder=runtime and runtime:FindFirstChild("Monsters")
    if root and folder then
        for _,model in ipairs(folder:GetChildren()) do
            local r=model.PrimaryPart; if r and model:GetAttribute("Rank")=="Boss" and (r.Position-root.Position).Magnitude<130 then boss=model; break end
        end
    end
    self.BossFrame.Visible=boss~=nil and not self:IsOpen()
    if boss then
        local hum=boss:FindFirstChildOfClass("Humanoid")
        if hum then self.BossLabel.Text=boss.Name.." · Phase "..tostring(boss:GetAttribute("Phase") or 1); self.BossFill.Size=UDim2.new(math.clamp(hum.Health/hum.MaxHealth,0,1),-12,0,7) end
    end
    self.Crosshair.Visible=not self:IsOpen() and (not self.C.InputController or self.C.InputController.Locked)
end
function U:Welcome()
    self:Open("WANDBOUND · RAVENMOOR ACADEMY","Welcome")
    self:Paragraph("A lantern flickers in the tower.\nSomething beneath Ravenmoor is waking.",80)
    self:Paragraph("Begin at Oakhart's Wandery in Hollowmere. Receive your wand, choose a house, attend your first class, and follow Tobb into Whisperwood.",95)
    self:Paragraph("Approach a named character and use the interaction prompt. Follow the quest card. Red ground circles warn you where enemies will strike.",90)
    self:Paragraph("LMB casts Spark Bolt · RMB raises your ward · Shift or double-tap WASD dodges · F flies your broom\nUse the on-screen buttons on touch devices. K opens your spellbook.",74)
    button(self.Body,"BEGIN YOUR FIRST YEAR",function() self:Close() end,{BackgroundColor3=palette.Gold,Size=UDim2.new(1,-12,0,56)})
end
function U:Start()
    self:Build(); self:Layout(); self.Root:GetPropertyChangedSignal("AbsoluteSize"):Connect(function() self:Layout() end)
    self.Remotes.Profile.OnClientEvent:Connect(function(data)
        self.Data=data
        if self.Menu and ({Spells=true,Skills=true,Journal=true,Bag=true,Settings=true,Bank=true,Shop=true,House=true,Library=true,Wandery=true,Admin=true})[self.Menu] then
            -- Re-render in place: keep the scroll position once the new layout has been measured.
            local menu=self.Menu; local scroll=self.Body.CanvasPosition; self:Show(menu)
            task.spawn(function() Run.RenderStepped:Wait(); if self.Menu==menu then self.Body.CanvasPosition=scroll end end)
        end
    end)
    self.Remotes.State.OnClientEvent:Connect(function(state)
        self.State=state; self.Cooldowns={}; for id,left in pairs(state.Cooldowns) do self.Cooldowns[id]=os.clock()+left end
    end)
    self.Remotes.CastReply.OnClientEvent:Connect(function(id,ok,value)
        if ok then self.Cooldowns[id]=os.clock()+value elseif value~="Cooling down" then self:Toast(value) end
    end)
    self.Remotes.UI.OnClientEvent:Connect(function(kind,info)
        if kind=="Toast" then self:Toast(info)
        elseif kind=="Dialogue" then
            self:Open(string.upper(info.Name),"Dialogue")
            self:Paragraph(info.Text,110)
            for _,choice in ipairs(info.Choices) do
                button(self.Body,choice.Label,function() self:Close(); self:Action("Interact",info.Anchor,choice.Id) end)
            end
            button(self.Body,"Goodbye",function() self:Close() end)
        elseif kind=="Sorting" then self:Sorting()
        elseif kind=="Lesson" then self:Lesson(info)
        elseif kind=="GestureResult" then if info.Pass then self:Close() else self:Toast("Rune accuracy: "..info.Score.."%. Clear the canvas and try again.") end
        elseif kind=="DuelInvite" then
            self:Open("A CHALLENGE TO DUEL","Invite"); self:Paragraph(info.Name.." challenges you to a friendly duel. No items are lost.",80)
            button(self.Body,"Accept duel",function() self:Action("DuelRespond",true); self:Close() end)
            button(self.Body,"Decline",function() self:Action("DuelRespond",false); self:Close() end)
        elseif kind=="DuelStart" then self:Close(); self:Toast("Bow. Ready in "..info.." seconds…")
        elseif kind=="Knockout" then self:Close(); self:Toast("Knocked out · returning to your Waystone in "..info.." seconds. Nothing lost.")
        else self:Show(kind) end
    end)
    self:Welcome()
    task.spawn(function()
        for _=1,10 do if self.Data then break end; self:Action("Ready"); task.wait(1) end
    end)
    local elapsed=0
    Run.RenderStepped:Connect(function(dt) elapsed=elapsed+dt; if elapsed>0.1 then elapsed=0; self:UpdateHUD() end end)
end
return U
