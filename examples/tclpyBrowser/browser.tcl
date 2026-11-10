# browser.tcl - TCLpy Web Browser Interface Layer

# --- HEADER & CONTROLS SETUP ---
proc CreateBrowserUI {} {
    # Main action frame below toolbar
    set action_frame [ttk::frame .actions -padding {5 5 5 5}]
    pack $action_frame -fill x

    # Bookmark Quick-Bar Frame
    set bm_frame [ttk::frame .bookmarks -padding {5 0 5 5}]
    pack $bm_frame -fill x

    # Populate default quick links if available from bookmarks.tcl
    if {[info commands GetBookmarks] ne ""} {
        foreach bm [GetBookmarks] {
            set name [dict get $bm name]
            set url [dict get $bm url]
            ttk::button $bm_frame.btn_$name -text $name -command "set_url $url; navigate $url"
            pack $bm_frame.btn_$name -side left -padx 2
        }
    }
}

# Auto-initialize UI layout components
CreateBrowserUI()

