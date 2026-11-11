# scripts/commands.tcl - Hot-Reloadable Analyst DSL Dispatcher

proc analyst {cmd args} {
    switch -- $cmd {
        filter {
            py_filter {*}$args
        }
        sort {
            py_sort {*}$args
        }
        extract {
            py_extract {*}$args
        }
        stats {
            py_stats
        }
        help {
            puts "\n=== TCLpy Analyst Console Help ==="
            puts "  filter keyword \"term\"    - Find comments containing term"
            puts "  filter author \"name\"     - Find comments by author"
            puts "  filter length > <num>    - Find comments longer than num chars"
            puts "  sort length asc|desc     - Sort dataset by comment length"
            puts "  sort author asc|desc     - Sort dataset alphabetically by author"
            puts "  extract author           - List all unique authors"
            puts "  stats                    - View dataset metrics"
            puts "==================================\n"
        }
        default {
            puts "Unknown DSL command: '$cmd'. Type 'help' for valid options."
        }
    }
}
