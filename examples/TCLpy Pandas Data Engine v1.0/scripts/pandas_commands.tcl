proc df_analyst {cmd args} {
    switch -- $cmd {
        where -
        query {
            py_df_query [join $args " "]
        }
        sort {
            py_df_sort {*}$args
        }
        stats -
        describe {
            py_df_stats
        }
        head {
            py_df_head {*}$args
        }
        nlargest {
            # Usage: nlargest <n> <column>
            py_df_nlargest {*}$args
        }
		shape {
         py_df_shape
		}
		columns -
		colname {
         py_df_colName
		}
		authors {
         # Usage: authors [n]
         py_df_authors {*}$args
		}
		author_search {
            # Usage: author_search <username>
            py_df_author_search {*}$args
        }
		author_stats {
            # Usage: author_stats <username>
            py_df_author_stats {*}$args
        }
		top_authors {
            # Usage: top_authors [n] (default 10)
            py_df_top_authors {*}$args
        }
		exclude_authors -
        exclude {
            # Usage: exclude_author <username_pattern>
            py_df_exclude_author {*}$args
        }
        help {
            puts "\n=== TCLpy Pandas Command Reference ==="
            puts "  query <expr>      - Pandas vector query (e.g. 'likes > 5')"
            puts "  sort <col> [asc|desc] - Sort DataFrame by column"
            puts "  head [n]          - View top n rows"
            puts "  nlargest <n> <col> - Show top n rows by column"
            puts "  stats             - Display summary statistics"
            puts "=======================================\n"
        }
        default {
            puts "Unknown command: '$cmd'. Type 'help' for syntax."
        }
    }
}