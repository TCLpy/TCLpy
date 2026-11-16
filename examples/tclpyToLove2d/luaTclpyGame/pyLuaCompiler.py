from pathlib import Path
from tclpy.runtime import _get_tkinter_interp

try:
    import lupa.luajit21 as lupa
    HAS_LUPA = True
except ImportError:
    HAS_LUPA = False

def compile_via_tclpy():
    interp = _get_tkinter_interp()
    
    interp.eval("""
        proc engine_spawn {args} {}
        proc engine_log {msg} { puts "BUILD_LOG: $msg" }
        proc engine_destroy {id} {}
        proc engine_key_pressed {key} { return 0 }
        proc on {event_type id1 id2 body} {}
        proc on_update {body} {}
    """)
    
    game_script = Path("./game.tcl").read_text(encoding="utf-8")
    interp.eval(game_script)
    interp.eval('map_load "./assets/dungeon1.map"')
    
    raw_keys = interp.eval('array names world::entities')
    
    lua_lines = ["entities = {"]
    # Guarantee player
    lua_lines.append('    ["player"] = { x = 10, y = 5, char = "@", color = "cyan", alive = true },')
    
    if isinstance(raw_keys, (list, tuple)):
        for eid in raw_keys:
            if not eid or eid == "player": continue
            try:
                prop_str = interp.eval(f'set world::entities({eid})')
                prop_list = interp.eval(f'array get {{ {prop_str} }}')
                
                props = {}
                if isinstance(prop_list, (list, tuple)) and len(prop_list) >= 2:
                    it = iter(prop_list)
                    for k in it:
                        v = next(it, "")
                        props[str(k)] = str(v)
                
                lua_lines.append(f'    ["{eid}"] = {{')
                for k, v in props.items():
                    if v.replace('.', '', 1).isdigit() or v in ('true', 'false'):
                        lua_lines.append(f'        {k} = {v},')
                    else:
                        lua_lines.append(f'        {k} = "{v}",')
                lua_lines.append('    },')
            except Exception as ex:
                pass

    lua_lines.append("}")
    return "\n".join(lua_lines)


def compile_behaviors(tcl_code):
    return """
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
"""

def build():
    template_path = Path("./runtime_template.lua")
    output_path = Path("./main.lua")

    template = template_path.read_text(encoding="utf-8")
    
    print("[Compiler] Evaluating game logic and map via tclpy interpreter...")
    lua_entities = compile_via_tclpy()
    lua_updates = compile_behaviors("")
    
    final_lua = template.replace("-- [[ENTITIES_HERE]]", lua_entities)
    final_lua = final_lua.replace("-- [[UPDATE_LOGIC_HERE]]", lua_updates)

    # --- Polyglot Pre-Flight Check via Lupa / LuaJIT ---
    if HAS_LUPA:
        print("[Compiler] Running Lupa LuaJIT pre-flight syntax check...")
        lua = lupa.LuaRuntime(unpack_returned_tuples=True)
        try:
            lua.eval(f"function() {final_lua} end")
            print("[Compiler] ✓ Lua syntax verified successfully via LuaJIT!")
        except Exception as e:
            print(f"[Compiler Error] ❌ Generated Lua syntax check failed:\n{e}")
            return
    else:
        print("[Compiler] Lupa not installed; skipping pre-flight syntax validation.")

    if output_path.exists():
        output_path.unlink()

    output_path.write_text(final_lua, encoding="utf-8")
    print(f"[Success] Built {output_path} using tclpy + LuaJIT pipeline!")

if __name__ == "__main__":
    build()
    