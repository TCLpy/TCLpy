###quick cheat sheet of your active DSL surface:

shape -> Row and column counts

stats -> Dataset summary statistics

head [n] -> Top n records

sort <col> [asc|desc] -> 
Sort DataFrame by column

query <expr> -> 
Vectorized boolean expressions 
(e.g. text.str.contains('clove', case=False))

# search for specify user
ex: author_search DrMindyPelz

sort likes desc

top_authors 10