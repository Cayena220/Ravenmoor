local Players=game:GetService("Players")
local RS=game:GetService("ReplicatedStorage")
local Config=require(RS.Shared.Config)
local F=require(RS.Shared.Formulas)
local Wands=require(RS.Shared.WandData)
local Quests=require(RS.Shared.QuestData)
local I={}
function I:Init(services) self.S=services; self.PotionCooldowns={}; self.Interactions={} end
local advice={
    Oakhart="Open your bag with B to equip a wand. Use K to assign learned spells to 1–4. Right mouse raises your ward; left mouse casts Scintara.",
    Tobb="Watch for red attack circles in Whisperwood. Shift dodges. Bring Thorn Barbs and Spider Silk to the apothecary to brew Health Draughts.",
    Bank="Your vault keeps Gilders separate from your spending money. Deposits and withdrawals are available here.",
    Apothecary="A Thorn Barb and Spider Silk make one Health Draught. Use it from your bag to recover health over four seconds.",
    Duelmaster="Bring another student here for a friendly duel. Both players must accept. You keep your items, and matches end before a lethal hit.",
}
function I:Interact(player,name,choice)
    if type(name)~="string" or type(choice)~="string" then return end
    local npc=self.Interactions[name]; local d=self.S.PlayerDataService:Get(player)
    if not npc or not d or not self.S.WorldService:Near(player,name,15) or self.S.DuelService:IsBusy(player) then return end
    if choice=="Service" then return npc.Callback(player) end
    local message
    if choice=="Advice" then message=advice[name] or "Receive your wand, choose a house, then ask a professor for a lesson. Trace the rune and hit five targets with Scintara."
    elseif choice=="Quest" then local q=Quests[d.Quest]; message=q and (q.Title..": "..q.Hint) or "You have completed the first story. Explore the woods, practise spells, and try a friendly duel."
    elseif choice=="Hello" then message="Welcome, student. What can I help you with?"
    else return end
    self.S.NetworkService.UI:FireClient(player,"Dialogue",{Anchor=name,Name=npc.Name,Text=message,
        Choices={{Id="Service",Label=npc.Action},{Id="Advice",Label="Do you have any advice?"},{Id="Quest",Label="What should I do next?"}}})
end
function I:Prompt(name,label,action,callback)
    local conversational=name~="Mirror" and not name:match("^Waystone_")
    if conversational then self.Interactions[name]={Name=label,Action=action,Callback=callback} end
    local anchor=self.S.WorldService:Anchor(name); if not anchor then warn("Missing interaction",name); return end
    local prompt=Instance.new("ProximityPrompt"); prompt.Name="Interact"; prompt.ObjectText=label; prompt.ActionText=conversational and "Talk" or action
    prompt.KeyboardKeyCode=Enum.KeyCode.E; prompt.GamepadKeyCode=Enum.KeyCode.ButtonX
    prompt.MaxActivationDistance=12; prompt.HoldDuration=0.2; prompt.RequiresLineOfSight=false; prompt.Parent=anchor
    prompt.Triggered:Connect(function(player)
        if self.S.WorldService:Near(player,anchor,15) and self.S.PlayerDataService:Get(player)
            and not self.S.DuelService:IsBusy(player) and self.S.NetworkService:Allow(player,"Prompt",3,5) then
                if conversational then self:Interact(player,name,"Hello") else callback(player) end
            end
    end)
end
function I:Unseal(player,part)
    local chest=part
    while chest and chest.Parent~=workspace.Map do
        if chest:GetAttribute("ChestId") then break end
        chest=chest.Parent
    end
    if not chest or not chest:GetAttribute("ChestId") then return end
    local id=chest:GetAttribute("ChestId"); local root=self.S.WorldService:Root(player); local pos=chest:GetPivot().Position
    if not root or (root.Position-pos).Magnitude>35 then return end
    local d=self.S.PlayerDataService:Get(player); if not d then return end
    d.Chests=d.Chests or {}
    if os.time()-(d.Chests[id] or 0)<300 then return self.S.NetworkService:Notice(player,"This chest will refill in five minutes.") end
    d.Chests[id]=os.time(); self.S.ProgressionService:Award(player,25,35)
    self.S.NetworkService:Notice(player,"Unsealed chest · +35 Gilders")
    self.S.NetworkService.FX:FireAllClients("Blast",pos,"Aegara",4)
end
function I:Start()
    self.S.NetworkService.Handlers.Interact=function(player,name,choice) self:Interact(player,name,choice) end
    self:Prompt("Oakhart","Odric Oakhart","Wands",function(player)
        local d=self.S.PlayerDataService:Get(player)
        if d.HasWand then self.S.WandService:Deliver(player); return self.S.NetworkService.UI:FireClient(player,"Wandery") end
        local wand=Wands.Roll("Common")
        d.HasWand=true; self.S.WandService:Grant(player,wand)
        for _,id in ipairs({"Scintara","Aegara","Glimmora"}) do self.S.ProgressionService:Learn(player,id,true) end
        self.S.ProgressionService:Event(player,"Wand")
        self.S.NetworkService:Notice(player,"The wand chooses you: "..Wands.Name(wand)..". Scintara, Aegara and Glimmora are yours.")
    end)
    self:Prompt("Mirror","Mirror of Choosing","Discover your house",function(player)
        local d=self.S.PlayerDataService:Get(player)
        if not d.HasWand then return self.S.NetworkService:Notice(player,"Visit Oakhart's Wandery first.") end
        if d.House~="" then return self.S.NetworkService:Notice(player,"You belong to "..d.House..". "..Config.Houses[d.House].Perk) end
        self.S.NetworkService.UI:FireClient(player,"Sorting")
    end)
    for school,teacher in pairs(Config.Teachers) do
        self:Prompt(teacher.Anchor,teacher.Name,"Practice "..teacher.Title,function(player) self.S.ClassService:Begin(player,school) end)
    end
    self:Prompt("Tobb","Tobb Brambleworth","Ask about Whisperwood",function(player)
        self.S.ProgressionService:Event(player,"Tobb")
        self.S.NetworkService:Notice(player,"Thornimps are swarming the woodland path. Watch the red attack circles, and dodge!")
    end)
    self:Prompt("Bank","Vaultkeep Bank","Open vault",function(player) self.S.NetworkService.UI:FireClient(player,"Bank") end)
    self:Prompt("Apothecary","Hollowmere Apothecary","Shop & brew",function(player) self.S.NetworkService.UI:FireClient(player,"Shop") end)
    self:Prompt("Library","Restricted Shelf","Study the archive",function(player)
        local d=self.S.PlayerDataService:Get(player)
        if d.Level>=14 then self.S.ProgressionService:Learn(player,"Tractum",false)
        else self.S.NetworkService:Notice(player,"Return at level 14 to study Tractum.") end
        self.S.NetworkService.UI:FireClient(player,"Library")
    end)
    self:Prompt("Duelmaster","Duelmaster Kestrel Vey","Open Dueling Club",function(player)
        local d=self.S.PlayerDataService:Get(player)
        if d.Level>=6 then self.S.ProgressionService:Learn(player,"Excido",false) end
        self.S.NetworkService.UI:FireClient(player,"Duels")
    end)
    for id in pairs(Config.Waystones) do
        self:Prompt("Waystone_"..id,id.." Waystone","Attune / travel",function(player)
            local d=self.S.PlayerDataService:Get(player); d.Waystones[id]=true; d.LastWaystone=id
            self.S.ProgressionService:Refresh(player); self.S.NetworkService.UI:FireClient(player,"Map")
        end)
    end
    self.S.NetworkService.Handlers.Sort=function(player,answers,choice)
        local d=self.S.PlayerDataService:Get(player)
        if not d or not d.HasWand or d.House~="" or type(answers)~="table" or #answers~=5 or type(choice)~="string" or not Config.Houses[choice] then return end
        if not self.S.WorldService:Near(player,"Mirror",18) then return end
        for _,v in ipairs(answers) do if not F.Finite(v) or v%1~=0 or v<1 or v>4 then return end end
        d.House=choice; self.S.ProgressionService:Event(player,"Sorted"); self.S.CombatService:UpdateStats(player,true)
        self.S.NetworkService:Notice(player,"Welcome to "..choice.."!")
    end
    self.S.NetworkService.Handlers.Bank=function(player,action,amount)
        local d=self.S.PlayerDataService:Get(player)
        if not d or not self.S.WorldService:Near(player,"Bank",15) or self.S.DuelService:IsBusy(player)
            or not F.Finite(amount) or amount%1~=0 or amount<1 or amount>1000000 then return end
        if action=="Deposit" and d.Gilders>=amount then d.Gilders=d.Gilders-amount; d.BankGilders=d.BankGilders+amount
        elseif action=="Withdraw" and d.BankGilders>=amount then d.BankGilders=d.BankGilders-amount; d.Gilders=d.Gilders+amount
        else return self.S.NetworkService:Notice(player,"Not enough Gilders.") end
        self.S.ProgressionService:Refresh(player); self.S.NetworkService:Notice(player,"Vault balance: "..d.BankGilders.." Gilders")
    end
    self.S.NetworkService.Handlers.Shop=function(player,action)
        local d=self.S.PlayerDataService:Get(player)
        if not d or not self.S.WorldService:Near(player,"Apothecary",15) or self.S.DuelService:IsBusy(player) then return end
        if action=="BuyHealth" then
            if d.Gilders<50 then return self.S.NetworkService:Notice(player,"A Health Draught costs 50 Gilders.") end
            d.Gilders=d.Gilders-50; d.Inventory["Health Draught"]=(d.Inventory["Health Draught"] or 0)+1
        elseif action=="BrewHealth" then
            if (d.Inventory["Thorn Barb"] or 0)<1 or (d.Inventory["Spider Silk"] or 0)<1 then return self.S.NetworkService:Notice(player,"You need one Thorn Barb and one Spider Silk.") end
            d.Inventory["Thorn Barb"]=d.Inventory["Thorn Barb"]-1; d.Inventory["Spider Silk"]=d.Inventory["Spider Silk"]-1
            d.Inventory["Health Draught"]=(d.Inventory["Health Draught"] or 0)+1
        else return end
        self.S.ProgressionService:Refresh(player); self.S.NetworkService:Notice(player,"Health Draught added to your bag.")
    end
    self.S.NetworkService.Handlers.UseItem=function(player,id)
        local d=self.S.PlayerDataService:Get(player); local s=self.S.CombatService.States[player]
        if type(id)~="string" or not d or not self.S.CombatService:CanAct(s) or self.S.DuelService:IsBusy(player) or (d.Inventory[id] or 0)<1 then return end
        if id=="Health Draught" then
            if os.clock()<(self.PotionCooldowns[player] or 0) then return self.S.NetworkService:Notice(player,"Potions share a 30-second cooldown.") end
            if s.Humanoid.Health>=s.Humanoid.MaxHealth then return self.S.NetworkService:Notice(player,"Your health is already full.") end
            self.PotionCooldowns[player]=os.clock()+30; d.Inventory[id]=d.Inventory[id]-1
            task.spawn(function()
                for _=1,4 do task.wait(1); if self.S.CombatService.States[player]~=s or s.Humanoid.Health<=0 or self.S.DuelService:IsBusy(player) then return end; self.S.CombatService:Heal(player,s,s.Humanoid.MaxHealth*0.1) end
            end)
        elseif id=="Frigora Tome" or id=="Somnara Tome" then
            if self.S.ProgressionService:Learn(player,id:gsub(" Tome$",""),false) then d.Inventory[id]=d.Inventory[id]-1
            else return self.S.NetworkService:Notice(player,"You must meet the spell's level requirement and not already know it.") end
        else return end
        self.S.ProgressionService:Refresh(player)
    end
    self.S.NetworkService.Handlers.Respec=function(player)
        local d=self.S.PlayerDataService:Get(player)
        if not d or not self.S.WorldService:Near(player,"Library",15) or self.S.DuelService:IsBusy(player) then return end
        local day=math.floor(os.time()/86400)
        if d.LastRespec==day then return self.S.NetworkService:Notice(player,"Your next free respec is available tomorrow (UTC).") end
        d.LastRespec=day; d.Attributes={Power=0,Focus=0,Vitality=0,Agility=0,Unspent=(d.Level-1)*2}
        self.S.CombatService:UpdateStats(player,false); self.S.ProgressionService:Refresh(player)
    end
    self.S.NetworkService.Handlers.TalentReset=function(player)
        local d=self.S.PlayerDataService:Get(player)
        if not d or not self.S.WorldService:Near(player,"Library",15) or self.S.DuelService:IsBusy(player) then return end
        local day=math.floor(os.time()/86400)
        if d.LastTalentReset==day then return self.S.NetworkService:Notice(player,"Your next free skill reset is available tomorrow (UTC).") end
        d.LastTalentReset=day; d.Talents={}
        self.S.CombatService:UpdateStats(player,false); self.S.ProgressionService:Refresh(player)
        self.S.NetworkService:Notice(player,"All skill points refunded.")
    end
    for i=1,3 do
        local model=Instance.new("Model"); model.Name="Training Dummy"
        local root=Instance.new("Part"); root.Name="HumanoidRootPart"; root.Size=Vector3.new(3,5,2); root.Position=Vector3.new(156+(i-1)*9,3,-10)
        root.Anchored=true; root.Material=Enum.Material.Wood; root.Color=Color3.fromRGB(155,118,75); root.Parent=model; model.PrimaryPart=root
        local hum=Instance.new("Humanoid"); hum.RequiresNeck=false; hum.MaxHealth=100000; hum.Health=100000; hum.DisplayDistanceType=Enum.HumanoidDisplayDistanceType.None; hum.Parent=model
        model.Parent=self.S.WorldService.Targets; self.S.CombatService:Register(model,{Dummy=true})
    end
    for i=1,3 do
        local chest=workspace.Map:FindFirstChild("RuneChest"..i,true); if chest then chest:SetAttribute("ChestId","Chest"..i) end
    end
    Players.PlayerRemoving:Connect(function(player) self.PotionCooldowns[player]=nil end)
end
return I
