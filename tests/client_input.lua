-- Input routing regressions. Roblox camera/GUI integration still needs Studio.
local total=0
local function check(ok,message) total=total+1; assert(ok,message) end
local function signal() return {Connect=function(self,fn) self.Callback=fn end} end
local enum=setmetatable({},{__index=function(t,k) rawset(t,k,k); return k end})
Enum={UserInputType=enum,KeyCode=enum,UserInputState=enum,ContextActionResult=enum,ContextActionPriority={High={Value=3000}},RenderPriority={Camera={Value=200}}}
local bindings={}
local cas={BindAction=function(_,name,fn) bindings[name]=fn end,BindActionAtPriority=function(_,name,fn) bindings[name]=fn end}
local focused=false
local uis={GetFocusedTextBox=function() return focused end,GetMouseLocation=function() return {X=0,Y=0} end,
    InputBegan=signal(),TextBoxFocused=signal(),TextBoxFocusReleased=signal(),WindowFocusReleased=signal()}
local player={PlayerGui={GetGuiObjectsAtPosition=function() return {} end},CharacterAdded=signal()}
local services={Players={LocalPlayer=player},ReplicatedStorage={},UserInputService=uis,ContextActionService=cas,RunService={BindToRenderStep=function() end}}
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
return total
