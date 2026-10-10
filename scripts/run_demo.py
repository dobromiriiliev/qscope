#!/usr/bin/env python3
"""Graphical launcher for qscope."""
from qscope.cli import main
import tkinter as tk
from tkinter import messagebox
from qscope.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["demo", *__import__("sys").argv[1:]]))
def run_command(command):
    status.set(f"Running: {command} ...")
    root.update_idletasks()

    try:
        result = main([command])
        if result is None:
            result = 0

        status.set(f"{command} finished (exit code {result})")
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
        status.set(f"{command} finished (exit code {code})")
    except Exception as exc:
        status.set(f"{command} failed")
        messagebox.showerror(
            "Command failed",
            f"The command '{command}' failed:\n{exc}",
        )


def inject_drift():
    confirmed = messagebox.askyesno(
        "Inject Drift",
    )
    if confirmed:
        run_command("demo")

def diagnose():
    run_command("diagnose")

root = tk.Tk()
root.title("QScope")
root.geometry("380x220")
root.resizable(False, False)

heading = tk.Label(
    root,
    text="QScope Control Panel",
    font=("Arial", 16, "bold"),
)
heading.pack(pady=(22, 16))

buttons = tk.Frame(root)
buttons.pack()

inject_button = tk.Button(
    buttons,
    text="Inject Drift",
    command=inject_drift,
    width=14,
    height=2,
)
inject_button.pack(side=tk.LEFT, padx=8)

diagnose_button = tk.Button(
    buttons,
    text="Diagnose",
    command=diagnose,
    width=14,
    height=2,
)
diagnose_button.pack(side=tk.LEFT, padx=8)

status = tk.StringVar(value="Ready")
status_label = tk.Label(
    root,
    textvariable=status,
    wraplength=340,
)
status_label.pack(pady=18)

root.mainloop()
