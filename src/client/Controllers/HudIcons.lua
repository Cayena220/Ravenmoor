-- White-line HUD icons drawn from Frames, so the place needs no image assets. Each glyph is a list of strokes
-- in a unit square: lines {x1,y1,x2,y2}, rings {x,y,diameter}, boxes {x,y,w,h,radius,rotation} and diamonds
-- {x,y,size,filled}. Rings, boxes and hollow diamonds are outlines; a filled diamond or a dot is solid.
local H={}
local LINE=Color3.fromRGB(244,239,228)
local glyphs={
    flame={{"ring",0.5,0.64,0.46},{"line",0.5,0.08,0.27,0.56},{"line",0.5,0.08,0.73,0.56},{"dot",0.5,0.68,0.14}},
    snowflake={{"line",0.5,0.08,0.5,0.92},{"line",0.14,0.29,0.86,0.71},{"line",0.14,0.71,0.86,0.29},{"diamond",0.5,0.5,0.2,true}},
    bolt={{"line",0.64,0.06,0.34,0.52},{"line",0.34,0.52,0.66,0.48},{"line",0.66,0.48,0.36,0.94}},
    leaf={{"box",0.55,0.42,0.4,0.66,0.5,40},{"line",0.38,0.62,0.18,0.9},{"line",0.38,0.62,0.7,0.24}},
    shield={{"line",0.18,0.16,0.82,0.16},{"line",0.18,0.16,0.18,0.54},{"line",0.82,0.16,0.82,0.54},{"line",0.18,0.54,0.5,0.88},{"line",0.82,0.54,0.5,0.88}},
    spark={{"line",0.5,0.06,0.5,0.94},{"line",0.06,0.5,0.94,0.5},{"diamond",0.5,0.5,0.34,true}},
    burst={{"ring",0.5,0.5,0.34},{"line",0.5,0.04,0.5,0.28},{"line",0.5,0.72,0.5,0.96},{"line",0.04,0.5,0.28,0.5},{"line",0.72,0.5,0.96,0.5},
        {"line",0.18,0.18,0.32,0.32},{"line",0.68,0.68,0.82,0.82},{"line",0.82,0.18,0.68,0.32},{"line",0.32,0.68,0.18,0.82}},
    stone={{"box",0.5,0.56,0.66,0.52,0.18,10},{"line",0.38,0.38,0.52,0.6},{"line",0.52,0.6,0.46,0.76}},
    shadow={{"ring",0.5,0.5,0.7},{"dot",0.62,0.4,0.4}},
    bag={{"box",0.5,0.62,0.66,0.54,0.14,0},{"box",0.5,0.3,0.3,0.26,0.5,0},{"line",0.17,0.56,0.83,0.56},{"dot",0.5,0.56,0.12}},
    broom={{"line",0.88,0.1,0.45,0.53},{"diamond",0.45,0.53,0.16,true},{"line",0.45,0.53,0.1,0.7},{"line",0.45,0.53,0.17,0.86},{"line",0.45,0.53,0.3,0.92}},
    flask={{"line",0.32,0.08,0.68,0.08},{"line",0.42,0.08,0.42,0.38},{"line",0.58,0.08,0.58,0.38},{"ring",0.5,0.65,0.54},{"dot",0.5,0.72,0.26}},
    book={{"box",0.5,0.5,0.66,0.78,0.06,0},{"line",0.28,0.11,0.28,0.89},{"line",0.4,0.38,0.7,0.38},{"line",0.4,0.54,0.7,0.54}},
    dodge={{"line",0.16,0.22,0.44,0.5},{"line",0.44,0.5,0.16,0.78},{"line",0.5,0.22,0.78,0.5},{"line",0.78,0.5,0.5,0.78}},
    lance={{"line",0.14,0.86,0.76,0.24},{"diamond",0.78,0.22,0.24,true},{"line",0.22,0.62,0.38,0.78}},
    lock={{"box",0.5,0.66,0.62,0.44,0.1,0},{"box",0.5,0.36,0.36,0.44,0.5,0},{"dot",0.5,0.66,0.12}},
    plus={{"line",0.5,0.2,0.5,0.8},{"line",0.2,0.5,0.8,0.5}},
    arrow={{"line",0.5,0.06,0.18,0.9},{"line",0.5,0.06,0.82,0.9},{"line",0.18,0.9,0.5,0.68},{"line",0.82,0.9,0.5,0.68},{"line",0.5,0.2,0.5,0.68}},
}
H.Glyphs=glyphs
local function frame(parent,color,props)
    local f=Instance.new("Frame"); f.BorderSizePixel=0; f.BackgroundColor3=color; f.AnchorPoint=Vector2.new(0.5,0.5)
    for k,v in pairs(props) do f[k]=v end; f.Parent=parent; return f
end
local function outline(f,color,thick)
    f.BackgroundTransparency=1
    local s=Instance.new("UIStroke"); s.Color=color; s.Thickness=thick; s.Parent=f
end
local function round(f,radius) local c=Instance.new("UICorner"); c.CornerRadius=UDim.new(radius,0); c.Parent=f end
-- Draws `name` centred in `parent`, `size` pixels square. An unknown name draws `fallback` (a letter) instead.
function H.Draw(name,parent,size,color,fallback)
    color=color or LINE
    local box=Instance.new("Frame"); box.Name="Icon"; box.BackgroundTransparency=1; box.AnchorPoint=Vector2.new(0.5,0.5)
    box.Position=UDim2.fromScale(0.5,0.5); box.Size=UDim2.fromOffset(size,size); box.ZIndex=parent.ZIndex; box.Parent=parent
    -- Thinner than 2px, a level stroke can drop out entirely once the HUD is scaled down.
    local thick=math.max(2,math.floor(size*0.075*2+0.5)/2); local z=box.ZIndex
    local glyph=glyphs[name]
    if not glyph then
        local label=Instance.new("TextLabel"); label.BackgroundTransparency=1; label.Size=UDim2.fromScale(1,1); label.Text=fallback or "?"
        label.Font=Enum.Font.Garamond; label.TextScaled=true; label.TextColor3=color; label.ZIndex=z; label.Parent=box
        return box
    end
    for _,s in ipairs(glyph) do
        local kind=s[1]
        if kind=="line" then
            local dx,dy=s[4]-s[2],s[5]-s[3]
            frame(box,color,{Position=UDim2.fromScale((s[2]+s[4])/2,(s[3]+s[5])/2),Size=UDim2.new(math.sqrt(dx*dx+dy*dy),thick,0,thick),
                Rotation=math.deg(math.atan2(dy,dx)),ZIndex=z})
        elseif kind=="ring" then
            local f=frame(box,color,{Position=UDim2.fromScale(s[2],s[3]),Size=UDim2.fromScale(s[4],s[4]),ZIndex=z}); round(f,0.5); outline(f,color,thick)
        elseif kind=="dot" then
            local f=frame(box,color,{Position=UDim2.fromScale(s[2],s[3]),Size=UDim2.fromScale(s[4],s[4]),ZIndex=z}); round(f,0.5)
        elseif kind=="box" then
            local f=frame(box,color,{Position=UDim2.fromScale(s[2],s[3]),Size=UDim2.fromScale(s[4],s[5]),Rotation=s[7] or 0,ZIndex=z})
            if s[6]>0 then round(f,s[6]) end; outline(f,color,thick)
        elseif kind=="diamond" then
            local f=frame(box,color,{Position=UDim2.fromScale(s[2],s[3]),Size=UDim2.fromScale(s[4],s[4]),Rotation=45,ZIndex=z})
            if not s[5] then outline(f,color,thick) end
        end
    end
    return box
end
-- Recolours an icon drawn by Draw.
function H.Tint(box,color)
    for _,d in ipairs(box:GetDescendants()) do
        if d:IsA("UIStroke") then d.Color=color
        elseif d:IsA("TextLabel") then d.TextColor3=color
        elseif d:IsA("Frame") then d.BackgroundColor3=color end
    end
end
-- The glyph for a spell: its element first (fire, frost, lightning), then its school.
local ELEMENTS={Fire="flame",Frost="snowflake",Lightning="bolt"}
local SCHOOLS={Ward="shield",Restoration="leaf",Alteration="stone",Charm="spark",Hex="burst",Shadow="shadow"}
function H.ForSpell(spell)
    if not spell then return "plus" end
    if spell.Id=="Scintara" then return "spark" end
    return ELEMENTS[spell.Element] or SCHOOLS[spell.School] or "spark"
end
return H
