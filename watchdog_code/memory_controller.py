"""
WatchDogs - Memory Controller & Security Logic ("The Watchdog")
===============================================================
Member 2 of 3 | Computer Organization & Architecture

Hardware security module that sits between the CPU (Member 1) and RAM
(Member 3). Every memory request must pass through this controller.

COA concepts implemented:
    * Base and Limit registers      - per-region (base, limit) pairs
    * Memory bounds checking        - base <= addr AND addr + size <= base + limit
    * Hardware exceptions (traps)   - MemoryViolationError raised to the CPU
    * Execute (NX) permission bit   - AccessType.EXECUTE
    * Address-space bounds          - 16-bit space (0x0000 .. 0xFFFF)
    * Security overhead accounting  - cycles charged per check, so Member 3
                                      can benchmark with/without protection
"""

from dataclasses import dataclass
from enum import Flag
from typing import List, Optional


# --------------------------------------------------------------------------- #
#  Access types & permissions
# --------------------------------------------------------------------------- #

class AccessType(Flag):
    READ = 1
    WRITE = 2
    EXECUTE = 4


def perm_str(p: AccessType) -> str:
    """Human-readable permission string, e.g. 'RW-' or 'R-X'."""
    return (("R" if p & AccessType.READ else "-") +
            ("W" if p & AccessType.WRITE else "-") +
            ("X" if p & AccessType.EXECUTE else "-"))


# --------------------------------------------------------------------------- #
#  Hardware exception
# --------------------------------------------------------------------------- #

class MemoryViolationError(Exception):
    """
    Raised by the watchdog when a memory access is illegal.
    This simulates a hardware trap (think: protection fault / segfault
    delivered to the CPU instead of the access reaching RAM).
    """

    def __init__(self, address, size, access, reason, region=None):
        self.address = address
        self.size = size
        self.access_type = access
        self.reason = reason
        self.region = region
        super().__init__(f"[{access.name}] @ {address:#06x} (size {size}): {reason}")


# --------------------------------------------------------------------------- #
#  Memory region = one (base, limit) register pair
# --------------------------------------------------------------------------- #

@dataclass
class MemoryRegion:
    name: str
    base: int                # start address (inclusive)
    limit: int               # size in bytes
    permissions: AccessType
    owner: str = "kernel"

    @property
    def end(self) -> int:    # exclusive upper bound = base + limit
        return self.base + self.limit


# --------------------------------------------------------------------------- #
#  The Watchdog
# --------------------------------------------------------------------------- #

class MemoryController:
    """
    Interposes between the CPU and RAM:

        CPU -- request --> MemoryController -- safe requests --> RAM
              <-- ok / MemoryViolationError (trap) <-- read/write -->

    Usage:
        ram = SimpleRAM()                # (Member 3's module)
        mc  = MemoryController(ram)
        mc.map_region("stack", 0xF000, 0x1000, AccessType.READ | AccessType.WRITE)
        mc.write(0xF010, 42, size=4)     # safe  -> forwarded to RAM
        mc.write(0xF010, 0, size=9999)   # unsafe -> MemoryViolationError
    """

    ADDRESS_SPACE = 0x10000   # 16-bit address space = 64 KiB

    def __init__(self, ram=None, security_overhead_cycles: int = 2):
        self.ram = ram
        self.security_overhead_cycles = security_overhead_cycles
        self.regions: List[MemoryRegion] = []
        self.violations: List[MemoryViolationError] = []
        self.stats = {
            "checks": 0,
            "violations": 0,
            "regions_mapped": 0,
            "security_cycles": 0,
        }

    # ---------------- region management (base/limit registers) -------- #

    def attach(self, ram) -> None:
        """Plug in Member 3's RAM module."""
        self.ram = ram

    def map_region(self, name, base, limit, permissions, owner="kernel") -> MemoryRegion:
        """Install a (base, limit) register pair for a new memory region."""
        if limit <= 0:
            raise ValueError(f"region '{name}': limit must be positive")
        if base < 0 or base + limit > self.ADDRESS_SPACE:
            raise ValueError(f"region '{name}': does not fit in "
                             f"{self.ADDRESS_SPACE:#x}-byte address space")
        for r in self.regions:
            if base < r.end and r.base < base + limit:
                raise ValueError(f"region '{name}' overlaps region '{r.name}'")
        region = MemoryRegion(name, base, limit, permissions, owner)
        self.regions.append(region)
        self.stats["regions_mapped"] += 1
        return region

    def unmap_region(self, name: str) -> None:
        """Free a region. Subsequent accesses to it become faults."""
        self.regions = [r for r in self.regions if r.name != name]

    # ---------------- the actual security check ------------------------ #

    def _find_region(self, address: int) -> Optional[MemoryRegion]:
        for r in self.regions:
            if r.base <= address < r.end:
                return r
        return None

    def _validate(self, address, size, access) -> MemoryRegion:
        """
        Full hardware-style check. Returns the owning region on success,
        raises MemoryViolationError otherwise.

        The rule (base/limit bounds checking):
            base <= address  AND  address + size <= base + limit

        Note the second condition: even if `address` itself is valid, a
        multi-byte access can still run past the end of the region.
        That is the off-by-one that breaks naive bounds checkers.
        """
        self.stats["checks"] += 1
        self.stats["security_cycles"] += self.security_overhead_cycles

        if size <= 0:
            raise MemoryViolationError(address, size, access, "size must be >= 1")
        if not 0 <= address < self.ADDRESS_SPACE:
            raise MemoryViolationError(address, size, access,
                f"address outside the {self.ADDRESS_SPACE:#x}-byte address space")

        region = self._find_region(address)
        if region is None:
            raise MemoryViolationError(address, size, access,
                "unmapped memory (no region owns this address)")

        if not (region.permissions & access):
            raise MemoryViolationError(address, size, access,
                f"permission denied: region '{region.name}' is "
                f"{perm_str(region.permissions)}, {access.name} requested",
                region=region)

        if address + size > region.end:
            raise MemoryViolationError(address, size, access,
                f"out of bounds: {size}-byte access crosses the limit of "
                f"region '{region.name}' (base={region.base:#06x}, limit={region.limit})",
                region=region)

        return region

    def _trap(self, exc: MemoryViolationError) -> None:
        self.violations.append(exc)
        self.stats["violations"] += 1

    # ---------------- public API --------------------------------------- #

    def check_access(self, address, size=1, access=AccessType.READ) -> bool:
        """Boolean API: True = safe, False = attack. Never raises."""
        try:
            self._validate(address, size, access)
        except MemoryViolationError as e:
            self._trap(e)
            return False
        return True

    def read(self, address, size=1):
        """CPU read path: validate first, then forward to RAM. Traps on violation."""
        try:
            self._validate(address, size, AccessType.READ)
        except MemoryViolationError as e:
            self._trap(e)
            raise
        return self.ram.read(address, size)

    def write(self, address, value, size=1):
        """CPU write path: validate first, then forward to RAM. Traps on violation."""
        try:
            self._validate(address, size, AccessType.WRITE)
        except MemoryViolationError as e:
            self._trap(e)
            raise
        self.ram.write(address, value, size)

    # ---------------- reporting ---------------------------------------- #

    def dump_violation_report(self) -> None:
        print("\n" + "-" * 68)
        print(" VIOLATION REPORT (every attack the watchdog caught)")
        print("-" * 68)
        for i, v in enumerate(self.violations, 1):
            region = v.region.name if v.region else "UNMAPPED"
            print(f" {i}. {v.access_type.name:<7} addr={v.address:#06x} "
                  f"size={v.size:<4} region={region:<10} :: {v.reason}")

    def dump_stats(self) -> None:
        print("\n" + "-" * 68)
        print(" WATCHDOG STATS")
        print("-" * 68)
        print(f" checks performed      : {self.stats['checks']}")
        print(f" violations caught     : {self.stats['violations']}")
        print(f" regions mapped        : {self.stats['regions_mapped']}")
        print(f" security cycles spent : {self.stats['security_cycles']} "
              f"({self.security_overhead_cycles} per check)")
        print(" tip: rerun with security_overhead_cycles=0 for the")
        print("      unprotected baseline (Member 3's benchmark).")


# --------------------------------------------------------------------------- #
#  Placeholder RAM - Member 3 owns the real one.
#  Contract: any RAM class with read(address, size) and write(address, value, size).
# --------------------------------------------------------------------------- #

class SimpleRAM:
    """Byte-addressable RAM: just a big array of bytes, like real hardware."""

    def __init__(self, size: int = 0x10000):
        self.data = bytearray(size)

    def read(self, address: int, size: int = 1) -> bytes:
        return bytes(self.data[address:address + size])

    def write(self, address: int, value, size: int = 1) -> None:
        if isinstance(value, int):
            value = value.to_bytes(size, byteorder="little")
        self.data[address:address + size] = value[:size]


# --------------------------------------------------------------------------- #
#  Demo - run with:  python memory_controller.py
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    ram = SimpleRAM(MemoryController.ADDRESS_SPACE)
    mc = MemoryController(ram, security_overhead_cycles=2)

    print("=" * 68)
    print(" WatchDogs | Memory Controller (the Watchdog) | live demo")
    print("=" * 68)

    print("\n[setup] mapping regions (base + limit register pairs)")
    code  = mc.map_region("code",     0x0000, 0x0100, AccessType.READ | AccessType.EXECUTE)
    buf   = mc.map_region("heap_buf", 0x1000, 10,     AccessType.READ | AccessType.WRITE)
    stack = mc.map_region("stack",    0xF000, 0x1000, AccessType.READ | AccessType.WRITE)
    for r in (code, buf, stack):
        print(f"   + {r.name:<9} base={r.base:#06x}  limit={r.limit:<6} perms={perm_str(r.permissions)}")

    print("\n[safe program]")
    mc.write(0x1000, 42, size=4)
    print("   write  4 bytes @ 0x1000 (fits in 10-byte heap_buf)   ALLOWED")
    data = mc.read(0x1000, size=4)
    print(f"   read   4 bytes @ 0x1000                             ALLOWED -> {data.hex()}")
    ok = mc.check_access(0x0000, size=1, access=AccessType.EXECUTE)
    print(f"   fetch  1 byte   @ 0x0000 (code region, R-X)         {'ALLOWED' if ok else 'BLOCKED'}")

    print("\n[attack program]")

    ok = mc.check_access(0xF000, size=1, access=AccessType.EXECUTE)
    print(f"   execute @ 0xF000 (stack, RW-)                       {'ALLOWED' if ok else 'BLOCKED'}")

    def attack(label, fn):
        try:
            fn()
            print(f"   {label}  ALLOWED (!!)")
        except MemoryViolationError as e:
            print(f"   {label}  BLOCKED")
            print(f"        trap -> {e}")

    attack("overflow: 100-byte write into 10-byte heap_buf @ 0x1000",
           lambda: mc.write(0x1000, b"A" * 100, size=100))

    attack("off-by-one: 2-byte write @ 0x1009 (last valid byte)",
           lambda: mc.write(0x1009, 0xFFFF, size=2))

    attack("unmapped read @ 0x0500 (no region owns it)",
           lambda: mc.read(0x0500, size=4))

    attack("write into read-only code region @ 0x0000",
           lambda: mc.write(0x0000, 0x90, size=1))

    mc.dump_violation_report()
    mc.dump_stats()
