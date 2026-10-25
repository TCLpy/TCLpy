# tests/stress_test.py
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from runtime import execute_tcl

def run_test(name, tcl_code, verify_func=None):
    print(f"\n==========================================")
    print(f" Running Test: {name}")
    print(f"==========================================")
    
    env = {}
    start_time = time.time()
    try:
        execute_tcl(tcl_code, env)
        elapsed = (time.time() - start_time) * 1000
        print(f"Status: PASSED")
        print(f"Execution Time: {elapsed:.2f} ms")
        if verify_func:
            verify_func(env)
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        print(f"Status: FAILED after {elapsed:.2f} ms")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise e

def test_tight_loop():
    code = """
    set total 0
    set i 0
    while {$i < 100000} {
        set total [expr {$total + $i}]
        incr i
    }
    """
    def check(env):
        val = env.get("total")
        print(f"Result Verified: total = {val}")
        assert val == 4999950000
    run_test("100,000 Iteration Tight Loop", code, check)

def test_deep_recursion():
    code = """
    proc fib {n} {
        if {$n <= 1} {
            return $n
        }
        set n1 [expr {$n - 1}]
        set n2 [expr {$n - 2}]
        return [expr {[fib $n1] + [fib $n2]}]
    }
    set result [fib 20]
    """
    def check(env):
        val = env.get("result")
        print(f"Result Verified: fib(20) = {val}")
        assert val == 6765
    run_test("Recursive Fibonacci (fib(20))", code, check)

def test_nested_loops():
    code = """
    set count 0
    set i 0
    while {$i < 100} {
        set j 0
        while {$j < 100} {
            incr count
            incr j
        }
        incr i
    }
    """
    def check(env):
        val = env.get("count")
        print(f"Result Verified: 100x100 nested loop count = {val}")
        assert val == 10000
    run_test("100x100 Nested Loops", code, check)

def test_python_interop_stress():
    code = """
    set i 1
    while {$i <= 10000} {
        set res [expr {math::sqrt($i)}]
        incr i
    }
    """
    def check(env):
        print("Result Verified: 10,000 Python math calls executed successfully.")
    run_test("10,000 Python Standard Math Library Calls", code, check)

def test_list_manipulation():
    code = """
    set mylist {}
    set i 0
    while {$i < 5000} {
        lappend mylist $i
        incr i
    }
    set len [llength $mylist]
    set val [lindex $mylist 2500]
    """
    def check(env):
        l_len = env.get("len")
        val = env.get("val")
        print(f"Result Verified: list length = {l_len}, middle index value = {val}")
        assert l_len == 5000
        assert str(val) == "2500"
    run_test("5,000 List Appends & Index Access", code, check)

if __name__ == "__main__":
    print("==========================================")
    print("          TCLPY STRESS TEST SUITE         ")
    print("==========================================")
    test_tight_loop()
    test_deep_recursion()
    test_nested_loops()
    test_python_interop_stress()
    test_list_manipulation()
    print("\n==========================================")
    print("      ALL STRESS TESTS COMPLETED!         ")
    print("==========================================")
