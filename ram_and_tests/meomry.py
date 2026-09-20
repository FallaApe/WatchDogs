class RAM:
    def __init__(self, size=1024):
        self.size = size
        # We use a dictionary to represent memory addresses to save space
        self.memory = {}
        self.cycles_used = 0  # Tracks CPU cycles for performance metrics

    def read(self, address):
        """Simulates reading from RAM."""
        self.cycles_used += 1  # Reading takes 1 clock cycle
        # Return the data at address, or 0 if nothing is there yet
        return self.memory.get(address, 0)

    def write(self, address, value):
        """Simulates writing to RAM."""
        self.cycles_used += 1  # Writing takes 1 clock cycle
        self.memory[address] = value

    def get_cycles(self):
        """Returns total cycles used."""
        return self.cycles_used

    def dump_memory(self, start_address, end_address):
        """Prints out a chunk of memory so we can see if an attack corrupted it."""
        print("\n--- Memory Dump ---")
        for i in range(start_address, end_address):
            print(f"Address {i}: {self.memory.get(i, 0)}")
        print("-------------------\n")
