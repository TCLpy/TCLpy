# ==============================================================================
# init.tcl — Engine Globals & State Initialization
# ==============================================================================

namespace eval world {
    variable entities
    array set entities {}
}

namespace eval events {
    variable handlers
    array set handlers {}
}

engine_log "[*] Tcl Core Subsystems Initialized."