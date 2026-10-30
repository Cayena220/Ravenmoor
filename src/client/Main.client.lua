local RS=game:GetService("ReplicatedStorage")
local remotes=RS:WaitForChild("Remotes")
for _,name in ipairs({"Cast","Channel","Aim","Action","Gesture","Profile","State","UI","FX","CastReply"}) do remotes:WaitForChild(name) end
local shared=RS:WaitForChild("Shared")
for _,name in ipairs({"Config","SpellData","Formulas","QuestData","Gesture","WorldPoints","WandData","WandModel","SkillData","BroomData"}) do shared:WaitForChild(name) end
local order={"UIController","EffectsController","InputController","AdminController","FlightController"}
-- PlayerScripts and its descendants may replicate after this LocalScript starts.
-- Wait for every controller before requiring any of them or starting the UI.
local folder=script.Parent:WaitForChild("Controllers")
local modules={}
for _,name in ipairs(order) do modules[name]=folder:WaitForChild(name) end
local controllers={}
for _,name in ipairs(order) do controllers[name]=require(modules[name]) end
for _,name in ipairs(order) do controllers[name]:Init(controllers) end
for _,name in ipairs(order) do controllers[name]:Start() end
