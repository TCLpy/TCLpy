-- ==========================================================
-- Love2D Runtime Template for TCLpy
-- ==========================================================
entities = {}

local colors = {
    cyan    = {0, 1, 1},
    green   = {0, 1, 0},
    yellow  = {1, 1, 0},
    magenta = {1, 0, 1},
    white   = {1, 1, 1},
    gray    = {0.5, 0.5, 0.5},
    red     = {1, 0, 0}
}

local update_timer = 0

function love.update(dt)
    update_timer = update_timer + dt
    if update_timer >= 0.15 then
        update_timer = 0
        
        -- Poll engine inputs if defined or update player position based on active keys
        local p = entities["player"]
        if p and p.alive ~= false then
            local nx, ny = p.x, p.y
            if engine_key_pressed("left") or engine_key_pressed("a") then nx = nx - 1
            elseif engine_key_pressed("right") or engine_key_pressed("d") then nx = nx + 1
            elseif engine_key_pressed("up") or engine_key_pressed("w") then ny = ny - 1
            elseif engine_key_pressed("down") or engine_key_pressed("s") then ny = ny + 1 end
            
            if nx ~= p.x or ny ~= p.y then
                p.x, p.y = nx, ny
            end
        end
    end
    
    update_timer = update_timer + dt
    if update_timer >= 0.3 then
        update_timer = 0
        local g = entities["goblin"]
        local p = entities["player"]
        if g and p then
            if g.x < p.x then g.x = g.x + 1
            elseif g.x > p.x then g.x = g.x - 1 end
            if g.y < p.y then g.y = g.y + 1
            elseif g.y > p.y then g.y = g.y - 1 end
        end
    end

end

-- Dynamic D-Pad geometry helper (adapts to any mobile screen resolution)
local function get_dpad_buttons()
    local w, h = love.graphics.getDimensions()
    local btn = 68
    local pad = 24
    local base_x = pad
    local base_y = h - (btn * 3) - pad

    return {
        up    = {x = base_x + btn,     y = base_y,           w = btn, h = btn, label = "^"},
        down  = {x = base_x + btn,     y = base_y + btn * 2, w = btn, h = btn, label = "v"},
        left  = {x = base_x,           y = base_y + btn,     w = btn, h = btn, label = "<"},
        right = {x = base_x + btn * 2, y = base_y + btn,     w = btn, h = btn, label = ">"}
    }
end

local active_keys = {}

function love.keypressed(key)
    active_keys[key] = true
    if key == "escape" then
        love.event.quit()
    end
end

function love.keyreleased(key)
    active_keys[key] = false
end

function love.mousepressed(x, y, button)
    local btns = get_dpad_buttons()
    
    -- Reset directional flags on click
    active_keys["up"] = (x >= btns.up.x and x <= btns.up.x + btns.up.w and y >= btns.up.y and y <= btns.up.y + btns.up.h)
    active_keys["down"] = (x >= btns.down.x and x <= btns.down.x + btns.down.w and y >= btns.down.y and y <= btns.down.y + btns.down.h)
    active_keys["left"] = (x >= btns.left.x and x <= btns.left.x + btns.left.w and y >= btns.left.y and y <= btns.left.y + btns.left.h)
    active_keys["right"] = (x >= btns.right.x and x <= btns.right.x + btns.right.w and y >= btns.right.y and y <= btns.right.y + btns.right.h)
end

function love.mousereleased(x, y, button)
    active_keys["up"] = false
    active_keys["down"] = false
    active_keys["left"] = false
    active_keys["right"] = false
end

-- Stub or map engine_key_pressed so Tcl's input logic evaluates correctly
function engine_key_pressed(key)
    if key == "left" then return active_keys["left"] or active_keys["a"]
    elseif key == "right" then return active_keys["right"] or active_keys["d"]
    elseif key == "up" then return active_keys["up"] or active_keys["w"]
    elseif key == "down" then return active_keys["down"] or active_keys["s"]
    elseif key == "space" then return active_keys["space"]
    end
    return false
end

function love.load()
    love.window.setTitle("TCLpy Gauntlet")
end

function love.touchpressed(id, x, y, dx, dy, pressure)
    local p = entities["player"]
    if not p then return end

    local btns = get_dpad_buttons()
    if x >= btns.up.x and x <= btns.up.x + btns.up.w and y >= btns.up.y and y <= btns.up.y + btns.up.h then
        p.y = p.y - 1
    elseif x >= btns.down.x and x <= btns.down.x + btns.down.w and y >= btns.down.y and y <= btns.down.y + btns.down.h then
        p.y = p.y + 1
    elseif x >= btns.left.x and x <= btns.left.x + btns.left.w and y >= btns.left.y and y <= btns.left.y + btns.left.h then
        p.x = p.x - 1
    elseif x >= btns.right.x and x <= btns.right.x + btns.right.w and y >= btns.right.y and y <= btns.right.y + btns.right.h then
        p.x = p.x + 1
    end
end

entities = {
    ["player"] = { x = 10, y = 5, char = "@", color = "cyan", alive = true },
}

function love.draw()
    love.graphics.clear(0.1, 0.1, 0.15)
    love.graphics.setColor(1, 1, 1)
    love.graphics.print("TCLpy Love2D Runtime", 20, 20)

    local tile_size = 32
    for id, ent in pairs(entities) do
        local x = (ent.x or 0) * tile_size + 20
        local y = (ent.y or 0) * tile_size + 60
        local char = tostring(ent.char or "?")
        local col = colors[ent.color] or colors.white

        love.graphics.setColor(col)
        love.graphics.print(char, x, y, 0, 2, 2)
    end

    -- Draw D-Pad anchored cleanly to bottom-left of actual screen height
    local btns = get_dpad_buttons()
    for _, b in pairs(btns) do
        love.graphics.setColor(0.3, 0.3, 0.4, 0.85)
        love.graphics.rectangle("fill", b.x, b.y, b.w, b.h, 8)
        love.graphics.setColor(1, 1, 1)
        love.graphics.print(b.label, b.x + 24, b.y + 16, 0, 2, 2)
    end
end
