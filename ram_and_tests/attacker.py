import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory import RAM

def run_attack():
    print("--- Running Malicious Buffer Overflow Attack ---")
    ram = RAM()
    
    # Program allocates 4 bytes of memory (Addresses 0, 1, 2, 3)
    allocated_size = 4
    print(f"Program allocated {allocated_size} bytes of memory.")
    
    # Attacker tries to write 20 bytes, overwriting adjacent memory!
    print("Attacker attempting to write 20 bytes...")
    
    for i in range(20):
        ram.write(i, 99) # Writing 99 to addresses 0 through 19
        
    print("\n[!] ATTACK SUCCESSFUL (Baseline CPU has no protection)")
    print("Memory state after attack:")
    
    # Dump the first 25 addresses to prove we corrupted memory outside our bounds
    ram.dump_memory(0, 25)
    print(f"Total CPU Cycles Used: {ram.get_cycles()}")

if __name__ == "__main__":
    run_attack()
