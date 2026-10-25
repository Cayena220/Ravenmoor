local RS=game:GetService("ReplicatedStorage")
local remotes=RS:WaitForChild("Remotes")
for _,name in ipairs({"Cast","Aim","Action","Gesture","Profile","State","UI","FX","CastReply"}) do remotes:WaitForChild(name) end
local shared=RS:WaitForChild("Shared")
for _,name in ipairs({"Config","SpellData","Formulas","QuestData","Gesture","WorldPoints","WandData","WandModel","SkillData"}) do shared:WaitForChild(name) end
local order={"UIController","EffectsController","InputController"}
local controllers={}
for _,name in ipairs(order) do controllers[name]=require(script.Parent.Controllers[name]) end
for _,name in ipairs(order) do controllers[name]:Init(controllers) end
for _,name in ipairs(order) do controllers[name]:Start() end
