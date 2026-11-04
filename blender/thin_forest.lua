--[[ Thin the WorldPlan oaks in the place to the ones blender/thin_forest.py keeps (see blender/README.md, "WorldPlan
in the game"). Run it after install_worldplan.lua's Finish, with the decoded
blender/exports/RobloxWorld/forest_thinning.json:

    require(thin_forest)(thinning)

Every Map.Forest oak whose number isn't kept is removed, a few hundred a frame, as one undoable change. Running it
again changes nothing. It refuses a list made for a different number of trees than stand or once stood.
]]
local ChangeHistoryService = game:GetService("ChangeHistoryService")

return function(thinning)
    local forest = workspace.Map.Forest
    local keep, highest = {}, 0
    for _, n in ipairs(thinning.kept) do keep[n] = true end
    for _, oak in ipairs(forest:GetChildren()) do
        highest = math.max(highest, tonumber(oak.Name:match("^Oak (%d+)$")) or 0)
    end
    assert(highest <= thinning.trees_in_manifest, string.format(
        "Oak %04d stands, but the list is for %d trees: run blender/thin_forest.py again", highest, thinning.trees_in_manifest))
    local recording = ChangeHistoryService:TryBeginRecording("Thin the WorldPlan oaks")
    local removed = 0
    for _, oak in ipairs(forest:GetChildren()) do
        local n = tonumber(oak.Name:match("^Oak (%d+)$"))
        if n and not keep[n] then
            oak:Destroy(); removed += 1
            if removed % 300 == 0 then task.wait() end
        end
    end
    if recording then ChangeHistoryService:FinishRecording(recording, Enum.FinishRecordingOperation.Commit) end
    return string.format("Removed %d oaks; %d stand, %d kept by the list.", removed, #forest:GetChildren(), #thinning.kept)
end
