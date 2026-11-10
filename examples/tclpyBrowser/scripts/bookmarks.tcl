# scripts/bookmarks.tcl - Managed Bookmark Collections

proc GetBookmarks {} {
    return [list \
        [list name "HTML Test" url "https://httpbin.org/html"] \
        [list name "Google Logo" url "https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_92x30dp.png"] \
    ]
}
