local Players=game:GetService("Players")
local F=require(game:GetService("ReplicatedStorage").Shared.Formulas)
local D={}
function D:Init(services) self.S=services; self.Invites={}; self.Matches={}; self.Rewards={} end
function D:IsBusy(player) return self.Matches[player]~=nil end
function D:IsCounting(player) local m=self.Matches[player]; return m and os.clock()<m.Starts end
function D:CanDamage(a,b)
    local m=self.Matches[a]
    return m~=nil and self.Matches[b]==m and a~=b and not m.Ended and os.clock()>=m.Starts
end
function D:Invite(player,userId)
    if not F.Finite(userId) or userId%1~=0 or self:IsBusy(player) then return end
    local other=Players:GetPlayerByUserId(userId); local a=self.S.CombatService.States[player]; local b=other and self.S.CombatService.States[other]
    if not a or not b or a.Humanoid.Health<=0 or b.Humanoid.Health<=0 or other==player or self:IsBusy(other) then return end
    if not self.S.WorldService:Near(player,"Duelmaster",35) or not self.S.WorldService:Near(other,"Duelmaster",35) then return self.S.NetworkService:Notice(player,"Both duelists must stand near Duelmaster Vey.") end
    local invite=self.Invites[other]
    if invite and os.clock()<invite.Expires then return self.S.NetworkService:Notice(player,"That student already has an invitation.") end
    self.Invites[other]={From=player,Expires=os.clock()+20}
    self.S.NetworkService.UI:FireClient(other,"DuelInvite",{Name=player.DisplayName,UserId=player.UserId})
    self.S.NetworkService:Notice(player,"Duel invitation sent.")
end
function D:Respond(player,accept)
    local invite=self.Invites[player]; self.Invites[player]=nil
    if type(accept)~="boolean" or not invite or invite.Expires<os.clock() or not accept then return end
    if self.Active and not self.Active.Ended then return self.S.NetworkService:Notice(player,"The dueling platform is occupied. Try again after this match.") end
    local other=invite.From
    if not other.Parent or self:IsBusy(player) or self:IsBusy(other) then return end
    if not self.S.WorldService:Near(player,"Duelmaster",35) or not self.S.WorldService:Near(other,"Duelmaster",35) then return end
    local a=self.S.CombatService.States[player]; local b=self.S.CombatService.States[other]
    if not a or not b or a.Humanoid.Health<=0 or b.Humanoid.Health<=0 then return end
    local m={Players={player,other},Starts=os.clock()+3,Ends=os.clock()+183,Positions={[player]=a.Root.Position,[other]=b.Root.Position}}
    self.Active=m
    self.Matches[player]=m; self.Matches[other]=m
    for i,p in ipairs(m.Players) do
        self.S.ClassService:Cancel(p)
        local s=self.S.CombatService.States[p]; s.Humanoid.Health=s.Humanoid.MaxHealth; s.Mana=s.MaxMana; s.Stamina=100; s.Statuses={}; s.Shield=0; s.Cooldowns={}; s.InvulnerableUntil=m.Starts
        self.S.WorldService:Teleport(p,Vector3.new(240,5,i==1 and -120 or -170))
        self.S.NetworkService.UI:FireClient(p,"DuelStart",3)
    end
end
function D:Finish(m,winner)
    if m.Ended then return end; m.Ended=true
    if self.Active==m then self.Active=nil end
    for _,p in ipairs(m.Players) do
        self.Matches[p]=nil
        local s=self.S.CombatService.States[p]
        if s and p.Parent then
            s.Statuses={}; s.Shield=0; s.Cooldowns={}; s.Humanoid.Health=s.Humanoid.MaxHealth; s.Mana=s.MaxMana; s.InvulnerableUntil=os.clock()+5
            self.S.WorldService:Teleport(p,m.Positions[p])
            self.S.NetworkService:Notice(p,winner and (winner==p and "Duel won!" or "Duel lost. Train, adapt, return.") or "Duel ended in a draw.")
        end
    end
    if winner then
        local d=self.S.PlayerDataService:Get(winner)
        if d then
            d.DuelWins=d.DuelWins+1
            local rewards=self.Rewards[winner] or {Hour=math.floor(os.time()/3600),Count=0}; self.Rewards[winner]=rewards
            if rewards.Hour~=math.floor(os.time()/3600) then rewards.Hour=math.floor(os.time()/3600); rewards.Count=0 end
            if rewards.Count<10 then
                rewards.Count=rewards.Count+1; self.S.ProgressionService:HousePoints(winner,5)
                local perk=d.House=="Nightfang" and 1.05 or 1
                self.S.ProgressionService:Award(winner,math.floor(80*perk),math.floor(20*perk))
            end
            self.S.ProgressionService:Refresh(winner)
        end
    end
end
function D:Defeated(player)
    local m=self.Matches[player]; if not m then return end
    local winner=m.Players[1]==player and m.Players[2] or m.Players[1]
    self:Finish(m,winner)
end
function D:Start()
    self.S.NetworkService.Handlers.DuelInvite=function(player,id) self:Invite(player,id) end
    self.S.NetworkService.Handlers.DuelRespond=function(player,accept) self:Respond(player,accept) end
    Players.PlayerRemoving:Connect(function(player) self:Defeated(player); self.Invites[player]=nil; self.Rewards[player]=nil end)
    task.spawn(function()
        while true do
            task.wait(1)
            for player,m in pairs(self.Matches) do
                local root=self.S.WorldService:Root(player)
                if os.clock()>m.Ends then self:Finish(m,nil)
                elseif root and (math.abs(root.Position.X-240)>39 or math.abs(root.Position.Z+145)>45) then self:Defeated(player) end
            end
            for player,inv in pairs(self.Invites) do if not player.Parent or not inv.From.Parent or os.clock()>inv.Expires then self.Invites[player]=nil end end
        end
    end)
end
return D
