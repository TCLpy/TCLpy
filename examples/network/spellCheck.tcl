# 1. Handle secure networking and corpus ingestion in Python
py_exec {
    import urllib.request
    import re
    from collections import Counter

    print("[*] Fetching Norvig corpus securely via Python...")
    req = urllib.request.Request("https://www.norvig.com/big.txt", headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        fetched_text = response.read().decode('utf-8')

    print("[*] Parsing corpus tokens and building frequency matrix...")
    clean_text = fetched_text.lower()
    word_tokens = re.findall(r'[a-z]+', clean_text)
    
    # Store globally in Python workspace
    global WORD_COUNTS
    WORD_COUNTS = dict(Counter(word_tokens))
    print(f"[*] Corpus compiled successfully! Total unique words tracked: {len(WORD_COUNTS)}")
}

# 2. Tcl Combinatorics & Spell Correction Logic using Python bridge helpers
proc get_edits_1 {word} {
    set alphabet {a b c d e f g h i j k l m n o p q r s t u v w x y z}
    set len [string length $word]
    set splits [list]
    
    for {set i 0} {$i <= $len} {incr i} {
        lappend splits [list [string range $word 0 [expr {$i - 1}]] [string range $word $i end]]
    }
    
    set edits [list]
    foreach split $splits {
        lassign $split left right
        set r_len [string length $right]
        
        if {$r_len > 0} {
            lappend edits "$left[string range $right 1 end]"
        }
        if {$r_len > 1} {
            set r0 [string index $right 0]
            set r1 [string index $right 1]
            lappend edits "$left$r1$r0[string range $right 2 end]"
        }
        foreach c $alphabet {
            if {$r_len > 0} {
                lappend edits "$left$c[string range $right 1 end]"
            }
            lappend edits "$left$c$right"
        }
    }
    return [lsort -unique $edits]
}

proc get_edits_2 {word} {
    set result [list]
    foreach e1 [get_edits_1 $word] {
        lappend result {*}[get_edits_1 $e1]
    }
    return [lsort -unique $result]
}

proc word_exists {w} {
    return [py_eval "int(\"$w\" in WORD_COUNTS)"]
}

proc get_word_freq {w} {
    return [py_eval "WORD_COUNTS.get(\"$w\", 0)"]
}

proc filter_known {words_list} {
    set known [list]
    foreach w $words_list {
        if {[word_exists $w]} {
            lappend known $w
        }
    }
    return $known
}

proc correct {word} {
    set word [string tolower [string trim $word]]
    
    if {[word_exists $word]} {
        return $word
    }
    
    set candidates [filter_known [get_edits_1 $word]]
    if {[llength $candidates] == 0} {
        set candidates [filter_known [get_edits_2 $word]]
    }
    if {[llength $candidates] == 0} {
        return $word
    }
    
    set best_match ""
    set max_frequency -1
    foreach cand $candidates {
        set freq [get_word_freq $cand]
        if {$freq > $max_frequency} {
            set max_frequency $freq
            set best_match $cand
        }
    }
    return $best_match
}

# 3. Interactive Test Bench REPL
puts "\n=== Hybrid Spelling Correction Engine Active ==="
puts "Type a misspelled word (e.g.,'spelling', 'theh', 'mpy'), or 'exit' to quit.\n"

while {1} {
    puts -nonewline "intel_query> "
    flush stdout
    gets stdin input_line
    
    set trimmed_input [string trim $input_line]
    if {$trimmed_input eq "exit" || $trimmed_input eq ""} {
        if {$trimmed_input eq "exit"} {
            puts "Exiting spell check engine."
        }
        break
    }
    
    set correction [correct $trimmed_input]
    puts " -> Correction Vector: \[$correction\]\n"
}
