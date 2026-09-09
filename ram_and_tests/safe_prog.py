import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory import RAM

def run_safe_execution():
    print("--- Running Safe Execution Test ---")
    ram = RAM()
    
    # Simulate a program allocating 4 bytes of memory
    allocated_size = 4
    print(f"Program allocated {allocated_size} bytes of memory (Addresses 0 to 3).")
    
    # Write exactly within the bounds
    print("Writing data safely within bounds...")
    for i in range(allocated_size):
        ram.write(i, (i + 1) * 10)  # Writing values 10, 20, 30, 40
        
    print("\nReading data back to verify...")
    for i in range(allocated_size):
        value = ram.read(i)
        print(f"Address {i}: {value}")
        
    print("\n[+] Safe execution completed successfully. No boundaries violated.")
    print(f"Total CPU Cycles Used: {ram.get_cycles()}")

if __name__ == "__main__":
    run_safe_execution()
