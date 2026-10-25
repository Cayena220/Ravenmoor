-- Ordered arc-length resampling prevents a stationary point or shuffled rune from passing.
local G = {}
function G.Path(index)
    if index % 3 == 0 then return {{0.15,0.75},{0.35,0.2},{0.55,0.75},{0.8,0.2}} end
    if index % 3 == 1 then return {{0.18,0.25},{0.8,0.25},{0.2,0.75},{0.82,0.75}} end
    local p = {}
    for i = 0, 20 do
        local t = i / 20 * math.pi * 1.8
        p[#p+1] = {0.5 + math.cos(t) * 0.32, 0.5 + math.sin(t) * 0.32}
    end
    return p
end
local function dist(a,b) return math.sqrt((a[1]-b[1])^2+(a[2]-b[2])^2) end
function G.Resample(points, count)
    local lens, total = {0}, 0
    for i = 2, #points do total = total + dist(points[i], points[i-1]); lens[i] = total end
    if total < 0.1 then return nil end
    local result, j = {}, 2
    for i = 0, count-1 do
        local d = total * i / (count-1)
        while j < #points and lens[j] < d do j = j+1 end
        local t = (d-lens[j-1]) / math.max(0.00001, lens[j]-lens[j-1])
        result[#result+1] = {points[j-1][1]+(points[j][1]-points[j-1][1])*t, points[j-1][2]+(points[j][2]-points[j-1][2])*t}
    end
    return result
end
function G.Score(points, path)
    if type(points) ~= "table" or #points < 8 or #points > 160 then return 0 end
    for _, p in ipairs(points) do
        if type(p) ~= "table" or type(p[1]) ~= "number" or type(p[2]) ~= "number"
            or p[1] ~= p[1] or p[2] ~= p[2] or p[1] < 0 or p[1] > 1 or p[2] < 0 or p[2] > 1 then return 0 end
    end
    local a, b = G.Resample(points, 32), G.Resample(path, 32)
    if not a or not b then return 0 end
    local error = 0
    for i = 1, 32 do error = error + dist(a[i], b[i]) end
    return math.max(0, math.floor(100 * (1 - error / 32 / 0.28)))
end
return G
