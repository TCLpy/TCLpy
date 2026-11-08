# 1. Initialize the Knight Dialer graph and counting logic in Python via py_exec
py_exec {
    def count_dialer_paths(start_digit, hops):
        moves = {
            0: [4, 6],
            1: [6, 8],
            2: [7, 9],
            3: [4, 8],
            4: [0, 3, 9],
            5: [],
            6: [0, 1, 7],
            7: [2, 6],
            8: [1, 3],
            9: [2, 4]
        }
        
        dp = {i: 1 for i in range(10)}
        
        for _ in range(hops):
            new_dp = {i: 0 for i in range(10)}
            for digit, count in dp.items():
                for next_digit in moves[digit]:
                    new_dp[next_digit] += count
            dp = new_dp
            
        return dp[start_digit]
}

# 2. Define helper function for total paths across all keys
py_exec {
    def total_dialer_paths(hops):
        return sum(count_dialer_paths(d, hops) for d in range(10))
}

# 3. Test from Tcl: Calculate paths for a specific start digit and hop count
py_exec {
    start_key = 1
    num_hops = 3
    result_paths = count_dialer_paths(start_key, num_hops)
}

# Retrieve variables from Python resident state into Tcl variables
set path_result [py_eval {result_paths}]
set start_key [py_eval {start_key}]
set num_hops [py_eval {num_hops}]

puts "Number of phone numbers of length [expr {$num_hops + 1}] starting at $start_key: $path_result"

# 4. Total possible phone numbers across ALL starting digits for 10 hops
py_exec {
    total_10_hops = total_dialer_paths(10)
}
set grand_total [py_eval {total_10_hops}]
puts "Total distinct phone numbers of length 11 across all start keys: $grand_total"
