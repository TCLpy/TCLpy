import os
import sys
import lupa.luajit21 as lupa

# Locate Python's DLLs and Tcl/Tk script libraries automatically
py_dir = os.path.dirname(sys.executable)
dll_dir = os.path.join(py_dir, "DLLs")
tcl_lib = os.path.join(py_dir, "tcl", "tcl8.6")
tk_lib = os.path.join(py_dir, "tcl", "tk8.6")

# Ensure Windows can locate tcl86t.dll, tk86t.dll, and init.tcl
os.environ["TCL_LIBRARY"] = tcl_lib
os.environ["TK_LIBRARY"] = tk_lib
os.add_dll_directory(dll_dir)

lua = lupa.LuaRuntime()
lua.globals().dll_dir = dll_dir

lua.execute("""
    local ffi = require("ffi")

    ffi.cdef[[
        typedef struct Tcl_Interp Tcl_Interp;
        Tcl_Interp *Tcl_CreateInterp(void);
        int Tcl_Init(Tcl_Interp *interp);
        int Tk_Init(Tcl_Interp *interp);
        int Tcl_Eval(Tcl_Interp *interp, const char *script);
        const char *Tcl_GetStringResult(Tcl_Interp *interp);
        void Tk_MainLoop(void);
    ]]

    local tcl = ffi.load(dll_dir .. "\\\\tcl86t.dll")
    local tk  = ffi.load(dll_dir .. "\\\\tk86t.dll")

    local interp = tcl.Tcl_CreateInterp()
    assert(tcl.Tcl_Init(interp) == 0, ffi.string(tcl.Tcl_GetStringResult(interp)))
    assert(tk.Tk_Init(interp) == 0, ffi.string(tcl.Tcl_GetStringResult(interp)))

    tcl.Tcl_Eval(interp, [[
        wm title . "LuaJIT FFI + Tk"
        label .lbl -text "Running natively from LuaJIT FFI!" -padx 20 -pady 10
        button .btn -text "Close" -command { exit }
        pack .lbl .btn -pady 5
    ]])

    tk.Tk_MainLoop()
""")

