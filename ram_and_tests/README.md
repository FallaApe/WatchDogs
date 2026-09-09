

# RAM and Tests

This folder handles the memory storage simulation, performance metrics, and test cases for the project. It represents the Main Memory (RAM) in the virtual machine architecture and acts as the "attacker" to test the security of the system.

## Files

- **memory.py**: Simulates the RAM. Handles read and write operations to a memory array. Also tracks the number of clock cycles used during memory access so we can measure the performance overhead of the hardware security later.
- **attacker.py**: Test script that simulates a buffer overflow attack. It intentionally tries to write past allocated memory boundaries to test if the Memory Controller catches and blocks it.
- **safe_program.py**: Test script that simulates normal program execution. It reads and writes strictly within allocated boundaries to verify the system does not block legitimate traffic.

***

### How to add this and push it:

Run these commands in your terminal from the main project folder:

```bash
cd ram_and_tests
touch README.md
```
*(Open the README.md file in your text editor, paste the text above, and save it.)*

```bash
cd ..
git add .
git commit -m "Added README for ram_and_tests folder"
git push origin main
```
