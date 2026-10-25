local Players=game:GetService("Players")
local Http=game:GetService("HttpService")
local RS=game:GetService("ReplicatedStorage")
local Config=require(RS.Shared.Config)
local Spells=require(RS.Shared.SpellData)
local Gesture=require(RS.Shared.Gesture)
local L={}
function L:Init(services) self.S=services; self.Lessons={}; self.Started=os.clock() end
function L:Schedule()
    local elapsed=os.clock()-self.Started; local cycle=math.floor(elapsed/Config.ClassInterval)
    return {Subject=Config.Subjects[cycle % #Config.Subjects+1],Seconds=math.ceil(Config.ClassInterval-elapsed%Config.ClassInterval)}
end
function L:Cancel(player)
    local lesson=self.Lessons[player]; if not lesson then return end
    if lesson.Targets then for _,target in ipairs(lesson.Targets) do self.S.CombatService.Targets[target.Model]=nil; target.Model:Destroy() end end
    self.Lessons[player]=nil
end
function L:Begin(player,school)
    local d=self.S.PlayerDataService:Get(player); local teacher=Config.Teachers[school]
    if not d or not d.HasWand or d.House=="" then return self.S.NetworkService:Notice(player,"Receive a wand and choose your house first.") end
    if not teacher or not self.S.WorldService:Near(player,teacher.Anchor,15) or self.S.DuelService:IsBusy(player) then return end
    self:Cancel(player)
    local list={}
    for _,spell in pairs(Spells) do if spell.School==school and spell.Implemented and not spell.Story and spell.UnlockLevel<=d.Level then list[#list+1]=spell end end
    table.sort(list,function(a,b) return a.UnlockLevel<b.UnlockLevel end)
    local chosen
    for _,spell in ipairs(list) do if not d.Spells[spell.Id] then chosen=spell; break end end
    chosen=chosen or list[#list] or Spells.Scintara
    local index=math.random(1,99)
    local lesson={Token=Http:GenerateGUID(false),Spell=chosen.Id,School=school,Index=index,Started=os.clock(),Phase="Gesture",Hits=0,Targets={}}
    self.Lessons[player]=lesson
    self.S.NetworkService.UI:FireClient(player,"Lesson",{Token=lesson.Token,Spell=chosen.Id,Path=Gesture.Path(index),Teacher=teacher.Name})
end
function L:Submit(player,token,points)
    local l=self.Lessons[player]
    if not l or type(token)~="string" or token~=l.Token or l.Phase~="Gesture" then return end
    if os.clock()-l.Started<1.5 or os.clock()-l.Started>90 or not self.S.WorldService:Near(player,Config.Teachers[l.School].Anchor,22) then return end
    local score=Gesture.Score(points,Gesture.Path(l.Index))
    if score<70 then self.S.NetworkService.UI:FireClient(player,"GestureResult",{Pass=false,Score=score}); return end
    l.Phase="Test"; l.Started=os.clock()
    local marker=self.S.WorldService:Anchor(Config.Teachers[l.School].Anchor)
    for i=1,5 do
        local model=Instance.new("Model"); model.Name="Lesson target"
        local part=Instance.new("Part"); part.Name="HumanoidRootPart"; part.Shape=Enum.PartType.Ball; part.Size=Vector3.new(2.5,2.5,2.5)
        part.Anchored=true; part.CanCollide=false; part.Material=Enum.Material.Neon; part.Color=Color3.fromRGB(117,216,201)
        local pos=marker.Position+Vector3.new((i-3)*5,5,15); part.Position=pos; part.Parent=model; model.PrimaryPart=part
        local hum=Instance.new("Humanoid"); hum.RequiresNeck=false; hum.DisplayDistanceType=Enum.HumanoidDisplayDistanceType.None; hum.Parent=model
        model:SetAttribute("LessonOwner",player.UserId); model.Parent=self.S.WorldService.Targets
        local target=self.S.CombatService:Register(model,{Dummy=true,LessonOwner=player,Home=pos,Index=i})
        l.Targets[#l.Targets+1]=target
    end
    self.S.NetworkService.UI:FireClient(player,"GestureResult",{Pass=true,Score=score})
    self.S.NetworkService:Notice(player,"Rune passed! Close the panel and hit your five teal targets with Scintara.")
end
function L:TargetHit(player,target)
    local l=self.Lessons[player]
    if not l or l.Phase~="Test" or target.Hit or os.clock()-l.Started>120 then return end
    if not self.S.WorldService:Near(player,Config.Teachers[l.School].Anchor,55) then return end
    target.Hit=true; target.Root.CanQuery=false; target.Root.Transparency=1
    l.Hits=l.Hits+1
    self.S.NetworkService:Notice(player,"Class test: "..l.Hits.." / 5")
    if l.Hits==5 then
        local d=self.S.PlayerDataService:Get(player); if not d then self:Cancel(player); return end
        local school,spell=l.School,l.Spell
        self:Cancel(player)
        local learned=self.S.ProgressionService:Learn(player,spell,false)
        local rewardReady=os.time()-(d.LessonRewards[school] or 0)>=Config.LessonRewardCooldown
        if rewardReady then
            d.LessonRewards[school]=os.time()
            self.S.ProgressionService:Award(player,80+20*d.Level,30); self.S.ProgressionService:HousePoints(player,5)
            if not learned and d.Spells[spell] then for _=1,5 do self.S.ProgressionService:Hit(player,spell) end end
        end
        self.S.ProgressionService:Event(player,"Class")
        self.S.NetworkService:Notice(player,rewardReady and "Class passed! +5 House Points" or "Class passed! Repeat rewards recharge every two minutes.")
    end
end
function L:Start()
    self.S.NetworkService:Bind("Gesture",2,3,function(player,token,points) self:Submit(player,token,points) end)
    Players.PlayerRemoving:Connect(function(player) self:Cancel(player) end)
    task.spawn(function()
        while true do
            task.wait(0.1)
            for player,l in pairs(self.Lessons) do
                if os.clock()-l.Started>(l.Phase=="Test" and 120 or 90) then self:Cancel(player); self.S.NetworkService:Notice(player,"Lesson expired. Visit your professor to retry.")
                elseif l.Phase=="Test" then
                    for _,target in ipairs(l.Targets) do if not target.Hit then target.Root.Position=target.Home+Vector3.new(math.sin(os.clock()*1.4+target.Index)*1.5,math.cos(os.clock()+target.Index)*0.5,0) end end
                end
            end
        end
    end)
end
return L
