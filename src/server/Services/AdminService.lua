local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
local RS=game:GetService("ReplicatedStorage")
local Config=require(RS.Shared.Config)
local Spells=require(RS.Shared.SpellData)
local Quests=require(RS.Shared.QuestData)
local Wands=require(RS.Shared.WandData)
local F=require(RS.Shared.Formulas)
-- Testing tools for the admin panel (P). Studio playtests always qualify; on a live server only the
-- experience owner and the user ids listed in ADMINS do. Every command is checked here, never on the client.
local ADMINS={}
local ITEMS={"Health Draught","Frigora Tome","Somnara Tome","Thorn Barb","Spider Silk","Wisp Essence","Moonhowler Fang","Heartwood","Widow's Bite trophy"}
local A={}
function A:Init(services) self.S=services end
function A:IsAdmin(player)
    return RunService:IsStudio() or ADMINS[player.UserId]==true
        or (game.CreatorType==Enum.CreatorType.User and player.UserId==game.CreatorId)
end
-- Learns a spell whatever the player's level, filling an empty slot the way ProgressionService:Learn does.
function A:Teach(d,id)
    local sp=Spells[id]; if not sp or not sp.Implemented or d.Spells[id] then return end
    d.Spells[id]={Mastery=1,Hits=0}
    if id=="Scintara" or id=="Aegara" then return end
    for _,value in pairs(d.Loadout) do if value==id then return end end
    for i=1,4 do local key="Slot"..i; if d.Loadout[key]=="" then d.Loadout[key]=id; return end end
end
-- What Oakhart's first visit grants: the right to hold a wand and the three starter spells.
function A:Starter(d)
    d.HasWand=true
    for _,id in ipairs({"Scintara","Aegara","Glimmora"}) do self:Teach(d,id) end
end
function A:SetLevel(player,d,level)
    if level<d.Level then d.Attributes={Power=0,Focus=0,Vitality=0,Agility=0,Unspent=(level-1)*2}; d.Talents={}
    else d.Attributes.Unspent=d.Attributes.Unspent+(level-d.Level)*2 end
    d.Level=level; d.XP=0
    self.S.CombatService:UpdateStats(player,true)
end
local commands={}
function commands.Level(self,player,d,level)
    if not F.Finite(level) or level%1~=0 then return end
    self:SetLevel(player,d,math.clamp(level,1,Config.LevelCap))
    return "Level "..d.Level.." · attribute and skill points updated"
end
function commands.XP(self,player,d) self.S.ProgressionService:Award(player,1000,0); return "+1,000 XP" end
function commands.Gilders(self,player,d) d.Gilders=d.Gilders+1000; return "+1,000 Gilders" end
function commands.Items(self,player,d)
    for _,item in ipairs(ITEMS) do d.Inventory[item]=(d.Inventory[item] or 0)+5 end
    return "Added 5 of every potion, tome and material to your bag"
end
function commands.Refill(self,player,d)
    self.S.CombatService:UpdateStats(player,true)
    local s=self.S.CombatService.States[player]; if s then s.Cooldowns={}; s.Stamina=100 end
    return "Health, mana and stamina refilled · cooldowns reset"
end
function commands.FreeCast(self,player,d)
    local on=not player:GetAttribute("FreeCast"); player:SetAttribute("FreeCast",on)
    return on and "Free casting ON · no mana cost or cooldowns" or "Free casting OFF"
end
function commands.LearnAll(self,player,d)
    self:Starter(d)
    for id in pairs(Spells) do self:Teach(d,id) end
    return "Every spell is learned. Assign them with K or the slot buttons here."
end
function commands.Mastery(self,player,d)
    for _,s in pairs(d.Spells) do s.Mastery=5; s.Hits=math.max(s.Hits,300) end
    return "All learned spells are at Mastery 5"
end
function commands.Assign(self,player,d,pick)
    if type(pick)~="table" or type(pick.Spell)~="string" or type(pick.Slot)~="string" or not Spells[pick.Spell] then return end
    self:Starter(d); self:Teach(d,pick.Spell)
    self.S.NetworkService.Handlers.Loadout(player,pick.Slot,pick.Spell)
end
function commands.Wand(self,player,d,rarity)
    if type(rarity)~="string" or not Wands.Rarities[rarity] then return end
    self:Starter(d)
    local wand=Wands.Roll(rarity)
    if not self.S.WandService:Grant(player,wand) then return "Your wand case is full. Discard a wand in your bag (B) first." end
    return "Added to your bag: "..Wands.Name(wand)
end
function commands.Named(self,player,d,id)
    if type(id)~="string" or not Wands.Named[id] then return end
    self:Starter(d)
    self.S.WandService:GrantNamed(player,id,"Added to your bag: %s")
end
function commands.House(self,player,d,house)
    if type(house)~="string" or not Config.Houses[house] then return end
    d.House=house; self.S.ProgressionService:Event(player,"Sorted"); self.S.CombatService:UpdateStats(player,true)
    return "You now belong to "..house.." · "..Config.Houses[house].Perk
end
function commands.Waystones(self,player,d)
    for id in pairs(Config.Waystones) do d.Waystones[id]=true end
    return "Every Waystone is attuned"
end
-- Jumps the story to quest `index` (one past the last means finished), completing everything before it.
function commands.Quest(self,player,d,index)
    if not F.Finite(index) or index%1~=0 or index<1 or index>#Quests+1 then return end
    if index>1 then
        self:Starter(d)
        if #d.Wands==0 then self.S.WandService:Grant(player,Wands.Roll("Common")) end
    end
    d.QuestDone={}; d.Quest=index; d.QuestProgress=0
    for i,q in ipairs(Quests) do
        if i<index then
            d.QuestDone[q.Id]=true
            if q.Id=="Seal" then d.SealDefeated=true end
            if q.Id=="Vexweave" then d.BossDefeated=true end
            if q.Wand and not d.WandRewards[q.Wand] then
                d.WandRewards[q.Wand]=true
                self.S.WandService:GrantNamed(player,q.Wand,"Quest reward: %s. Equip it from your bag.")
            end
        end
    end
    local q=Quests[index]
    return q and "Story moved to: "..q.Title or "The alpha story is complete"
end
-- Lands beside a marker (or a Waystone's travel point) on whatever floor is there.
function commands.Teleport(self,player,d,name)
    if type(name)~="string" then return end
    local target
    local point=Config.Waystones[name]
    if point then target=Vector3.new(point[1],point[2],point[3]) else
        local marker=self.S.WorldService:Anchor(name); if not marker then return end
        -- Cast down from head height, not from the sky, so indoor markers land on the floor and not the roof.
        local above=marker.Position+Vector3.new(0,4,7)
        local params=RaycastParams.new(); params.FilterType=Enum.RaycastFilterType.Exclude
        params.FilterDescendantsInstances={player.Character,workspace.Markers}
        local hit=workspace:Raycast(above,Vector3.new(0,-20,0),params)
        target=hit and hit.Position+Vector3.new(0,3,0) or marker.Position+Vector3.new(0,3,7)
    end
    self.S.WorldService:Teleport(player,target)
end
function A:Start()
    local function mark(player) if self:IsAdmin(player) then player:SetAttribute("Admin",true) end end
    Players.PlayerAdded:Connect(mark)
    for _,player in ipairs(Players:GetPlayers()) do mark(player) end
    self.S.NetworkService.Handlers.Admin=function(player,command,arg)
        local d=self.S.PlayerDataService:Get(player); local fn=type(command)=="string" and commands[command]
        if not d or not fn or not self:IsAdmin(player) then return end
        local message=fn(self,player,d,arg)
        self.S.ProgressionService:Refresh(player)
        if message then self.S.NetworkService:Notice(player,message) end
    end
end
return A
