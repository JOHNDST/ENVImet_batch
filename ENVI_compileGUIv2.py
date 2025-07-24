import os
import threading
import subprocess
import tkinter as tk
import tkinter.scrolledtext as st
from tkinter import filedialog, messagebox
import re, sys


class ENVIApp(tk.Tk):
    def __init__(self):
        super().__init__()
                # locate the ICO at runtime
        if getattr(sys, 'frozen', False):
            basedir = sys._MEIPASS
        else:
            basedir = os.path.dirname(__file__)
        ico = os.path.join(basedir, 'ICO.ico')
        self.iconbitmap(ico)
        self.title("ENVI‑met Batch Runner")
        self.geometry("700x500")
        self.create_widgets()

    def create_widgets(self):
        row = 0

        # Workspace
        tk.Label(self, text="Workspace folder:").grid(row=row, column=0, sticky="e")
        self.ws_var = tk.StringVar()
        tk.Entry(self, textvariable=self.ws_var, width=50).grid(row=row, column=1)
        tk.Button(self, text="Browse…", command=self.browse_ws).grid(row=row, column=2)
        row += 1

        # Output base
        tk.Label(self, text="Output directory:").grid(row=row, column=0, sticky="e")
        self.out_var = tk.StringVar()
        tk.Entry(self, textvariable=self.out_var, width=50).grid(row=row, column=1)
        tk.Button(self, text="Browse…", command=self.browse_out).grid(row=row, column=2)
        row += 1

        # ENVI‑met core exe
        tk.Label(self, text="ENVI‑met core exe:").grid(row=row, column=0, sticky="e")
        self.core_var = tk.StringVar()
        tk.Entry(self, textvariable=self.core_var, width=50).grid(row=row, column=1)
        tk.Button(self, text="Browse…", command=self.browse_core).grid(row=row, column=2)
        row += 1

        # Duration
        tk.Label(self, text="Duration (hours):").grid(row=row, column=0, sticky="e")
        self.dur_var = tk.IntVar(value=2)
        tk.Entry(self, textvariable=self.dur_var, width=10).grid(row=row, column=1, sticky="w")
        row += 1

        # Simulate all vs single
        self.all_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self, text="Simulate all samples", variable=self.all_var,
                       command=self.toggle_sample_id).grid(row=row, column=1, sticky="w")
        row += 1

        # Sample ID
        tk.Label(self, text="Sample ID or range:").grid(row=row, column=0, sticky="e")
        self.id_var = tk.StringVar(value="0")
        self.id_entry = tk.Entry(self, textvariable=self.id_var, width=20, state="disabled")
        self.id_entry.grid(row=row, column=1, sticky="w")
        row += 1

        # Run button
        self.run_btn = tk.Button(self, text="Run Simulation", command=self.start_run)
        self.run_btn.grid(row=row, column=1, pady=10)
        row += 1

        # Log box
        tk.Label(self, text="Log:").grid(row=row, column=0, sticky="nw")
        self.log_box = st.ScrolledText(self, width=85, height=20, state="disabled", wrap="none")
        self.log_box.grid(row=row, column=0, columnspan=3, padx=5, pady=5)

    def browse_ws(self):
        path = filedialog.askdirectory()
        if path: self.ws_var.set(path)

    def browse_out(self):
        path = filedialog.askdirectory()
        if path: self.out_var.set(path)

    def browse_core(self):
        path = filedialog.askopenfilename(filetypes=[("Executable","*.exe"),("All files","*.*")])
        if path: self.core_var.set(path)

    def toggle_sample_id(self):
        state = "disabled" if self.all_var.get() else "normal"
        self.id_entry.configure(state=state)

    def append_log(self, text):
        """Thread‑safe append to the ScrolledText."""
        def _append():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", text)
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.log_box.after(0, _append)

    def start_run(self):
        # Validate inputs
        ws       = self.ws_var.get().strip()
        out_base = self.out_var.get().strip()
        core_exe = self.core_var.get().strip()
        duration = self.dur_var.get()

        try:
            if not os.path.isdir(ws):
                raise ValueError("Workspace folder not valid.")
            os.makedirs(out_base, exist_ok=True)
            if not os.path.isfile(core_exe):
                raise ValueError("Core executable not found.")
        except Exception as e:
            messagebox.showerror("Input Error", str(e))
            return

        # Discover sample IDs from files named sample_*.INX
        pattern = re.compile(r"sample_(\d+)\.INX$", re.IGNORECASE)
        ids = []
        for fn in os.listdir(ws):
            m = pattern.match(fn)
            if m:
                ids.append(int(m.group(1)))
        if not ids:
            messagebox.showerror("Input Error", "No sample_*.INX files found in workspace.")
            return
        ids.sort()

        if self.all_var.get():
            sample_ids = ids
        else:
            txt = self.id_var.get().strip()
            # range?
            if "-" in txt:
                try:
                    lo, hi = map(int, txt.split("-", 1))
                except ValueError:
                    messagebox.showerror("Input Error", "Invalid range format. Use e.g. 4-10.")
                    return
                sample_ids = [i for i in ids if lo <= i <= hi]
                if not sample_ids:
                    messagebox.showerror("Input Error", f"No samples found in range {lo}-{hi}.")
                    return
            else:
                try:
                    sid = int(txt)
                except ValueError:
                    messagebox.showerror("Input Error", "Sample ID must be an integer or range.")
                    return
                if sid not in ids:
                    messagebox.showerror("Input Error", f"Sample ID {sid} not found.")
                    return
                sample_ids = [sid]

        # Disable UI and start thread
        self.run_btn.config(state="disabled")
        self.append_log("\n=== Starting batch simulation ===\n")
        threading.Thread(
            target=self.run_simulation,
            args=(ws, out_base, core_exe, duration, sample_ids),
            daemon=True
        ).start()

    def run_simulation(self, ws, out_base, core_exe, duration, ids):
        os.chdir(ws)
        simx_files = [fn for fn in os.listdir(ws) if fn.lower().endswith('.simx')]
        if not simx_files:
            raise FileNotFoundError("No .SIMX file found in workspace.")
        simx = simx_files[0]   # or pick by other logic if you have multiple

        def normalize(p): return p.replace("\\", "/")
        def modify_general(path, pattern, value):
            with open(path, 'r', encoding='cp1252') as f:
                content = f.read()
            new = re.sub(f"<{pattern}>(.*?)</{pattern}>", f"<{pattern}>{value}</{pattern}>",
                         content, flags=re.DOTALL)
            with open(path, 'w', encoding='cp1252') as f:
                f.write(new)
            return new

        try:
            for sid in ids:
                self.append_log(f"\n--- Sample {sid} ---\n")
                out_dir = os.path.join(out_base, f"sample_{sid}")
                os.makedirs(out_dir, exist_ok=True)

                safe_simx = normalize(simx)
                safe_out  = normalize(out_dir)

                # tweak INX and outDir via regex
                modify_general(safe_simx, "INXFile",    f" sample_{sid}.INX ")
                modify_general(safe_simx, "outDir",      f" {safe_out} ")
                modify_general(safe_simx, "simDuration", f" {duration} ")

                # Launch ENVI‑met core and pipe in "0\n0\n"
                cmd = [core_exe]
                self.append_log(f"CMD: {' '.join(cmd)} {safe_simx}\n\n")

                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=ws
                )
                proc.stdin.write(b"0\n0\n")
                proc.stdin.flush()
                proc.stdin.close()

                # Read & log output
                while True:
                    out = proc.stdout.readline()
                    if not out and proc.poll() is not None:
                        break
                    if out:
                        try:
                            self.append_log(out.decode("utf-8"))
                        except UnicodeDecodeError:
                            pass

                stderr = proc.stderr.read()
                if stderr:
                    try:
                        self.append_log(stderr.decode("utf-8"))
                    except UnicodeDecodeError:
                        pass

                ret = proc.wait()
                if ret != 0:
                    raise RuntimeError(f"Sample {sid} failed (exit {ret})")

            self.append_log("\n=== All simulations completed successfully ===\n")
        except Exception as e:
            self.append_log(f"\nERROR: {e}\n")
            messagebox.showerror("Simulation Error", str(e))
        finally:
            self.run_btn.config(state="normal")


if __name__ == "__main__":
    ENVIApp().mainloop()
