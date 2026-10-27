-- All tuning lives here or in the data modules. No asset downloads are required.
return {
    Version = "0.1.0", LevelCap = 20, WalkSpeed = 16, RespawnTime = 5,
    StudioSaves = false, DataStoreName = "Wandbound_Alpha_v1",
    SaveInterval = 60, LockLifetime = 180, MaxMonsters = 25,
    ClassInterval = 300, LessonRewardCooldown = 120, DayLength = 1200,
    Houses = {
        Emberclaw = {Trait = "Courage", Color = {187, 71, 63}, Perk = "+5% attack power"},
        Stoneroot = {Trait = "Loyalty", Color = {204, 156, 64}, Perk = "+5% health and shields"},
        Skyquill = {Trait = "Wisdom", Color = {83, 145, 207}, Perk = "5% shorter cooldowns"},
        Nightfang = {Trait = "Ambition", Color = {75, 163, 123}, Perk = "+5% duel XP and Gilders"},
    },
    HouseOrder = {"Emberclaw", "Stoneroot", "Skyquill", "Nightfang"},
    SortingQuestions = {
        {Q = "A sealed door blocks your path. What do you do?", A = {"Break the seal", "Wait for your friends", "Study the inscription", "Find another entrance"}},
        {Q = "A classmate drops their wand during a duel.", A = {"Stand between them", "Help them recover", "Distract their opponent", "Use the opening wisely"}},
        {Q = "Which discovery matters most?", A = {"A dangerous new spell", "A cure for a friend", "An ancient library", "A secret passage"}},
        {Q = "Your group is lost in Whisperwood.", A = {"Lead the way", "Keep everyone together", "Read the stars", "Follow a hidden trail"}},
        {Q = "What will Ravenmoor remember you for?", A = {"My courage", "My loyalty", "My wisdom", "My ambition"}},
    },
    Zones = {
        {Id = "Castle", Name = "Ravenmoor Academy", Center = {94, -164}, Size = {176, 220}, Safe = true},
        {Id = "Whisperwood", Name = "Whisperwood", Center = {-155, -35}, Size = {270, 400}, Safe = false},
        {Id = "Hollowmere", Name = "Hollowmere Village", Center = {90, 140}, Size = {260, 155}, Safe = true},
        {Id = "Grounds", Name = "Castle Grounds", Center = {100, 0}, Size = {270, 130}, Safe = true},
    },
    Waystones = {Hollowmere = {90, 5, 164}, Castle = {85, 5, -58}, Whisperwood = {-36, 5, 20}},
    Teachers = {
        Hex = {Name = "Professor Rook", Title = "Hexcraft", Anchor = "Teacher_Hex"},
        Ward = {Name = "Professor Holloway", Title = "Warding", Anchor = "Teacher_Ward"},
        Charm = {Name = "Professor Quill", Title = "Charms", Anchor = "Teacher_Charm"},
        Restoration = {Name = "Healer Fenn", Title = "Restoration", Anchor = "Teacher_Restoration"},
        Alteration = {Name = "Professor Ashgrove", Title = "Alteration", Anchor = "Teacher_Alteration"},
    },
    Subjects = {"Charm", "Hex", "Ward", "Restoration", "Alteration"},
}
