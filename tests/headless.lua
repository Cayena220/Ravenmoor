-- Runs outside Studio against small API fakes. Does not claim engine integration coverage.
local total=0
local function check(value,message) total=total+1; assert(value,message or ("check "..total.." failed")) end
local function near(a,b) return math.abs(a-b)<0.00001 end
math.clamp=math.clamp or function(x,a,b) return math.max(a,math.min(b,x)) end
local V={}; V.__index=function(v,key)
    if key=="Magnitude" then return math.sqrt(v.X*v.X+v.Y*v.Y+v.Z*v.Z) end
    if key=="Unit" then local m=v.Magnitude; return setmetatable({X=v.X/m,Y=v.Y/m,Z=v.Z/m},V) end
    return V[key]
end
Vector3={new=function(x,y,z) return setmetatable({X=x,Y=y,Z=z},V) end}
V.__add=function(a,b) return Vector3.new(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end
V.__sub=function(a,b) return Vector3.new(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end
V.__mul=function(a,b) if type(b)=="number" then return Vector3.new(a.X*b,a.Y*b,a.Z*b) end; return Vector3.new(a.X*b.X,a.Y*b.Y,a.Z*b.Z) end
function V:Dot(b) return self.X*b.X+self.Y*b.Y+self.Z*b.Z end
Vector3.zero=Vector3.new(0,0,0); Vector3.one=Vector3.new(1,1,1)
typeof=function(v) return getmetatable(v)==V and "Vector3" or type(v) end
local queued={}
task={delay=function(_,fn) queued[#queued+1]=fn end,spawn=function() end,defer=function(fn) queued[#queued+1]=fn end,wait=function() end}
warn=function() end
local function fire() end
local event={FireClient=fire,FireAllClients=fire}
local shared={}
for _,name in ipairs({"Config","Formulas","Gesture","SpellData","QuestData","MonsterData","WorldPoints","WandData","WandModel","SkillData"}) do shared[name]=ROOT.."/src/shared/"..name..".lua" end
local services={ReplicatedStorage={Shared=shared},Players={GetPlayers=function() return {} end},RunService={IsStudio=function() return true end},
    HttpService={GenerateGUID=function() return "session-test" end},TextChatService={},ServerStorage={LootTables=ROOT.."/src/serverstorage/LootTables.lua"}}
game={JobId="test-server",GetService=function(_,name) return services[name] or {} end}
workspace={Markers={}}
require=function(path) return assert(loadfile(path))() end
local F=require(shared.Formulas); local G=require(shared.Gesture); local spells=require(shared.SpellData)
check(F.XP(1)==100,"level 1 XP"); check(F.XP(10)==3162,"level 10 XP"); check(F.XP(20)==8944,"level 20 XP")
check(F.Monster(20,"Boss").HP==8250,"Vexweave HP"); check(F.Monster(18,"Elite").HP==1500,"Rotbark HP")
check(F.Elo(1000,1000,0,1)==1024,"placement Elo"); check(F.Elo(1000,1000,10,0)==984,"normal Elo")
local count,implemented=0,0
for _,spell in pairs(spells) do count=count+1; if spell.Implemented then implemented=implemented+1; check(spell.UnlockLevel<=20,"launch spell gate") end end
check(count==29,"29 reference spells"); check(implemented==19,"19 executable spells")
for _,case in ipairs({{0,1},{24,1},{25,2},{74,2},{75,3},{149,3},{150,4},{299,4},{300,5}}) do check(F.Mastery(case[1])==case[2],"mastery threshold") end
check(not F.Finite(0/0),"reject NaN"); check(not F.Finite(math.huge),"reject infinity"); check(not F.Finite("1"),"reject string")
local data={Level=10,House="",Attributes={Power=10,Focus=0,Vitality=0,Agility=0,Unspent=0},Spells={Flamara={Mastery=2}},Loadout={Slot1="Flamara"}}
check(near(F.Power(18,data,spells.Flamara,false),39.0096),"plan formula example")
check(near(F.Power(18,data,spells.Flamara,true),42.91056),"spoken bonus")
check(F.Stats(data).HP==200,"health formula"); check(F.Stats(data).Mana==120,"mana formula")
data.House="Stoneroot"; check(F.Stats(data).HP==210,"house health")
data.Attributes.Agility=100; check(near(F.Stats(data).Speed,18.4),"speed cap"); check(near(F.Stats(data).Crit,0.25),"crit cap")
data.House=""; data.Attributes.Agility=0
local Wands=require(shared.WandData); local Skills=require(shared.SkillData)
local rare={Wood="Rowan",Core="Emberplume",Rarity="Rare"}
check(Wands.Valid(rare) and not Wands.Valid({Wood="Oak",Core="Emberplume",Rarity="Rare"}),"wand catalogue validation")
check(Wands.Describe(rare)=="-6% cooldowns  ·  +10% Fire damage","rarity scales wand bonuses")
local armed={Level=10,House="",Attributes={Power=10,Focus=0,Vitality=0,Agility=0,Unspent=0},Spells={Flamara={Mastery=2}},Wands={rare},EquippedWand=1,Talents={}}
check(near(F.Power(18,armed,spells.Flamara,false),39.0096*1.1),"wand core boosts its element")
check(near(F.Cooldown(spells.Flamara,armed),5*0.94),"wand wood shortens cooldowns")
armed.EquippedWand=0; check(near(F.Cooldown(spells.Flamara,armed),5),"unequipped wands grant nothing")
armed.Wands={{Wood="Silverbirch",Core="Moonmane",Rarity="Common"}}; armed.EquippedWand=1; armed.Talents={EfficientCasting=2}
check(near(F.ManaCost(spells.Flamara,armed),13.5),"wand and skills lower mana cost")
check(near(F.Duration(spells.Frigora,armed),2.12),"wand core extends effect duration")
local tough={Level=10,House="",Attributes={Power=0,Focus=0,Vitality=0,Agility=0,Unspent=0},Talents={Bulwark=1,SteadyStance=3}}
check(F.Stats(tough).HP==216 and near(F.Stats(tough).Guard,0.06),"skill tree health and guard")
local legacy={HasWand=true,Wand="Willow / Moonmane",Wands={},EquippedWand=0}; Wands.Sanitize(legacy)
check(#legacy.Wands==1 and legacy.Wands[1].Wood=="Willow" and legacy.EquippedWand==1,"old text wand becomes a bag item")
local messy={HasWand=true,Wand="",Wands={{Wood="Ash",Core="Frostfang",Rarity="Common"},{Wood="Nope"}},EquippedWand=7}; Wands.Sanitize(messy)
check(#messy.Wands==1 and messy.EquippedWand==1 and messy.Wand=="Ash / Frostfang","invalid saved wands are dropped")
local storm,hearth,widow=Wands.Make("Stormfork"),Wands.Make("Hearthroot"),Wands.Make("WidowsBite")
check(Wands.Valid(storm) and Wands.Valid(hearth) and Wands.Valid(widow),"named wands are valid")
check(not Wands.Valid({Wood="Ash",Core="Vexfang",Rarity="Epic",Named="WidowsBite"}) and not Wands.Valid({Wood="Rowan",Core="Stormglass",Rarity="Uncommon",Named="Nope"}),"named wands keep their parts")
check(Wands.Describe(storm)=="-4.5% cooldowns  ·  +7.5% Lightning damage\nStatic: every 4th Spark Bolt arcs to a second enemy","Stormfork effect line")
check(Wands.Describe(hearth):find("+10% mana regeneration  ·  +12% effect duration\n",1,true)==1,"Hearthroot effect line")
check(Wands.Describe(widow):find("+5% critical chance  ·  +15% Alteration effect duration\n",1,true)==1,"Widow's Bite effect line")
check(Wands.Name(widow)=="Widow's Bite · Epic Blackthorn wand" and Wands.Label(widow)=="Widow's Bite","named wand titles")
check(Wands.Length(widow)==2.4 and Wands.Length(storm)==2.0 and Wands.Length(rare)==2.0,"named length override")
local shopOnly=true
for _=1,300 do local w=Wands.Roll(); if w.Rarity=="Epic" or w.Wood=="Heartwood" or w.Core=="Vexfang" then shopOnly=false end end
check(shopOnly,"shop rolls never make named-only parts")
local named={Level=10,House="",Attributes={Power=0,Focus=0,Vitality=0,Agility=0,Unspent=0},Spells={},Wands={widow},EquippedWand=1,Talents={}}
check(near(F.Stats(named).Crit,0.1) and near(F.Duration(spells.Saxifra,named),1.725),"Widow's Bite crit and root duration")
check(Wands.Signature(named)=="VenomBite" and Wands.Signature({Wands={rare},EquippedWand=1})==nil,"equipped signature")
named.Wands={hearth}; check(near(F.Stats(named).ManaRegen,4.4) and near(F.Duration(spells.Somnara,named),3.36),"Hearthroot regen and duration")
local held={HasWand=true,Wand="",Wands={storm},EquippedWand=1,WandsHeld={"Stormfork","Nope"}}; Wands.Sanitize(held)
check(#held.WandsHeld==1 and held.Wand=="Stormfork","held wands are sanitized")
local student={Level=5,Talents={}}
check(Skills.CanLearn(student,"SearingFocus"),"tier one skill"); check(not Skills.CanLearn(student,"QuickenedHexes"),"tier two needs school points")
student.Talents.SearingFocus=3; check(not Skills.CanLearn(student,"SearingFocus"),"skill max rank"); check(Skills.CanLearn(student,"QuickenedHexes"),"tier two unlocks")
student.Talents.ThickWards=1; check(not Skills.CanLearn(student,"QuickenedHexes"),"skill points come from levels")
student.Level=1; Skills.Sanitize(student); check(next(student.Talents)==nil,"overspent tree is refunded")
for index=0,2 do
    local path=G.Path(index); local trace=G.Resample(path,100)
    check(G.Score(trace,path)>=95,"good gesture")
    local reverse={}; for i=#trace,1,-1 do reverse[#reverse+1]=trace[i] end
    check(G.Score(reverse,path)<70,"reversed gesture fails")
end
check(G.Score({{0/0,0}},G.Path(1))==0,"invalid gesture")
local still={}; for _=1,32 do still[#still+1]={0.5,0.5} end
check(G.Score(still,G.Path(1))==0,"stationary point fails")
local far={}; for _=1,20 do far[#far+1]={100,100} end
check(G.Score(far,G.Path(1))==0,"out of bounds gesture fails")

local C=require(ROOT.."/src/server/Services/CombatService.lua")
local N={Notice=fire,Sync=fire,FX=event,UI=event,CastReply=event,Handlers={},Allow=function() return true end}
local duel={allowed=false,CanDamage=function(self) return self.allowed end,IsBusy=function() return false end,IsCounting=function() return false end}
local profileData={}
local deps={NetworkService=N,DuelService=duel,PlayerDataService={Get=function(_,p) return profileData[p] end},
    MonsterService={Killed=fire},ProgressionService={Hit=fire,Event=fire}}
C:Init(deps); deps.CombatService=C
local player={Parent=true,UserId=7}; local other={Parent=true,UserId=9}
local function target(p)
    return {Player=p,Model={Parent=true},Humanoid={Health=110,MaxHealth=110},Root={Position=Vector3.zero},Statuses={},Shield=0,LastCombat=-100}
end
local t=target(other)
check(not C:CanDamage(player,t),"safe-zone PvP is rejected")
duel.allowed=true; check(C:CanDamage(player,t),"consented duel can hit"); check(not C:CanDamage(other,t),"cannot self-hit")
duel.allowed=false
local mob=target(nil); mob.Rank="Normal"
C:Status(mob,"Rooted",2,player); check(mob.CCCount==1,"first crowd control")
local now=os.clock(); C:Status(mob,"Silenced",2,player); check(mob.Statuses.Silenced.Until-now<1.01,"second CC half duration")
C:Status(mob,"Asleep",2,player); check(mob.Statuses.Asleep.Until-os.clock()<0.51,"third CC quarter duration")
C:Status(mob,"Stunned",2,player); check(not mob.Statuses.Stunned,"fourth CC immune")
local boss=target(nil); boss.Rank="Boss"; C:Status(boss,"Rooted",2,player); check(not boss.Statuses.Rooted,"boss CC immunity")
local shielded=target(nil); shielded.Shield=40
C:Damage(nil,shielded,25,nil); check(shielded.Humanoid.Health==110 and shielded.Shield==15,"shield absorbs first")
C:Damage(nil,shielded,30,nil); check(shielded.Humanoid.Health==95 and shielded.Shield==0,"shield overflow")
shielded.InvulnerableUntil=os.clock()+1
check(not C:Damage(nil,shielded,50,nil) and shielded.Humanoid.Health==95,"dodge protection")
local reflect=target(other); reflect.Statuses.Speculo={Until=os.clock()+1}; check(C:Has(reflect,"Speculo"),"ward status")

local S=require(ROOT.."/src/server/Services/SpellService.lua"); S:Init(deps)
local state=target(player); state.Mana=100; state.Cooldowns={}; state.BusyUntil=0; C.States[player]=state
data.HasWand=true; profileData[player]=data; data.Settings={SpokenCasting=true}
data.Loadout={Slot1="Flamara"}
local before=state.Mana
S:Cast(player,"Flamara",Vector3.new(0/0,0,0),false); check(state.Mana==before,"NaN aim rejected")
S:Cast(player,"Flamara",Vector3.new(math.huge,0,0),false); check(state.Mana==before,"infinite aim rejected")
S:Cast(player,"Animor",Vector3.new(0,0,20),false); check(state.Mana==before,"future spells rejected")
S:Cast(player,"Frigora",Vector3.new(0,0,20),false); check(state.Mana==before,"unlearned spell rejected")
S:Cast(player,"Flamara",Vector3.new(0,0,10000),false); check(state.Mana==before,"extreme aim rejected")
data.Loadout={}; S:Cast(player,"Flamara",Vector3.new(0,0,20),false); check(state.Mana==before,"unequipped spell rejected")
data.Loadout={Slot1="Flamara"}; S:Cast(player,"Flamara",Vector3.new(0,0,20),false)
check(state.Mana==85,"cast spends server mana"); check(state.Cooldowns.Flamara>os.clock(),"server cooldown set")
S:Cast(player,"Flamara",Vector3.new(0,0,20),false); check(state.Mana==85,"duplicate cast rejected")
state.Cooldowns={}; state.BusyUntil=0; state.Mana=14
S:Cast(player,"Flamara",Vector3.new(0,0,20),false); check(state.Mana==14,"insufficient mana rejected")
state.Mana=100; data.Settings.SpokenCasting=false
S:Cast(player,"Flamara",Vector3.new(0,0,20),true); check(state.Mana==100,"spoken setting enforced")
data.Settings.SpokenCasting=true; state.Statuses.Silenced={Until=os.clock()+5}
S:Cast(player,"Flamara",Vector3.new(0,0,20),false); check(state.Mana==100,"silence enforced")
state.Statuses={}

-- Named wand signatures.
local rnd=math.random; math.random=function() return 0.99 end
deps.WorldService={Runtime={}}; workspace.Raycast=function() return nil end
RaycastParams={new=function() return {} end}; Enum={RaycastFilterType={Exclude="Exclude"}}
local function mob(x)
    local m=target(nil); m.MonsterId="Thornimp"; m.Rank="Normal"; m.Root={Position=Vector3.new(x,0,0)}; m.Contributors={}; m.Threat={}
    C.Targets[m.Model]=m; return m
end
data.Wands={storm}; data.EquippedWand=1
local struck,beside,distant=mob(0),mob(5),mob(20)
local bolt=F.Power(10,data,spells.Scintara,false)
for _=1,3 do S:Impact(player,struck,spells.Scintara,false,1,Vector3.zero) end
check(beside.Humanoid.Health==110,"Static waits for the 4th hit")
S:Impact(player,struck,spells.Scintara,false,1,Vector3.zero)
check(near(beside.Humanoid.Health,110-bolt*0.5) and distant.Humanoid.Health==110,"Static arcs to the nearest monster within 12 studs")
check(near(struck.Humanoid.Health,110-bolt*4),"Static does not strike the bolt's own target")
data.Wands={rare}; beside.Humanoid.Health=110; struck.Humanoid.Health=110
for _=1,4 do S:Impact(player,beside,spells.Scintara,false,1,Vector3.zero) end
check(struck.Humanoid.Health==110,"no Static without Stormfork")
data.Wands={widow}; math.random=function() return 0 end
local rooted=mob(40); rooted.Statuses.Rooted={Until=os.clock()+5}
C:Damage(player,rooted,10,spells.Saxifra); check(near(rooted.Humanoid.Health,90),"Venom Bite doubles crits on Rooted foes")
local loose=mob(60); C:Damage(player,loose,10,spells.Saxifra); check(near(loose.Humanoid.Health,95),"other crits stay at x1.5")
local sleeper=mob(80); sleeper.Statuses.Asleep={Until=os.clock()+5}
C:Damage(player,sleeper,10,spells.Saxifra); check(near(sleeper.Humanoid.Health,90) and not C:Has(sleeper,"Asleep"),"the waking hit bites")
data.Wands={rare}; local plain=mob(100); plain.Statuses.Rooted={Until=os.clock()+5}
C:Damage(player,plain,10,spells.Saxifra); check(near(plain.Humanoid.Health,95),"no Venom Bite without Widow's Bite")
data.Wands={hearth}; math.random=rnd
state.MaxMana=100; state.Mana=50
S:Execute(player,spells.Vitara,Vector3.new(0,0,20),false); check(state.Mana==50,"Sapflow: no refund at full health")
state.Humanoid.Health=40; S:Execute(player,spells.Vitara,Vector3.new(0,0,20),false)
check(state.Mana==56 and state.Humanoid.Health>40,"Sapflow refunds 6 mana")
state.Mana=98; state.Humanoid.Health=40; S:Execute(player,spells.Vitara,Vector3.new(0,0,20),false); check(state.Mana==100,"Sapflow refund caps at max mana")
data.Wands={rare}; state.Mana=50; state.Humanoid.Health=40; S:Execute(player,spells.Vitara,Vector3.new(0,0,20),false)
check(state.Mana==50,"no Sapflow without Hearthroot")
data.Wands=nil; data.EquippedWand=nil; state.Humanoid.Health=110; state.Mana=100; C.Targets={}

local M=require(ROOT.."/src/server/Services/MonsterService.lua"); M:Init(deps)
local imp=target(nil); imp.MonsterId="Thornimp"; imp.Rank="Normal"; imp.Def={Cooldown=1.8}; imp.Phase=1; imp.NextAttack=0; M.Alive[imp]=true
imp.Statuses.Asleep={Until=os.clock()+5}; M:Attack(imp,state); check(imp.NextAttack==0,"sleeping monster cannot start an attack")
imp.Statuses={Stunned={Until=os.clock()+5}}; M:Attack(imp,state); check(imp.NextAttack==0,"stunned monster cannot start an attack")
imp.Statuses={}; M:Attack(imp,state); check(imp.NextAttack>0,"awake monster attacks")
local CF={}; CF.__add=function(c,v) return setmetatable({Position=c.Position+v},CF) end
CFrame={new=function(x,y,z) return setmetatable({Position=Vector3.new(x,y,z)},CF) end}
local lifted=target(nil); lifted.Rank="Normal"; lifted.Root={Position=Vector3.new(0,2,0),CFrame=CFrame.new(0,2,0)}
lifted.Model.PivotTo=function(_,cf) lifted.Root.Position=cf.Position; lifted.Root.CFrame=cf end
local landings=#queued
C:Status(lifted,"Airborne",1.5,player); C:Status(lifted,"Airborne",1.5,other)
check(lifted.Root.Position.Y==8,"overlapping lifts do not stack")
for i=landings+1,#queued do queued[i]() end
check(lifted.Root.Position.Y==2,"lifted unit lands at its ground height")
local ally=target(other); local mob2=target(nil); mob2.MonsterId="Thornimp"; C.Targets[ally.Model]=ally; C.Targets[mob2.Model]=mob2
local lane={{Parent=ally.Model},{Parent=mob2.Model}}
workspace.Spherecast=function(_,_,_,_,params)
    for _,part in ipairs(lane) do
        local skip=false; for _,m in ipairs(params.FilterDescendantsInstances) do if part.Parent==m then skip=true end end
        if not skip then return {Instance=part} end
    end
end
local hit=S:Trace(player,Vector3.zero,Vector3.new(0,0,10),0.8,{FilterDescendantsInstances={}})
check(hit and hit.Instance==lane[2],"bolts pass through allies to the unit behind")
mob2.Humanoid.Health=0
check(S:Trace(player,Vector3.zero,Vector3.new(0,0,10),0.8,{FilterDescendantsInstances={}})==nil,"defeated units do not absorb bolts")
duel.allowed=true; hit=S:Trace(player,Vector3.zero,Vector3.new(0,0,10),0.8,{FilterDescendantsInstances={}})
check(hit and hit.Instance==lane[1],"duel opponent still stops bolts"); duel.allowed=false
C.Targets={}

local P=require(ROOT.."/src/server/Services/ProgressionService.lua")
local p={Parent=true,UserId=11,FindFirstChild=function() return nil end,SetAttribute=function() end}
local record={Level=1,XP=0,Gilders=0,House="",HousePoints=0,Attributes={Power=0,Focus=0,Vitality=0,Agility=0,Unspent=0},
    Spells={},Loadout={Slot1="",Slot2="",Slot3="",Slot4=""},Quest=1,QuestProgress=0,QuestDone={},Daily={Day=0,Kills=0,Claimed=false},
    Talents={},Wands={},EquippedWand=0,Wand="",HasWand=true}
profileData[p]=record
local cFake={UpdateStats=fire,HouseTrim=fire,States={}}
P:Init({PlayerDataService=deps.PlayerDataService,NetworkService=N,CombatService=cFake,DuelService=duel})
P:Event(p,"Wand"); P:Event(p,"Sorted")
check(record.Level==2 and record.Quest==3,"first two tutorial steps")
P:Award(p,120,30); P:Event(p,"Class")
check(record.Level==3 and record.Quest==4,"first class leveling")
for _=1,5 do P:Event(p,"Practice") end; P:Event(p,"Tobb")
for _=1,6 do P:Award(p,35,7); P:Event(p,"Kill","Thornimp") end
check(record.Level==4 and record.Quest==7,"first hunt unlocks Flamara")
check(not P:Learn(p,"Frigora",true),"learning level gate")
check(P:Learn(p,"Flamara",true),"eligible learned spell")
check(not P:Learn(p,"Flamara",true),"learn is idempotent")
for _=1,75 do P:Hit(p,"Flamara") end
check(record.Spells.Flamara.Mastery==3,"hit mastery progression")
P:Award(p,1000000,0); check(record.Level==20,"launch level cap"); check(record.Attributes.Unspent==38,"two points per level")
record.SealDefeated=true; record.BossDefeated=true; P:Refresh(p)
check(record.Spells.Tonitra and record.Spells.Murallis,"deferred boss and story unlocks")
local beforeGold=record.Gilders
for _=1,20 do P:Event(p,"Kill","Thornimp") end
check(record.Daily.Claimed and record.Gilders==beforeGold+120,"daily reward grants once")
check(P:Talent(p,"SearingFocus") and record.Talents.SearingFocus==1,"skill point spent"); check(not P:Talent(p,"Overload"),"capstone stays locked")

local WS=require(ROOT.."/src/server/Services/WandService.lua")
WS:Init({PlayerDataService=deps.PlayerDataService,NetworkService=N,DuelService=duel,ProgressionService=P,CombatService=cFake})
check(WS:Grant(p,{Wood="Ash",Core="Frostfang",Rarity="Common"}) and record.EquippedWand==1,"first wand is equipped")
WS:Grant(p,{Wood="Ironoak",Core="Stormglass",Rarity="Rare"})
cFake.States[p]={LastCombat=-100,Model={FindFirstChild=function() return nil end}}
WS:Equip(p,2,Wands.Name(record.Wands[1])); check(record.EquippedWand==1,"stale wand button rejected")
WS:Equip(p,2,Wands.Name(record.Wands[2])); check(record.EquippedWand==2 and record.Wand=="Ironoak / Stormglass","equip wand from bag")
WS:Discard(p,2,Wands.Name(record.Wands[2])); check(#record.Wands==2,"equipped wand cannot be discarded")
WS:Discard(p,1,Wands.Name(record.Wands[1])); check(#record.Wands==1 and record.EquippedWand==1,"discard keeps the equipped wand")
for _=1,12 do WS:Grant(p,Wands.Roll("Common")) end; check(#record.Wands==Wands.Capacity,"wand case capacity")

-- Named wand sources.
P.S.WandService=WS; WS.S.WorldService={Near=function() return true end}
record.Inventory={}; record.WandsHeld={}; record.WandRewards={}
for i,q in ipairs(require(shared.QuestData)) do if q.Id=="Seal" then record.Quest=i end end
record.QuestProgress=0; P:Event(p,"Kill","RotbarkSentinel")
check(record.WandRewards.Stormfork and record.WandsHeld[1]=="Stormfork" and #record.Wands==Wands.Capacity,"full case: Oakhart holds the quest wand")
WS:Deliver(p); check(#record.WandsHeld==1,"held wand waits for room")
WS:Discard(p,2,Wands.Name(record.Wands[2])); WS:Deliver(p)
check(#record.WandsHeld==0 and record.Wands[#record.Wands].Named=="Stormfork","Oakhart hands over the held wand")
record.WandRewards={}; WS:Discard(p,2,Wands.Name(record.Wands[2])); WS:Deliver(p); WS:Deliver(p)
local storms=0; for _,w in ipairs(record.Wands) do if w.Named=="Stormfork" then storms=storms+1 end end
check(storms==2 and record.WandRewards.Stormfork,"quest wands earned before this update arrive once")
for _=1,3 do WS:Discard(p,2,Wands.Name(record.Wands[2])) end
record.Gilders=1000; record.Inventory.Heartwood=2; local count=#record.Wands
WS:Commission(p,"Hearthroot"); check(#record.Wands==count and record.Gilders==1000,"Hearthroot needs three Heartwood")
record.Inventory.Heartwood=3; record.Level=17; WS:Commission(p,"Hearthroot"); check(#record.Wands==count,"Hearthroot needs level 18")
record.Level=20; WS:Commission(p,"Hearthroot")
check(record.Inventory.Heartwood==0 and record.Gilders==400 and record.Wands[#record.Wands].Named=="Hearthroot","Oakhart commissions Hearthroot")
record.Inventory["Widow's Bite trophy"]=5; WS:Commission(p,"WidowsBite")
check(record.Inventory["Widow's Bite trophy"]==0 and record.Wands[#record.Wands].Named=="WidowsBite","five trophies forge Widow's Bite")
count=#record.Wands; WS:Commission(p,"Stormfork"); WS:Commission(p,"Nope"); check(#record.Wands==count,"Stormfork is not for sale")
local Loot=require(services.ServerStorage.LootTables)
check(Wands.Named[Loot.MotherVexweave.Named.Id] and Loot.MotherVexweave.Named.Chance==0.1,"Mother Vexweave can drop Widow's Bite")

local D=require(ROOT.."/src/server/Services/PlayerDataService.lua")
D:Init({NetworkService=N}); D.Ephemeral=false
local store={value={Data={Gilders=4},Session={Id=D.SessionId,Expires=os.time()+180}}}
function store:UpdateAsync(_,transform) local result=transform(self.value); if result then self.value=result end; return result end
D.Store=store
local saver={UserId=22,Parent=false}
D.Profiles[saver]={Data={Gilders=55,Inventory={Herb=2}},Busy=false,SavedAt=os.time()}
check(D:Save(saver,false),"save works with owned lock")
check(store.value.Data.Gilders==55 and store.value.Session.Id==D.SessionId,"data and lock committed together")
D.Profiles[saver].Data.Inventory.Herb=3
check(store.value.Data.Inventory.Herb==2,"save snapshot is a deep copy")
store.value.Session.Id="other-server"; D.Profiles[saver].Data.Gilders=1000
check(not D:Save(saver,false),"stale writer rejected")
check(store.value.Data.Gilders==55,"stale writer cannot overwrite")
store.value.Session.Id=D.SessionId
check(D:Save(saver,true) and store.value.Session==nil,"release clears only owned lock")

local NService=require(ROOT.."/src/server/Services/NetworkService.lua"); NService.Buckets={}
check(NService:Allow(player,"Cast",0,2),"bucket first token")
check(NService:Allow(player,"Cast",0,2),"bucket second token")
check(not NService:Allow(player,"Cast",0,2),"bucket burst limit")

-- A delayed discard must not delete the identical wand that shifted into its slot.
record.Wands={{Wood="Ash",Core="Frostfang",Rarity="Common"},{Wood="Rowan",Core="Emberplume",Rarity="Rare"},{Wood="Rowan",Core="Emberplume",Rarity="Rare"}}
record.EquippedWand=1
local revision=record.WandRevision or 0
local sameName=Wands.Name(record.Wands[2])
WS:Discard(p,2,sameName,revision); check(#record.Wands==2,"current bag revision can discard")
WS:Discard(p,2,sameName,revision); check(#record.Wands==2,"stale discard cannot delete identical replacement")
WS:Equip(p,2,sameName,revision); check(record.EquippedWand==1,"stale equip rejected after case changes")
WS:Equip(p,2,sameName,record.WandRevision); check(record.EquippedWand==2,"fresh bag selection equips")

-- Learning a starter already assigned by the profile must not consume a second slot.
record.Spells.Glimmora=nil; record.Loadout={Slot1="Glimmora",Slot2="",Slot3="",Slot4=""}
check(P:Learn(p,"Glimmora",true),"learn preassigned starter")
check(record.Loadout.Slot2=="","starter learning preserves empty slots")

-- NPC choices are validated again on the server, including after walking away.
local interactions=require(ROOT.."/src/server/Services/InteractionService.lua")
local nearby,busy,used=true,false,0
local dialogue
interactions:Init({PlayerDataService=deps.PlayerDataService,
    WorldService={Near=function() return nearby end}, DuelService={IsBusy=function() return busy end},
    NetworkService={UI={FireClient=function(_,_,kind,info) dialogue={kind,info} end}}})
interactions.Interactions.Tobb={Name="Tobb",Action="Ask about Whisperwood",Callback=function() used=used+1 end}
interactions:Interact(p,"Tobb","Hello")
check(dialogue[1]=="Dialogue" and #dialogue[2].Choices==3,"NPC conversation offers service, advice and quest choices")
interactions:Interact(p,"Tobb","Advice"); check(dialogue[2].Text:find("Shift",1,true),"Tobb gives combat advice")
interactions:Interact(p,"Tobb","Quest"); check(type(dialogue[2].Text)=="string","NPC provides quest guidance")
interactions:Interact(p,"Tobb","Service"); check(used==1,"NPC service executes once")
nearby=false; interactions:Interact(p,"Tobb","Service"); check(used==1,"remote NPC service rejected")
nearby=true; busy=true; interactions:Interact(p,"Tobb","Service"); check(used==1,"NPC service rejected during duel")
busy=false; interactions:Interact(p,"Unknown","Service"); interactions:Interact(p,"Tobb","Unknown"); interactions:Interact(p,{},"Service")
check(used==1,"unknown NPCs and choices are ignored")

-- More than four friendly units must not swallow a projectile.
C.Targets={}; lane={}
for i=1,6 do local friend=target(other); C.Targets[friend.Model]=friend; lane[i]={Parent=friend.Model} end
local enemy=target(nil); enemy.MonsterId="Thornimp"; C.Targets[enemy.Model]=enemy; lane[7]={Parent=enemy.Model}
hit=S:Trace(player,Vector3.zero,Vector3.new(0,0,10),0.8,{FilterDescendantsInstances={}})
check(hit and hit.Instance==lane[7],"bolts pass through a crowd of allies")

-- Wand bodies, with just enough of Instance, CFrame, Color3 and Enum to count parts.
local CFm={}; CFm.__mul=function() return setmetatable({},CFm) end
CFrame={new=function() return setmetatable({},CFm) end,Angles=function() return setmetatable({},CFm) end}
Color3={fromRGB=function(r,g,b) return {r,g,b} end}
local named_enum={__index=function(_,k) return k end}
Enum={PartType=setmetatable({},named_enum),Material=setmetatable({},named_enum),MeshType=setmetatable({},named_enum)}
local made={}
Instance={new=function(class) local o={ClassName=class}; made[#made+1]=o; return o end}
local WM=require(shared.WandModel)
local function build(wand)
    made={}; local model=WM.Build(wand,CFrame.new(),true); local n,tip={},nil
    for _,o in ipairs(made) do
        if o.Parent==model and o.ClassName=="Part" then n[o.Name]=(n[o.Name] or 0)+1 end
        if o.ClassName=="Attachment" then tip=o.Parent end
    end
    return n,tip
end
local n,tip=build(storm); check(n.Prong==2 and n.Cap==2 and n.Coil==4 and n.Band==1 and tip.Name=="Tip" and tip.Shape=="Ball","Stormfork body")
n,tip=build(hearth); check(n.Leaf==1 and n.Bud==1 and n.Stem==1 and n.Root==4 and n.Knot==3 and n.Core==1 and n.Band==2 and tip.Shape=="Ball","Hearthroot body")
n,tip=build(widow); check(n.Leg==8 and n.Claw==8 and n.Silk==3 and n.Mandible==2 and n.Collar==1 and not n.Thorn and tip.Shape=="Block","Widow's Bite body")
n=build({Wood="Blackthorn",Core="Emberplume",Rarity="Common"}); check(n.Thorn==3 and not n.Band and not n.Leg and not n.Collar,"catalogue wands build as before")
-- Start the real client with dependencies arriving after the LocalScript.
do
    local oldGame,oldScript,oldRequire=game,script,require
    local available={}
    local function folder(path)
        return setmetatable({WaitForChild=function(_,name)
            local key=path.."/"..name
            while not available[key] do coroutine.yield(key) end
            return available[key]
        end},{__index=function(_,name) error("Dependency accessed before arrival: "..path.."/"..name) end})
    end
    local rs=folder("RS")
    game={GetService=function(_,name) assert(name=="ReplicatedStorage"); return rs end}
    script={Parent=folder("PlayerScripts")}
    local order={"UIController","EffectsController","InputController"}
    local initialized,started,loaded={},{},{}
    local calls={}
    local modules={}
    for _,name in ipairs(order) do
        local id=name
        modules[id]={
            Init=function(_,controllers)
                for _,other in ipairs(order) do check(controllers[other]==modules[other],"all controllers loaded before Init") end
                initialized[id]=true
            end,
            Start=function()
                for _,other in ipairs(order) do check(initialized[other],"all controllers initialized before Start") end
                started[id]=true; calls[#calls+1]=id
            end,
        }
    end
    require=function(module) loaded[module]=true; return modules[module] end
    local client=coroutine.create(function() dofile(ROOT.."/src/client/Main.client.lua") end)
    local ok,waiting=coroutine.resume(client)
    check(ok and waiting=="RS/Remotes","client waits for remotes")
    while coroutine.status(client)~="dead" do
        if waiting=="PlayerScripts/Controllers" then check(not next(loaded),"controllers do not load before their folder arrives") end
        if waiting=="PlayerScripts/Controllers/InputController" then check(not next(loaded),"all controller modules arrive before require") end
        local name=waiting:match("([^/]+)$")
        available[waiting]=modules[name] and name or folder(waiting)
        ok,waiting=coroutine.resume(client)
        check(ok,"delayed client startup failed: "..tostring(waiting))
    end
    check(started.UIController and started.InputController and started.EffectsController,"UI, inventory inputs and effects all start")
    check(table.concat(calls,",")==table.concat(order,","),"UI starts before input and effects")
    game,script,require=oldGame,oldScript,oldRequire
end
-- Exercise every authored prompt and the inventory actions used by their menus.
do
    local oldGame,oldWorkspace,oldInstance,oldEnum=game,workspace,Instance,Enum
    local oldTask,oldRequire=task,require
    local function signal() return {Connect=function(self,fn) self.Callback=fn end} end
    local noop=function() end
    local enum=setmetatable({},{__index=function(_,key) return key end})
    Enum={KeyCode=enum,Material=enum,HumanoidDisplayDistanceType=enum}
    local prompts={}
    Instance={new=function(class)
        local obj={ClassName=class,Triggered=signal()}
        if class=="ProximityPrompt" then prompts[#prompts+1]=obj end
        return obj
    end}
    workspace={Map={FindFirstChild=function() return nil end}}
    local jobs={}
    task={spawn=function(fn) jobs[#jobs+1]=fn end,wait=noop}
    local shared={}
    for _,name in ipairs({"Config","Formulas","WandData","WandModel","QuestData","SkillData","SpellData","Gesture"}) do shared[name]=ROOT.."/src/shared/"..name..".lua" end
    local services={ReplicatedStorage={Shared=shared},Players={PlayerRemoving=signal()},HttpService={GenerateGUID=function() return "lesson-test" end}}
    game={GetService=function(_,name) return services[name] end}
    require=function(path) return assert(loadfile(path))() end
    local config=require(shared.Config)
    local d={Level=1,XP=0,Gilders=0,BankGilders=0,House="",HousePoints=0,HasWand=false,Wands={},EquippedWand=0,
        WandRewards={},WandsHeld={},Spells={},Loadout={Ward="Aegara",Slot1="Glimmora",Slot2="",Slot3="",Slot4=""},
        Attributes={Power=0,Focus=0,Vitality=0,Agility=0,Unspent=0},Talents={},Quest=1,QuestProgress=0,QuestDone={},
        Inventory={},Waystones={},LastRespec=0,LastTalentReset=0}
    local player={Parent=true,UserId=1,FindFirstChild=function() return nil end,SetAttribute=noop}
    local state={Humanoid={Health=60,MaxHealth=100},Model={FindFirstChild=function() return nil end},LastCombat=-100}
    local anchor,nearby,busy=nil,true,false
    local ui,notice,syncs=nil,nil,0
    local net={Handlers={},UI={FireClient=function(_,_,kind,info) ui={kind,info} end},
        Notice=function(_,_,message) notice=message end,Sync=function() syncs=syncs+1 end,Allow=function() return true end}
    local s={NetworkService=net,PlayerDataService={Get=function() return d end},
        WorldService={Anchor=function(_,name) return {Name=name} end,Near=function(_,_,marker)
            local name=type(marker)=="table" and marker.Name or marker
            return nearby and name==anchor
        end},DuelService={IsBusy=function() return busy end},
        CombatService={States={[player]=state},Register=noop,HouseTrim=noop,UpdateStats=noop,
            CanAct=function() return state.Humanoid.Health>0 end,Heal=function(_,_,target,amount) target.Humanoid.Health=math.min(100,target.Humanoid.Health+amount) end}}
    s.ProgressionService=require(ROOT.."/src/server/Services/ProgressionService.lua"); s.ProgressionService:Init(s)
    s.WandService=require(ROOT.."/src/server/Services/WandService.lua"); s.WandService:Init(s); s.WandService:Start()
    s.ClassService=require(ROOT.."/src/server/Services/ClassService.lua"); s.ClassService:Init(s)
    local interactions=require(ROOT.."/src/server/Services/InteractionService.lua"); interactions:Init(s); interactions:Start()
    local byName={}
    for _,prompt in ipairs(prompts) do
        local name=prompt.Parent.Name; byName[name]=prompt; anchor=name; ui=nil
        prompt.Triggered.Callback(player)
        if interactions.Interactions[name] then
            check(ui and ui[1]=="Dialogue" and ui[2].Anchor==name,name.." prompt opens its dialogue")
            net.Handlers.Interact(player,name,"Advice"); check(ui[1]=="Dialogue" and #ui[2].Text>0,name.." advice works")
            net.Handlers.Interact(player,name,"Quest"); check(ui[1]=="Dialogue" and #ui[2].Text>0,name.." quest guidance works")
        end
        check(prompt.KeyboardKeyCode=="E" and prompt.GamepadKeyCode=="ButtonX",name.." uses documented controls")
    end
    check(#prompts==15,"all eleven NPCs, mirror and three waystones registered")
    local function service(name)
        anchor=name; ui=nil
        net.Handlers.Interact(player,name,"Service")
    end
    service("Oakhart")
    check(d.HasWand and #d.Wands==1 and d.EquippedWand==1,"first wand appears equipped in inventory")
    check(d.Spells.Scintara and d.Spells.Aegara and d.Spells.Glimmora,"first wand grants all starter spells")
    service("Oakhart"); check(#d.Wands==1 and ui[1]=="Wandery","repeat visit opens shop without duplicating starter")
    anchor="Mirror"; byName.Mirror.Triggered.Callback(player); check(ui[1]=="Sorting","mirror opens sorting")
    net.Handlers.Sort(player,{1,2,3,4,1},"Emberclaw"); check(d.House=="Emberclaw","sorting choice is applied")
    for school,teacher in pairs(config.Teachers) do
        service(teacher.Anchor)
        check(ui[1]=="Lesson" and ui[2].Teacher==teacher.Name and s.ClassService.Lessons[player].School==school,teacher.Name.." opens the correct lesson")
    end
    d.Quest=5; d.QuestProgress=0; service("Tobb"); check(d.QuestDone.Tobb,"Tobb advances his quest")
    d.Level=20
    for name,menu in pairs({Bank="Bank",Apothecary="Shop",Library="Library",Duelmaster="Duels"}) do
        service(name); check(ui and ui[1]==menu,name.." opens its service menu")
    end
    check(d.Spells.Tractum and d.Spells.Excido,"library and duelmaster teach eligible spells")
    for id in pairs(config.Waystones) do
        anchor="Waystone_"..id; byName[anchor].Triggered.Callback(player)
        check(d.Waystones[id] and d.LastWaystone==id and ui[1]=="Map",id.." attunes and opens travel")
    end
    anchor="Bank"; d.Gilders=250; net.Handlers.Bank(player,"Deposit",100)
    check(d.Gilders==150 and d.BankGilders==100,"bank deposit updates carried and stored currency")
    net.Handlers.Bank(player,"Withdraw",100); check(d.Gilders==250 and d.BankGilders==0,"bank withdrawal returns currency")
    anchor="Apothecary"; net.Handlers.Shop(player,"BuyHealth")
    check(d.Gilders==200 and d.Inventory["Health Draught"]==1,"purchased potion appears in bag")
    d.Inventory["Thorn Barb"]=1; d.Inventory["Spider Silk"]=1; net.Handlers.Shop(player,"BrewHealth")
    check(d.Inventory["Health Draught"]==2 and d.Inventory["Thorn Barb"]==0 and d.Inventory["Spider Silk"]==0,"brewing consumes ingredients and adds potion")
    net.Handlers.UseItem(player,"Health Draught"); check(d.Inventory["Health Draught"]==1,"using potion consumes one")
    net.Handlers.UseItem(player,"Health Draught"); check(d.Inventory["Health Draught"]==1,"cooldown prevents consuming second potion")
    for _,fn in ipairs(jobs) do fn() end; check(state.Humanoid.Health==100,"potion heals over four ticks")
    interactions.PotionCooldowns[player]=nil; net.Handlers.UseItem(player,"Health Draught")
    check(d.Inventory["Health Draught"]==1,"full health does not consume potion")
    d.Inventory["Frigora Tome"]=2; d.Level=1; net.Handlers.UseItem(player,"Frigora Tome")
    check(d.Inventory["Frigora Tome"]==2 and not d.Spells.Frigora,"level gate preserves tome")
    d.Level=20; net.Handlers.UseItem(player,"Frigora Tome")
    check(d.Inventory["Frigora Tome"]==1 and d.Spells.Frigora,"tome teaches spell and consumes one")
    net.Handlers.UseItem(player,"Frigora Tome"); check(d.Inventory["Frigora Tome"]==1,"known spell preserves remaining tome")
    anchor="Oakhart"; d.Gilders=1000; net.Handlers.BuyWand(player)
    check(#d.Wands==2 and d.Gilders==800,"wand commission adds inventory item")
    local wands=require(shared.WandData)
    local selection={Name=wands.Name(d.Wands[2]),Revision=d.WandRevision}
    net.Handlers.EquipWand(player,2,selection); check(d.EquippedWand==2,"bag selection payload equips wand")
    selection={Name=wands.Name(d.Wands[1]),Revision=d.WandRevision}
    net.Handlers.DiscardWand(player,1,selection); check(#d.Wands==1 and d.EquippedWand==1,"discard preserves equipped wand")
    nearby=false; local gold=d.Gilders; service("Oakhart"); net.Handlers.BuyWand(player)
    check(ui==nil and d.Gilders==gold,"walking away blocks NPC services and purchases")
    nearby=true; busy=true; service("Bank"); check(ui==nil,"duels block NPC services")
    check(syncs>10,"inventory and progression changes publish updated profiles")
    game,workspace,Instance,Enum=oldGame,oldWorkspace,oldInstance,oldEnum
    task,require=oldTask,oldRequire
end
-- Input routing regressions. Roblox camera/GUI integration still needs Studio.
do
    local function signal() return {Connect=function(self,fn) self.Callback=fn end} end
    local enum=setmetatable({},{__index=function(t,k) rawset(t,k,k); return k end})
    Enum={UserInputType=enum,KeyCode=enum,UserInputState=enum,ContextActionResult=enum,ContextActionPriority={High={Value=3000}},RenderPriority={Camera={Value=200}}}
    local bindings={}
    local cas={BindAction=function(_,name,fn) bindings[name]=fn end,BindActionAtPriority=function(_,name,fn) bindings[name]=fn end}
    local focused=false
    local uis={GetFocusedTextBox=function() return focused end,GetMouseLocation=function() return {X=0,Y=0} end,
        InputBegan=signal(),TextBoxFocused=signal(),TextBoxFocusReleased=signal(),WindowFocusReleased=signal()}
    local player={PlayerGui={GetGuiObjectsAtPosition=function() return {} end},CharacterAdded=signal()}
    local prompts={PromptShown=signal(),PromptHidden=signal()}
    local services={Players={LocalPlayer=player},ReplicatedStorage={},UserInputService=uis,ContextActionService=cas,RunService={BindToRenderStep=function() end},ProximityPromptService=prompts}
    game={GetService=function(_,name) return services[name] end}
    local input=dofile(ROOT.."/src/client/Controllers/InputController.lua")
    local ui={Menu=nil,IsOpen=function(self) return self.Menu~=nil end,Close=function(self) self.Menu=nil end,Show=function(self,menu) self.Menu=menu end}
    input:Init({UIController=ui}); input.CameraMode=function() end
    local casts=0; input.UseSlot=function() casts=casts+1 end
    input:Start()
    local mouse={UserInputType=Enum.UserInputType.MouseButton1}
    local pad={UserInputType="Gamepad1"}
    local basic=bindings.Wandbound_Basic
    basic(nil,"Begin",pad); check(input.Holding and casts==1,"trigger begins held casting")
    basic(nil,"Change",pad); check(input.Holding and casts==1,"analog changes preserve hold without duplicate casts")
    basic(nil,"End",pad); check(not input.Holding,"trigger release stops casting")
    basic(nil,"Begin",mouse); basic(nil,"Cancel",mouse); check(not input.Holding,"cancel stops held casting")
    basic(nil,"Begin",mouse); uis.WindowFocusReleased.Callback(); check(not input.Holding,"window focus loss stops casting")
    basic(nil,"Begin",mouse); uis.TextBoxFocused.Callback(); check(not input.Holding,"typing stops held casting")
    input:ToggleMenu("Bag"); check(ui.Menu=="Bag" and not input.Holding,"bag hotkey opens bag")
    input:ToggleMenu("Spells"); check(ui.Menu=="Spells","different menu hotkey switches directly")
    input:ToggleMenu("Spells"); check(ui.Menu==nil,"same menu hotkey closes menu")
    focused=true
    check(bindings.Wandbound_Bag(nil,"Begin")=="Pass" and ui.Menu==nil,"bag hotkey passes through while typing")
    local before=casts
    check(basic(nil,"Begin",mouse)=="Pass" and casts==before,"typing blocks casting")
    focused=false; ui.Menu="Bag"
    check(basic(nil,"Begin",pad)=="Pass" and casts==before and not input.Holding,"menu blocks casting and passes gamepad input")
    ui.Menu=nil
    local prompt={Parent={},Enabled=true,GamepadKeyCode=Enum.KeyCode.ButtonX}
    local interact={UserInputType="Gamepad1",KeyCode=Enum.KeyCode.ButtonX}
    local slot=bindings.Wandbound_Slot1
    prompts.PromptShown.Callback(prompt)
    check(slot(nil,"Begin",interact)=="Pass" and casts==before,"visible NPC prompt receives X without casting")
    check(slot(nil,"End",interact)=="Pass","NPC prompt receives X release")
    slot(nil,"Begin",{UserInputType="Keyboard",KeyCode=Enum.KeyCode.One})
    check(casts==before+1,"keyboard slot still works beside NPC")
    prompts.PromptHidden.Callback(prompt)
    check(slot(nil,"Begin",interact)=="Sink" and casts==before+2,"X casts again after leaving prompt")
    prompts.PromptShown.Callback(prompt); prompt.Enabled=false
    slot(nil,"Begin",interact); check(casts==before+3,"disabled prompts do not block spells")
    prompt.Enabled=true; prompt.Parent=nil
    slot(nil,"Begin",interact); check(casts==before+4,"removed prompts do not block spells")
end
print("PASS: "..total.." headless assertions (formulas, catalogue, gestures, PvP, CC, shielding, cast validation, unit interactions, wands, named wands, skill tree, progression, locks, rate limits, client startup, NPC prompts and services, inventory, input routing).")
