--[[ After-import fix-up for models built in blender/ (see blender/README.md, step 5).

Select the imported models in Explorer, paste this whole file into View > Command Bar and press Enter.
Running it again changes nothing. For each selected model it:
  * turns MeshParts still in the importer's default grey to white, because Studio multiplies a mesh's
    vertex colours by the part's Color;
  * renames the root Pose of every keyframe in the model's imported animations (its AnimSaves) to the
    MeshPart that holds the bones. The importer names that Pose after the Blender armature, and the
    Animator then ignores the root bone's keys;
  * drops the .001-style suffixes Blender adds to repeated names from its parts and models, so that
    names such as "Lit window" match what WorldService's night lights look for. Bones keep theirs,
    since animations refer to them by name.
]]
local IMPORT_GREY = Color3.fromRGB(163, 162, 165)

local function isImportGrey(colour)
    return math.abs(colour.R - IMPORT_GREY.R) < 1e-3 and math.abs(colour.G - IMPORT_GREY.G) < 1e-3
        and math.abs(colour.B - IMPORT_GREY.B) < 1e-3
end

local function fixModel(model)
    local whitened, renamed, unmatched, sequences, tidied = 0, 0, 0, 0, 0
    local holders = {}   -- bone name -> the part it sits in
    for _, item in ipairs(model:GetDescendants()) do
        local base = (item:IsA("BasePart") or item:IsA("Model")) and item.Name:match("^(.-)%.%d%d%d$")
        if base then
            item.Name = base
            tidied = tidied + 1
        end
        if item:IsA("MeshPart") and isImportGrey(item.Color) then
            item.Color = Color3.new(1, 1, 1)
            whitened = whitened + 1
        elseif item:IsA("Bone") and item.Parent:IsA("BasePart") then
            holders[item.Name] = item.Parent
        end
    end
    local saves = model:FindFirstChild("AnimSaves")
    local folder = saves and saves:IsA("ObjectValue") and saves.Value
    for _, sequence in ipairs(folder and folder:GetDescendants() or {}) do
        if sequence:IsA("KeyframeSequence") then
            sequences = sequences + 1
            for _, keyframe in ipairs(sequence:GetKeyframes()) do
                for _, root in ipairs(keyframe:GetChildren()) do
                    if root:IsA("Pose") then
                        local holder
                        for _, pose in ipairs(root:GetChildren()) do holder = holder or holders[pose.Name] end
                        if not holder then
                            unmatched = unmatched + 1
                        elseif root.Name ~= holder.Name then
                            root.Name = holder.Name
                            renamed = renamed + 1
                        end
                    end
                end
            end
        end
    end
    local line = string.format("%s: %d MeshParts set to white, %d root poses renamed in %d animations, %d names tidied",
        model.Name, whitened, renamed, sequences, tidied)
    if unmatched > 0 then
        line = line .. string.format(" (%d root poses left alone: none of their bones is in this model)", unmatched)
    end
    return line
end

local models, seen = {}, {}
for _, item in ipairs(game:GetService("Selection"):Get()) do
    local model = item:IsA("Model") and item or item:FindFirstAncestorOfClass("Model")
    if model and not seen[model] then
        seen[model] = true
        table.insert(models, model)
    end
end
local lines = {}
for _, model in ipairs(models) do table.insert(lines, fixModel(model)) end
if #lines == 0 then lines = {"Select the imported models in Explorer first."} end
local report = table.concat(lines, "\n")
print(report)
return report
