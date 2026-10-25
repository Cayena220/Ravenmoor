local RS=game:GetService("ReplicatedStorage")
local Wands=require(RS.Shared.WandData)
local WandModel=require(RS.Shared.WandModel)
local Quests=require(RS.Shared.QuestData)
local F=require(RS.Shared.Formulas)
local W={}
function W:Init(services) self.S=services end
-- Names plus a case revision protect selections even when two wands look identical.
function W:Valid(d,index,name,revision)
    return (revision==nil or revision==(d.WandRevision or 0)) and F.Finite(index) and index%1==0 and index>=1 and index<=#d.Wands and (name==nil or Wands.Name(d.Wands[index])==name)
end
-- Replaces the wand model in the character's hand with the equipped wand.
function W:Attach(player)
    local d=self.S.PlayerDataService:Get(player); local s=self.S.CombatService.States[player]
    if not d or not s then return end
    local old=s.Model:FindFirstChild("RavenmoorWand"); if old then old:Destroy() end
    local wand=d.Wands[d.EquippedWand]; if not d.HasWand or not wand then return end
    local hand=s.Model:FindFirstChild("RightHand") or s.Model:FindFirstChild("Right Arm"); if not hand then return end
    local model=WandModel.Build(wand,hand.CFrame*CFrame.new(0,-0.2,0),false); model.Name="RavenmoorWand"
    local weld=Instance.new("WeldConstraint"); weld.Part0=hand; weld.Part1=model.PrimaryPart; weld.Parent=model.PrimaryPart
    model.Parent=s.Model
end
function W:Use(player,index)
    local d=self.S.PlayerDataService:Get(player)
    d.WandRevision=(d.WandRevision or 0)+1
    d.EquippedWand=index; d.Wand=Wands.Label(d.Wands[index])
    local s=self.S.CombatService.States[player]; if s then s.StaticHits=0 end
    self:Attach(player); self.S.CombatService:UpdateStats(player,false); self.S.ProgressionService:Refresh(player)
end
-- Adds a wand to the case, equipping it when it is the first. Returns false when the case is full.
function W:Grant(player,wand)
    local d=self.S.PlayerDataService:Get(player)
    if not d or #d.Wands>=Wands.Capacity then return false end
    d.WandRevision=(d.WandRevision or 0)+1
    d.Wands[#d.Wands+1]=wand
    if d.EquippedWand==0 then self:Use(player,#d.Wands) else self.S.ProgressionService:Refresh(player) end
    return true
end
function W:Reward(player,rarity)
    local wand=Wands.Roll(rarity)
    if self:Grant(player,wand) then self.S.NetworkService:Notice(player,"A wand was left behind: "..Wands.Name(wand).."!")
    else self.S.NetworkService:Notice(player,"Your wand case is full. Discard a wand in your bag to collect more.") end
end
-- Gives a named wand; while the case is full, Oakhart holds it instead. `message` formats the wand's name.
function W:GrantNamed(player,id,message)
    local d=self.S.PlayerDataService:Get(player)
    if not d or not Wands.Named[id] then return false end
    local wand=Wands.Make(id)
    if self:Grant(player,wand) then self.S.NetworkService:Notice(player,message:format(Wands.Name(wand))); return true end
    d.WandsHeld[#d.WandsHeld+1]=id
    self.S.NetworkService:Notice(player,"Your wand case is full. Oakhart will keep your "..Wands.Named[id].Title.." until you make room.")
    return false
end
-- At Oakhart's: queues quest wands earned before they existed, then hands over held wands while the case has room.
function W:Deliver(player)
    local d=self.S.PlayerDataService:Get(player); if not d then return end
    for _,q in ipairs(Quests) do
        if q.Wand and d.QuestDone[q.Id] and not d.WandRewards[q.Wand] then d.WandRewards[q.Wand]=true; d.WandsHeld[#d.WandsHeld+1]=q.Wand end
    end
    while #d.WandsHeld>0 and #d.Wands<Wands.Capacity do
        local wand=Wands.Make(table.remove(d.WandsHeld,1))
        self:Grant(player,wand); self.S.NetworkService:Notice(player,"Oakhart hands you your "..Wands.Name(wand)..". Equip it from your bag.")
    end
end
function W:Commission(player,id)
    local d=self.S.PlayerDataService:Get(player); local named=Wands.Named[id]; local recipe=named and named.Recipe
    if not d or not recipe or not d.HasWand or not self.S.WorldService:Near(player,"Oakhart",15) or self.S.DuelService:IsBusy(player) then return end
    if #d.Wands>=Wands.Capacity then return self.S.NetworkService:Notice(player,"Your wand case is full. Discard a wand in your bag first.") end
    if d.Level<recipe.Level then return self.S.NetworkService:Notice(player,named.Title.." is commissioned from level "..recipe.Level..".") end
    for item,need in pairs(recipe.Items) do
        if (d.Inventory[item] or 0)<need then return self.S.NetworkService:Notice(player,named.Title.." needs "..item.." ×"..need..".") end
    end
    if d.Gilders<recipe.Gilders then return self.S.NetworkService:Notice(player,named.Title.." costs "..recipe.Gilders.." Gilders.") end
    for item,need in pairs(recipe.Items) do d.Inventory[item]=d.Inventory[item]-need end
    d.Gilders=d.Gilders-recipe.Gilders
    local wand=Wands.Make(id); self:Grant(player,wand)
    self.S.NetworkService:Notice(player,"Oakhart hands you a "..Wands.Name(wand)..". Equip it from your bag.")
end
function W:Equip(player,index,name,revision)
    local d=self.S.PlayerDataService:Get(player); local s=self.S.CombatService.States[player]
    if not d or not s or not self:Valid(d,index,name,revision) or index==d.EquippedWand then return end
    if self.S.DuelService:IsBusy(player) or os.clock()-s.LastCombat<5 then return self.S.NetworkService:Notice(player,"Wands can't be swapped during combat.") end
    self:Use(player,index); self.S.NetworkService:Notice(player,"Equipped your "..Wands.Name(d.Wands[index]))
end
function W:Discard(player,index,name,revision)
    local d=self.S.PlayerDataService:Get(player)
    if not d or not self:Valid(d,index,name,revision) or index==d.EquippedWand then return end
    d.WandRevision=(d.WandRevision or 0)+1
    local wand=table.remove(d.Wands,index)
    if d.EquippedWand>index then d.EquippedWand=d.EquippedWand-1 end
    self.S.NetworkService:Notice(player,"Discarded your "..Wands.Name(wand)); self.S.ProgressionService:Refresh(player)
end
function W:Buy(player)
    local d=self.S.PlayerDataService:Get(player)
    if not d or not d.HasWand or not self.S.WorldService:Near(player,"Oakhart",15) or self.S.DuelService:IsBusy(player) then return end
    if #d.Wands>=Wands.Capacity then return self.S.NetworkService:Notice(player,"Your wand case is full. Discard a wand in your bag first.") end
    if d.Gilders<Wands.Price then return self.S.NetworkService:Notice(player,"A commissioned wand costs "..Wands.Price.." Gilders.") end
    d.Gilders=d.Gilders-Wands.Price
    local wand=Wands.Roll(); self:Grant(player,wand)
    self.S.NetworkService:Notice(player,"Oakhart hands you a "..Wands.Name(wand)..". Equip it from your bag.")
end
function W:Start()
    local handlers=self.S.NetworkService.Handlers
    handlers.EquipWand=function(player,index,selection)
        if type(selection)=="table" and type(selection.Name)=="string" and F.Finite(selection.Revision) then self:Equip(player,index,selection.Name,selection.Revision) end
    end
    handlers.DiscardWand=function(player,index,selection)
        if type(selection)=="table" and type(selection.Name)=="string" and F.Finite(selection.Revision) then self:Discard(player,index,selection.Name,selection.Revision) end
    end
    handlers.BuyWand=function(player) self:Buy(player) end
    handlers.CommissionWand=function(player,id) if type(id)=="string" then self:Commission(player,id) end end
end
return W
