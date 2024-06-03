import time

# Perform a small operation to measure
def small_operation():
    x = 0
    for _ in range(99999999):
        x += 1
    return x

# Measure the small operation time
start_time = time.time_ns()
small_operation()
end_time = time.time_ns()

elapsed_time = (end_time - start_time)*(10**-6) # Convert to microseconds
print(f"Elapsed time using time_ns: {elapsed_time:.3f} ms")