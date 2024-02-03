import os
import subprocess
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from sys import platform
import glob

SIRIL = r'C:\Program Files\SiriL\bin\siril-cli.exe -s -'
EXT = "fit"
commands = {}
def_commands = {
    "Resample 50%": "requires 1.2.1\nsetext " + EXT + "\nload $FILE.$EXT\nresample 0.5\nsave $FILE_downscale.$EXT\nclose",
    "Resample 200%": "requires 1.2.1\nsetext " + EXT + "\nload $FILE.$EXT\nresample 2\nsave $FILE_upscale.$EXT\nclose"
}
config_dir = os.path.dirname(__file__)


def is_windows():
    return platform.startswith("win")


def is_osx():
    return platform.startswith("darwin")


def is_linux():
    return platform.startswith("linux")


def get_encoding():
    return "cp437" if is_windows() else "utf8"

def update_textbox(event):
    global sbatch
    selected = sbatch.combobox.get()
    command = commands.get(selected)
    sbatch.textbox.delete("1.0", tk.END)
    sbatch.textbox.insert("1.0", command)

class SirilBatch:

    def __init__(self, root):
        root.title("Siril Batch Executor")
        self.root = root
        self.recursive = False
        left_frame = tk.Frame(root, width=200, height=600)
        left_frame.grid(row=0, column=0, padx=10, pady=5)

        right_frame = tk.Frame(root, width=650, height=600)
        right_frame.grid(row=0, column=1, padx=10, pady=5)

        bottom_frame = tk.Frame(root, width=650, height=200)
        bottom_frame.grid(row=1, column=0, padx=10, pady=5)

        self.populate_commands()

        self.label = tk.Label(left_frame, text="Select Template")
        self.label.grid(row=0, column=0, padx=5, pady=5)
        self.combobox = ttk.Combobox(left_frame, values=list(commands.keys()))
        self.combobox.grid(row=0, column=1, padx=5, pady=5)
        self.combobox.bind("<<ComboboxSelected>>", update_textbox)

        self.textbox = tk.Text(left_frame, height=10, width=40)
        self.textbox.grid(row=1, column=0, padx=5, pady=5)

        self.launch_button = tk.Button(left_frame, text="Clear", command=self.clear_command)
        self.launch_button.grid(row=2, column=0, padx=5, pady=5)

        self.run_button = tk.Button(left_frame, text="Save", command=self.save_command)
        self.run_button.grid(row=2, column=1, padx=5, pady=5)

        self.save_text = tk.Text(left_frame, width=20, height=1)
        self.save_text.grid(row=2, column=2, padx=5, pady=5)

        self.select_files_button = tk.Button(right_frame, text="Select Files", command=self.select_files)
        self.select_files_button.grid(row=0, column=0, padx=5, pady=5)

        self.recursive_value = tk.BooleanVar()
        self.cb_recursive = tk.Checkbutton(right_frame, text='recursive', variable=self.recursive_value,  command=self.checkbox_clicked)
        self.cb_recursive.grid(row=0, column=1, padx=5, pady=5)

        self.select_files_button = tk.Button(right_frame, text="Output dir", command=self.output_dir)
        self.select_files_button.grid(row=0, column=2, padx=5, pady=5)
        self.out_dir = tk.Text(right_frame, width=20, height=1)
        self.out_dir.grid(row=0, column=3, padx=5, pady=5)
        self.out_dir.insert(0.0,"samedir")

        self.scrollbary = tk.Scrollbar(right_frame)
        self.scrollbary.grid(row=1, column=1, padx=5, pady=5)

        self.listbox = tk.Listbox(right_frame, width=75, yscrollcommand=self.scrollbary.set)
        self.listbox.grid(row=1, column=1, padx=5, pady=5)
        self.scrollbary.config(command=self.listbox.yview)

        self.launch_button = tk.Button(right_frame, text="Clear", command=self.clear_files)
        self.launch_button.grid(row=2, column=0, padx=5, pady=5)

        self.run_button = tk.Button(right_frame, text="Run", command=self.run_all)
        self.run_button.grid(row=2, column=1, padx=5, pady=5)

        self.progressbar = ttk.Progressbar(right_frame,length=300)
        self.progressbar.grid(row=3, column=1)

        self.output = tk.Text(bottom_frame, height=10, width=80)
        self.output.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

    def checkbox_clicked(self):
        print(self.recursive_value.get())

    def select_files(self):
        file_paths = filedialog.askopenfilenames()

        if self.recursive_value.get():
            # root_dir needs a trailing slash (i.e. /root/dir/)
            root_dir = os.path.dirname(file_paths[0]) + '/'
            for file_path in glob.iglob(root_dir + '**/*.' + EXT, recursive=True):
                self.listbox.insert(tk.END, file_path)
        else:
            for file_path in file_paths:
                self.listbox.insert(tk.END, file_path)

    def run_all(self):
        self.output.delete("1.0", tk.END)
        cmd = self.textbox.get("1.0", tk.END)
        self.progressbar.configure(maximum=self.listbox.size())
        for i, item in enumerate(self.listbox.get(0, tk.END)):
            self.launch_external_program(item, cmd)
            self.progressbar.step(1)
            self.root.update_idletasks()

    def launch_external_program(self, file_path, cmd):
        filename, ext = os.path.splitext(file_path)
        fmt_file = os.path.normpath(filename).replace('\\\\', '\\')
        cmd = cmd.replace("$FILE", fmt_file)
        cmd = cmd.replace("$EXT", ext[1:])
        print(cmd)
        process = subprocess.Popen(SIRIL, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(cmd.encode())

        self.output.insert(tk.END, stdout.decode(get_encoding()))


    def clear_command(self):
        self.textbox.delete(0.0, tk.END)

    def save_command(self):
        fname = self.save_text.get("1.0", tk.END).strip()
        path = os.path.abspath(os.path.join(config_dir, fname + ".sbcmd"))
        file = open(path, "w")
        file.write(self.textbox.get("1.0", tk.END))
        file.close()
        self.populate_commands()

    def output_dir(self):
        dir = filedialog.askdirectory();
        self.out_dir.delete(0.0, tk.END)
        self.out_dir.insert(0.0,dir)

    def populate_commands(self):
        global commands
        commands = def_commands

        for file in os.listdir(config_dir):
            if file.endswith(".sbcmd"):
                path = os.path.join(config_dir, file)
                with open(path) as f:
                    content = f.read()
                    basename = os.path.splitext(os.path.basename(path))[0]
                    commands[basename] = content

    def clear_files(self):
        self.listbox.delete(0, tk.END)


root = tk.Tk()
sbatch = SirilBatch(root)
root.mainloop()
