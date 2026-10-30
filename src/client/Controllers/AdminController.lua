local Players=game:GetService("Players")
local RS=game:GetService("ReplicatedStorage")
local CAS=game:GetService("ContextActionService")
local UIS=game:GetService("UserInputService")
local Config=require(RS.Shared.Config)
local Spells=require(RS.Shared.SpellData)
local Quests=require(RS.Shared.QuestData)
local Wands=require(RS.Shared.WandData)
-- The admin panel (P): testing tools that skip the story's gates. The server's AdminService decides who
-- may use it and checks every command; this controller only draws the menu for players it marked Admin.
local A={}
local TAB=Color3.fromRGB(223,210,181)
-- Teleport targets: Waystone ids from Config.Waystones, or names of parts in Workspace.Markers.
local PLACES={{"Hollowmere","Hollowmere Waystone"},{"Castle","Castle Waystone"},{"Whisperwood","Whisperwood Waystone"},
    {"Oakhart","Oakhart's Wandery"},{"Apothecary","Apothecary"},{"Bank","Vaultkeep Bank"},
    {"Mirror","Mirror of Choosing"},{"Library","Restricted Shelf"},{"Training","Training Yard"},{"Duelmaster","Dueling Club"}}
for _,school in ipairs(Config.Subjects) do
    local t=Config.Teachers[school]; PLACES[#PLACES+1]={t.Anchor,t.Name.." · "..t.Title}
end
for _,entry in ipairs({{"Tobb","Tobb · forest edge"},{"ForestGate","Forest gate"},{"SpiderClearing","Spider clearing"},{"Moonwell","Moonwell"},
    {"HowlerDen","Howler den"},{"Rotbark","Rotbark Sentinel"},{"Vexweave","Vexweave's grotto"}}) do PLACES[#PLACES+1]=entry end
function A:Init(controllers) self.C=controllers; self.Player=Players.LocalPlayer end
function A:Allowed() return self.Player:GetAttribute("Admin")==true end
function A:Send(command,arg) self.C.UIController:Action("Admin",command,arg) end
function A:Toggle()
    local ui=self.C.UIController
    if ui.Menu=="Admin" then ui:Close() else ui:Show("Admin") end
end
-- One row of equal-width buttons. Each entry is {label, callback, highlighted}.
function A:Buttons(list)
    local ui=self.C.UIController; local kit=ui.Kit; local row=ui:Row(44)
    for i,entry in ipairs(list) do
        kit.button(row,entry[1],entry[2],{Position=UDim2.new((i-1)/#list,3,0,0),Size=UDim2.new(1/#list,-6,1,0),TextSize=13,
            BackgroundColor3=entry[3] and kit.palette.Gold or TAB})
    end
end
-- Splits a long list of buttons into rows of `per`.
function A:Grid(list,per)
    for i=1,#list,per do self:Buttons({table.unpack(list,i,math.min(i+per-1,#list))}) end
end
function A:SpellRow(sp,d)
    local ui=self.C.UIController; local kit=ui.Kit; local row=ui:Row(44)
    kit.text(row,sp.Id.." · "..sp.DisplayName.."\nLv "..sp.UnlockLevel.." "..sp.School..(d.Spells[sp.Id] and " · learned" or ""),13,kit.palette.Ink,
        {Size=UDim2.new(0.46,0,1,0),TextWrapped=true})
    if sp.Id=="Scintara" then
        kit.text(row,"Always on left mouse",13,kit.palette.Ink,{Position=UDim2.fromScale(0.46,0),Size=UDim2.new(0.54,0,1,0)})
        return
    end
    local slots={"Slot1","Slot2","Slot3","Slot4"}; if sp.School=="Ward" then slots[5]="Ward" end
    for i,slot in ipairs(slots) do
        kit.button(row,slot=="Ward" and "Ward" or tostring(i),function() self:Send("Assign",{Spell=sp.Id,Slot=slot}) end,
            {Position=UDim2.new(0.46+(i-1)*0.108,3,0,2),Size=UDim2.new(0.108,-6,1,-4),TextSize=13,
            BackgroundColor3=d.Loadout[slot]==sp.Id and kit.palette.Gold or TAB})
    end
end
function A:Render()
    local ui=self.C.UIController; local d=ui.Data
    ui:Open("ADMIN · TESTING TOOLS","Admin")
    ui:Paragraph(self.Player:GetAttribute("SessionOnly") and "Unlock anything the story gates. This is a Studio playtest, so nothing here is saved."
        or "Unlock anything the story gates. This is a live server: these changes ARE saved to your profile.",40)

    ui:Paragraph("PLAYER · Level "..d.Level.." · "..d.Gilders.." Gilders · "..d.Attributes.Unspent.." attribute points",30)
    local levels={}
    for _,n in ipairs({1,5,10,15,20}) do levels[#levels+1]={"Level "..n,function() self:Send("Level",n) end,d.Level==n} end
    self:Buttons(levels)
    self:Buttons({{"+1,000 XP",function() self:Send("XP") end},{"+1,000 Gilders",function() self:Send("Gilders") end},
        {"Potions, tomes, materials ×5",function() self:Send("Items") end}})
    local free=self.Player:GetAttribute("FreeCast")==true
    self:Buttons({{"Refill HP & mana · reset cooldowns",function() self:Send("Refill") end},
        {"Free casting: "..(free and "ON" or "OFF"),function() self:Send("FreeCast") end,free}})

    ui:Paragraph("SPELLS · Learn any spell at any level, then press 1–4 (or Ward) to put it in that slot.",30)
    self:Buttons({{"Learn every spell",function() self:Send("LearnAll") end},{"Mastery 5 for learned spells",function() self:Send("Mastery") end}})
    local list={}
    for _,sp in pairs(Spells) do if sp.Implemented then list[#list+1]=sp end end
    table.sort(list,function(a,b) if a.UnlockLevel~=b.UnlockLevel then return a.UnlockLevel<b.UnlockLevel end; return a.Id<b.Id end)
    for _,sp in ipairs(list) do self:SpellRow(sp,d) end

    ui:Paragraph("WANDS · Case "..#d.Wands.." / "..Wands.Capacity..". Equip or discard wands in your bag (B).",30)
    local rolls={}; for _,id in ipairs(Wands.RarityOrder) do rolls[#rolls+1]={"Random "..id,function() self:Send("Wand",id) end} end
    self:Buttons(rolls)
    local named={}; for _,id in ipairs(Wands.NamedOrder) do named[#named+1]={Wands.Named[id].Title,function() self:Send("Named",id) end} end
    named[#named+1]={"Open your bag",function() ui:Show("Bag") end}
    self:Buttons(named)

    local q=Quests[d.Quest]
    ui:Paragraph("STORY · Now: "..(q and d.Quest..". "..q.Title or "complete")..". Jumping ahead completes every earlier quest and grants its rewards.",50)
    local steps={}
    for i,quest in ipairs(Quests) do steps[#steps+1]={i..". "..quest.Title,function() self:Send("Quest",i) end,d.Quest==i} end
    steps[#steps+1]={"Finish the story",function() self:Send("Quest",#Quests+1) end,d.Quest>#Quests}
    self:Grid(steps,2)

    ui:Paragraph("HOUSE & TRAVEL · "..(d.House~="" and d.House or "Unsorted"),30)
    local houses={}; for _,house in ipairs(Config.HouseOrder) do houses[#houses+1]={house,function() self:Send("House",house) end,d.House==house} end
    self:Buttons(houses)
    self:Buttons({{"Attune every Waystone",function() self:Send("Waystones") end},{"Open the map (M)",function() ui:Show("Map") end}})
    local places={}
    for _,place in ipairs(PLACES) do places[#places+1]={place[2],function() ui:Close(); self:Send("Teleport",place[1]) end} end
    self:Grid(places,3)

    ui:Paragraph("CAMERA · Scroll all the way in for first person, or press V to lock it on and off.",30)
    local input=self.C.InputController
    self:Buttons({{"First person: "..(self.Player.CameraMode==Enum.CameraMode.LockFirstPerson and "LOCKED" or "OFF"),function()
        input:SetFirstPerson(self.Player.CameraMode~=Enum.CameraMode.LockFirstPerson); self:Render()
    end,self.Player.CameraMode==Enum.CameraMode.LockFirstPerson}})
end
function A:Start()
    local ui=self.C.UIController; local kit=ui.Kit
    self.Button=kit.button(ui.Root,"P  ADMIN",function() self:Toggle() end,{AnchorPoint=Vector2.new(1,0),TextSize=13,
        BackgroundColor3=kit.palette.Ink,TextColor3=kit.palette.Gold,Visible=false})
    kit.stroke(self.Button,kit.palette.Gold,0.4)
    -- Sits under the spellbook button, which UIController resizes for touch screens.
    local function place()
        local menu=ui.MenuButton
        self.Button.Size=UDim2.fromOffset(menu.Size.X.Offset,34)
        self.Button.Position=UDim2.new(1,-20,0,menu.Position.Y.Offset+menu.Size.Y.Offset+6)
    end
    place(); ui.MenuButton:GetPropertyChangedSignal("Size"):Connect(place)
    local function refresh() self.Button.Visible=self:Allowed() end
    refresh(); self.Player:GetAttributeChangedSignal("Admin"):Connect(refresh)
    self.Player:GetAttributeChangedSignal("FreeCast"):Connect(function() if ui.Menu=="Admin" then ui:Show("Admin") end end)
    CAS:BindAction("Wandbound_Admin",function(_,state)
        if UIS:GetFocusedTextBox() or not self:Allowed() then return Enum.ContextActionResult.Pass end
        if state==Enum.UserInputState.Begin then self:Toggle() end
        return Enum.ContextActionResult.Sink
    end,false,Enum.KeyCode.P)
end
return A
