import torch
import time

# Create two tensors
a = torch.tensor([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
b = torch.tensor([4, 5, 6, 7, 8, 9, 10, 11, 12, 13])

# Element-wise addition
result = a + b

for i in range(100):
    start_time = time.time()
    result = a + b
    print(result)
    end_time = time.time()
    execution_time = end_time - start_time
    print("Execution time:", execution_time, "seconds")