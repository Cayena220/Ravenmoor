local Players=game:GetService("Players")
local RS=game:GetService("ReplicatedStorage")
local Tween=game:GetService("TweenService")
local SoundService=game:GetService("SoundService")
local Sounds=require(RS.Shared.SoundData)
-- Background music (SoundData.Music): the track for the zone you're in (your Zone attribute, set by WorldService), or
-- its own while you fly a broom. Moving from one to another crossfades over SoundData.Crossfade seconds. Every track
-- loops, and one you leave pauses where it was, so coming back picks it up again. The Music setting turns it off.
-- Tracks play from SoundService, so they sound the same wherever you are.
local M={}
function M:Init(controllers) self.C=controllers; self.Player=Players.LocalPlayer; self.Tracks={}; self.Playing=nil end
function M:Wanted()
    local d=self.C.UIController.Data
    if d and d.Settings and d.Settings.Music==false then return nil end
    if self.Player:GetAttribute("Broom") then return "Flying" end
    local zone=self.Player:GetAttribute("Zone")
    return Sounds.Music[zone or ""] and zone or "Hollowmere"
end
function M:Track(name)
    local track=self.Tracks[name]
    if not track then
        local entry=Sounds.Music[name]; if not entry then return nil end
        track=Instance.new("Sound"); track.Name="Music"..name; track.SoundId="rbxassetid://"..entry.Id
        track.Looped=true; track.Volume=0; track.Parent=SoundService
        self.Tracks[name]=track
    end
    return track
end
function M:Switch(name)
    if name==self.Playing then return end
    local fade=TweenInfo.new(Sounds.Crossfade,Enum.EasingStyle.Sine)
    local leaving=self.Playing; local old=leaving and self.Tracks[leaving]
    if old then
        local out=Tween:Create(old,fade,{Volume=0}); out:Play()
        out.Completed:Once(function(state)
            if state==Enum.PlaybackState.Completed and self.Playing~=leaving then old:Pause() end
        end)
    end
    self.Playing=name
    local track=name and self:Track(name)
    if track then
        if not track.IsPlaying then if track.TimePosition>0 then track:Resume() else track:Play() end end
        Tween:Create(track,fade,{Volume=Sounds.Music[name].Volume}):Play()
    end
end
function M:Start()
    task.spawn(function()
        while true do self:Switch(self:Wanted()); task.wait(0.5) end
    end)
end
return M
