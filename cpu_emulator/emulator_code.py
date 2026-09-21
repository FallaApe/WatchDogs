import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import hashlib
import os


# ============================================================
# CPU
# ============================================================

class CPU:

    def __init__(self):
        self.reset()

    def reset(self):

        self.registers = [0] * 8

        # 64 KB virtual memory
        self.memory = bytearray(65536)

        self.PC = 0
        self.SP = 65535

        self.zero_flag = 0
        self.carry_flag = 0

        self.halted = False

        self.program = []

        self.instruction_count = 0

        # Virtual file information
        self.file_name = ""
        self.file_size = 0
        self.file_hash = ""


# ============================================================
# WATCHDOG
# ============================================================

class Watchdog:

    def __init__(self, log_callback):

        self.log = log_callback

        self.allowed_instructions = {
            "NOP",
            "MOV",
            "ADD",
            "SUB",
            "MUL",
            "DIV",
            "LOAD",
            "STORE",
            "CMP",
            "JMP",
            "JZ",
            "JNZ",
            "PUSH",
            "POP",
            "PRINT",
            "HALT"
        }


    # --------------------------------------------------------
    # Check CPU instruction
    # --------------------------------------------------------

    def check_instruction(self, instruction):

        instruction = instruction.strip().upper()

        if not instruction:
            return True

        opcode = instruction.split()[0]

        if opcode not in self.allowed_instructions:

            self.log(
                f"[WATCHDOG] BLOCKED UNKNOWN "
                f"INSTRUCTION: {opcode}"
            )

            return False

        return True


    # --------------------------------------------------------
    # Check imported file
    # --------------------------------------------------------

    def check_file(self, filename, data):

        self.log(
            f"[WATCHDOG] Scanning file: {filename}"
        )

        # Maximum file size for this prototype

        MAX_FILE_SIZE = 1024 * 1024 * 5

        if len(data) > MAX_FILE_SIZE:

            self.log(
                "[WATCHDOG] BLOCKED: File exceeds 5 MB."
            )

            return False


        # Calculate SHA-256

        file_hash = hashlib.sha256(data).hexdigest()

        self.log(
            f"[WATCHDOG] SHA-256: {file_hash}"
        )


        # Basic demonstration checks

        dangerous_extensions = [
            ".exe",
            ".dll",
            ".bat",
            ".cmd",
            ".scr"
        ]

        extension = os.path.splitext(
            filename
        )[1].lower()


        if extension in dangerous_extensions:

            self.log(
                f"[WATCHDOG] WARNING: "
                f"Executable file type detected: {extension}"
            )

            # For the college prototype we can
            # allow it after warning.

            self.log(
                "[WATCHDOG] File allowed for sandbox analysis."
            )


        self.log(
            "[WATCHDOG] File scan completed."
        )

        return True


    # --------------------------------------------------------
    # Check export
    # --------------------------------------------------------

    def check_export(self, filename, data):

        self.log(
            f"[WATCHDOG] Checking outgoing file: {filename}"
        )

        if len(data) > 5 * 1024 * 1024:

            self.log(
                "[WATCHDOG] BLOCKED: Export too large."
            )

            return False

        self.log(
            "[WATCHDOG] Export approved."
        )

        return True


# ============================================================
# GUI
# ============================================================

class CPUEmulatorGUI:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "WATCHDOG - CPU Emulator"
        )

        self.root.geometry(
            "1250x750"
        )

        self.cpu = CPU()

        self.watchdog = Watchdog(
            self.log_message
        )

        self.create_gui()

        self.update_everything()


    # ========================================================
    # CREATE GUI
    # ========================================================

    def create_gui(self):

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        title = tk.Label(
            self.root,
            text="WATCHDOG CPU EMULATOR",
            font=("Arial", 22, "bold")
        )

        title.pack(pady=10)


        # ----------------------------------------------------
        # MAIN FRAME
        # ----------------------------------------------------

        main = tk.Frame(self.root)

        main.pack(
            fill="both",
            expand=True,
            padx=10
        )


        # ====================================================
        # LEFT PANEL
        # ====================================================

        left = tk.Frame(main)

        left.pack(
            side="left",
            fill="both",
            expand=True,
            padx=5
        )


        # ----------------------------------------------------
        # PROGRAM
        # ----------------------------------------------------

        tk.Label(
            left,
            text="Assembly Program",
            font=("Arial", 13, "bold")
        ).pack(
            anchor="w"
        )


        self.program_text = tk.Text(
            left,
            height=18,
            font=("Courier New", 11)
        )

        self.program_text.pack(
            fill="both",
            expand=True
        )


        example = """MOV R0, 10
MOV R1, 20
ADD R0, R1
STORE R0, [1000]
LOAD R2, [1000]
PRINT R2
HALT
"""

        self.program_text.insert(
            "1.0",
            example
        )


        # ----------------------------------------------------
        # CPU BUTTONS
        # ----------------------------------------------------

        buttons = tk.Frame(left)

        buttons.pack(
            pady=8
        )


        tk.Button(
            buttons,
            text="LOAD",
            width=10,
            command=self.load_program
        ).pack(
            side="left",
            padx=3
        )


        tk.Button(
            buttons,
            text="STEP",
            width=10,
            command=self.step
        ).pack(
            side="left",
            padx=3
        )


        tk.Button(
            buttons,
            text="RUN",
            width=10,
            command=self.run
        ).pack(
            side="left",
            padx=3
        )


        tk.Button(
            buttons,
            text="RESET",
            width=10,
            command=self.reset
        ).pack(
            side="left",
            padx=3
        )


        # ====================================================
        # FILE OPERATIONS
        # ====================================================

        file_frame = tk.LabelFrame(
            left,
            text="Virtual File System"
        )

        file_frame.pack(
            fill="x",
            pady=10
        )


        tk.Button(
            file_frame,
            text="IMPORT FILE",
            width=15,
            command=self.import_file
        ).pack(
            side="left",
            padx=10,
            pady=10
        )


        tk.Button(
            file_frame,
            text="EXPORT FILE",
            width=15,
            command=self.export_file
        ).pack(
            side="left",
            padx=10
        )


        self.file_label = tk.Label(
            file_frame,
            text="No file loaded"
        )

        self.file_label.pack(
            side="left",
            padx=10
        )


        # ====================================================
        # RIGHT PANEL
        # ====================================================

        right = tk.Frame(main)

        right.pack(
            side="right",
            fill="both",
            expand=True,
            padx=5
        )


        # ====================================================
        # REGISTERS
        # ====================================================

        tk.Label(
            right,
            text="CPU Registers",
            font=("Arial", 13, "bold")
        ).pack(
            anchor="w"
        )


        self.register_tree = ttk.Treeview(
            right,
            columns=("Register", "Value"),
            show="headings",
            height=8
        )

        self.register_tree.heading(
            "Register",
            text="Register"
        )

        self.register_tree.heading(
            "Value",
            text="Value"
        )

        self.register_tree.pack(
            fill="x"
        )


        # ====================================================
        # CPU STATUS
        # ====================================================

        status = tk.LabelFrame(
            right,
            text="CPU Status"
        )

        status.pack(
            fill="x",
            pady=10
        )


        self.pc_label = tk.Label(
            status,
            text="PC: 0"
        )

        self.pc_label.pack(
            anchor="w",
            padx=10
        )


        self.sp_label = tk.Label(
            status,
            text="SP: 65535"
        )

        self.sp_label.pack(
            anchor="w",
            padx=10
        )


        self.zero_label = tk.Label(
            status,
            text="Zero Flag: 0"
        )

        self.zero_label.pack(
            anchor="w",
            padx=10
        )


        self.carry_label = tk.Label(
            status,
            text="Carry Flag: 0"
        )

        self.carry_label.pack(
            anchor="w",
            padx=10
        )


        self.status_label = tk.Label(
            status,
            text="CPU READY",
            font=("Arial", 11, "bold")
        )

        self.status_label.pack(
            pady=5
        )


        # ====================================================
        # MEMORY
        # ====================================================

        tk.Label(
            right,
            text="Virtual Memory",
            font=("Arial", 13, "bold")
        ).pack(
            anchor="w"
        )


        self.memory_tree = ttk.Treeview(
            right,
            columns=("Address", "Value", "Hex"),
            show="headings",
            height=8
        )

        self.memory_tree.heading(
            "Address",
            text="Address"
        )

        self.memory_tree.heading(
            "Value",
            text="Decimal"
        )

        self.memory_tree.heading(
            "Hex",
            text="Hex"
        )

        self.memory_tree.pack(
            fill="x"
        )


        # ====================================================
        # LOG
        # ====================================================

        tk.Label(
            right,
            text="Watchdog / CPU Log",
            font=("Arial", 13, "bold")
        ).pack(
            anchor="w",
            pady=(10, 0)
        )


        self.log_text = tk.Text(
            right,
            height=10,
            font=("Courier New", 9)
        )

        self.log_text.pack(
            fill="both",
            expand=True
        )


    # ========================================================
    # LOG
    # ========================================================

    def log_message(self, message):

        self.log_text.insert(
            tk.END,
            message + "\n"
        )

        self.log_text.see(
            tk.END
        )


    # ========================================================
    # RESET
    # ========================================================

    def reset(self):

        self.cpu.reset()

        self.update_everything()

        self.log_message(
            "[CPU] CPU reset."
        )


    # ========================================================
    # LOAD PROGRAM
    # ========================================================

    def load_program(self):

        text = self.program_text.get(
            "1.0",
            tk.END
        )

        lines = text.splitlines()

        self.cpu.program = []

        for line in lines:

            line = line.strip()

            if not line:
                continue

            if line.startswith(";"):
                continue

            self.cpu.program.append(
                line.upper()
            )


        self.cpu.PC = 0

        self.cpu.halted = False

        self.cpu.instruction_count = 0

        self.log_message(
            f"[CPU] Loaded "
            f"{len(self.cpu.program)} instructions."
        )


        self.update_everything()


    # ========================================================
    # IMPORT FILE
    # ========================================================

    def import_file(self):

        filename = filedialog.askopenfilename(
            title="Select file to import"
        )


        if not filename:
            return


        try:

            with open(
                filename,
                "rb"
            ) as file:

                data = file.read()


            basename = os.path.basename(
                filename
            )


            # Watchdog scans file

            allowed = self.watchdog.check_file(
                basename,
                data
            )


            if not allowed:

                messagebox.showerror(
                    "Watchdog",
                    "File blocked by Watchdog."
                )

                return


            # Make sure it fits into memory

            if len(data) > len(
                self.cpu.memory
            ):

                messagebox.showerror(
                    "Memory Error",
                    "File is larger than virtual memory."
                )

                return


            # Load file into virtual memory

            self.cpu.memory[
                0:len(data)
            ] = data


            # Store file information

            self.cpu.file_name = basename

            self.cpu.file_size = len(data)

            self.cpu.file_hash = hashlib.sha256(
                data
            ).hexdigest()


            self.file_label.config(
                text=f"{basename} "
                     f"({len(data)} bytes)"
            )


            self.log_message(
                f"[FILE] Imported: {basename}"
            )


            self.log_message(
                f"[FILE] Size: {len(data)} bytes"
            )


            self.log_message(
                f"[FILE] SHA-256: "
                f"{self.cpu.file_hash}"
            )


            self.log_message(
                "[WATCHDOG] File accepted into sandbox."
            )


            self.update_memory()


        except Exception as e:

            messagebox.showerror(
                "Import Error",
                str(e)
            )


    # ========================================================
    # EXPORT FILE
    # ========================================================

    def export_file(self):

        if self.cpu.file_size == 0:

            messagebox.showwarning(
                "Export",
                "There is no imported file."
            )

            return


        data = bytes(
            self.cpu.memory[
                0:self.cpu.file_size
            ]
        )


        filename = filedialog.asksaveasfilename(
            title="Export file",
            initialfile=
            "watchdog_output.bin"
        )


        if not filename:
            return


        # Watchdog check

        allowed = self.watchdog.check_export(
            os.path.basename(filename),
            data
        )


        if not allowed:

            messagebox.showerror(
                "Watchdog",
                "Export blocked."
            )

            return


        try:

            with open(
                filename,
                "wb"
            ) as file:

                file.write(data)


            self.log_message(
                f"[FILE] Exported: {filename}"
            )


            messagebox.showinfo(
                "Export Successful",
                "File exported successfully."
            )


        except Exception as e:

            messagebox.showerror(
                "Export Error",
                str(e)
            )


    # ========================================================
    # GET REGISTER
    # ========================================================

    def get_register(self, value):

        value = value.upper()

        if not value.startswith("R"):

            raise ValueError(
                "Invalid register"
            )


        number = int(
            value[1:]
        )


        if number < 0 or number >= 8:

            raise ValueError(
                "Invalid register"
            )


        return number


    # ========================================================
    # EXECUTE INSTRUCTION
    # ========================================================

    def execute_instruction(self):

        if self.cpu.halted:
            return


        if self.cpu.PC >= len(
            self.cpu.program
        ):

            self.cpu.halted = True

            self.log_message(
                "[CPU] Program finished."
            )

            return


        instruction = self.cpu.program[
            self.cpu.PC
        ]


        # Watchdog

        if not self.watchdog.check_instruction(
            instruction
        ):

            self.cpu.halted = True

            self.status_label.config(
                text="WATCHDOG BLOCKED"
            )

            return


        self.log_message(
            f"[CPU] PC={self.cpu.PC}: "
            f"{instruction}"
        )


        parts = instruction.replace(
            ",",
            " "
        ).split()


        opcode = parts[0]


        # ----------------------------------------------------
        # NOP
        # ----------------------------------------------------

        if opcode == "NOP":

            self.cpu.PC += 1


        # ----------------------------------------------------
        # MOV
        # ----------------------------------------------------

        elif opcode == "MOV":

            reg = self.get_register(
                parts[1]
            )

            value = int(
                parts[2]
            )

            if not 0 <= value <= 255:

                raise ValueError(
                    "Value must be 0-255"
                )


            self.cpu.registers[
                reg
            ] = value


            self.cpu.zero_flag = int(
                value == 0
            )


            self.cpu.PC += 1


        # ----------------------------------------------------
        # ADD
        # ----------------------------------------------------

        elif opcode == "ADD":

            r1 = self.get_register(
                parts[1]
            )

            r2 = self.get_register(
                parts[2]
            )


            result = (
                self.cpu.registers[r1]
                +
                self.cpu.registers[r2]
            )


            self.cpu.carry_flag = int(
                result > 255
            )


            self.cpu.registers[r1] = (
                result % 256
            )


            self.cpu.zero_flag = int(
                self.cpu.registers[r1] == 0
            )


            self.cpu.PC += 1


        # ----------------------------------------------------
        # SUB
        # ----------------------------------------------------

        elif opcode == "SUB":

            r1 = self.get_register(
                parts[1]
            )

            r2 = self.get_register(
                parts[2]
            )


            self.cpu.registers[r1] = (
                self.cpu.registers[r1]
                -
                self.cpu.registers[r2]
            ) % 256


            self.cpu.zero_flag = int(
                self.cpu.registers[r1] == 0
            )


            self.cpu.PC += 1


        # ----------------------------------------------------
        # LOAD
        # ----------------------------------------------------

        elif opcode == "LOAD":

            reg = self.get_register(
                parts[1]
            )


            address = int(
                parts[2]
                .replace("[", "")
                .replace("]", "")
            )


            if not 0 <= address < 65536:

                raise ValueError(
                    "Invalid memory address"
                )


            self.cpu.registers[reg] = (
                self.cpu.memory[address]
            )


            self.cpu.zero_flag = int(
                self.cpu.registers[reg] == 0
            )


            self.cpu.PC += 1


        # ----------------------------------------------------
        # STORE
        # ----------------------------------------------------

        elif opcode == "STORE":

            reg = self.get_register(
                parts[1]
            )


            address = int(
                parts[2]
                .replace("[", "")
                .replace("]", "")
            )


            if not 0 <= address < 65536:

                raise ValueError(
                    "Invalid memory address"
                )


            self.cpu.memory[address] = (
                self.cpu.registers[reg]
            )


            self.cpu.PC += 1


        # ----------------------------------------------------
        # PRINT
        # ----------------------------------------------------

        elif opcode == "PRINT":

            reg = self.get_register(
                parts[1]
            )


            self.log_message(
                f"[PROGRAM OUTPUT] "
                f"R{reg} = "
                f"{self.cpu.registers[reg]}"
            )


            self.cpu.PC += 1


        # ----------------------------------------------------
        # HALT
        # ----------------------------------------------------

        elif opcode == "HALT":

            self.cpu.halted = True

            self.log_message(
                "[CPU] HALT."
            )


        else:

            self.log_message(
                f"[WATCHDOG] BLOCKED: {opcode}"
            )

            self.cpu.halted = True


        # Infinite loop protection

        self.cpu.instruction_count += 1


        if self.cpu.instruction_count > 1000:

            self.log_message(
                "[WATCHDOG] Possible infinite loop."
            )

            self.cpu.halted = True


        self.update_everything()


    # ========================================================
    # STEP
    # ========================================================

    def step(self):

        try:

            self.execute_instruction()

        except Exception as e:

            self.log_message(
                f"[CPU ERROR] {e}"
            )

            self.cpu.halted = True


    # ========================================================
    # RUN
    # ========================================================

    def run(self):

        if not self.cpu.program:

            self.load_program()


        self.cpu.halted = False

        self.cpu.instruction_count = 0


        try:

            while not self.cpu.halted:

                self.execute_instruction()

                self.root.update()


        except Exception as e:

            self.log_message(
                f"[CPU ERROR] {e}"
            )

            self.cpu.halted = True


    # ========================================================
    # UPDATE REGISTERS
    # ========================================================

    def update_registers(self):

        for item in self.register_tree.get_children():

            self.register_tree.delete(item)


        for i in range(8):

            self.register_tree.insert(
                "",
                "end",
                values=(
                    f"R{i}",
                    self.cpu.registers[i]
                )
            )


    # ========================================================
    # UPDATE MEMORY
    # ========================================================

    def update_memory(self):

        for item in self.memory_tree.get_children():

            self.memory_tree.delete(item)


        # Display first 16 bytes

        for i in range(16):

            value = self.cpu.memory[i]

            self.memory_tree.insert(
                "",
                "end",
                values=(
                    i,
                    value,
                    f"0x{value:02X}"
                )
            )


        # Display last 16 bytes / stack

        for i in range(65520, 65536):

            value = self.cpu.memory[i]

            self.memory_tree.insert(
                "",
                "end",
                values=(
                    i,
                    value,
                    f"0x{value:02X}"
                )
            )


    # ========================================================
    # UPDATE EVERYTHING
    # ========================================================

    def update_everything(self):

        if hasattr(
            self,
            "register_tree"
        ):

            self.update_registers()


        if hasattr(
            self,
            "memory_tree"
        ):

            self.update_memory()


        if hasattr(
            self,
            "pc_label"
        ):

            self.pc_label.config(
                text=f"PC: {self.cpu.PC}"
            )

            self.sp_label.config(
                text=f"SP: {self.cpu.SP}"
            )

            self.zero_label.config(
                text=f"Zero Flag: "
                     f"{self.cpu.zero_flag}"
            )

            self.carry_label.config(
                text=f"Carry Flag: "
                     f"{self.cpu.carry_flag}"
            )


            if self.cpu.halted:

                self.status_label.config(
                    text="CPU HALTED"
                )

            else:

                self.status_label.config(
                    text="CPU READY"
                )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = CPUEmulatorGUI(root)

    root.mainloop()
