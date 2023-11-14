import tkinter as tk
from tkinter import ttk, messagebox
import json

class ConfigGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SFTP Configurations")

        self.configurations = []

        self.load_configurations()

        self.tree = ttk.Treeview(root)
        self.tree["columns"] = ("local_folder", "sftp_folder", "sftp_host", "sftp_port", "sftp_username", "sftp_password", "filename_patterns", "direction")
        self.tree.column("#0", width=0, stretch=tk.NO)
        self.tree.column("local_folder", anchor=tk.W, width=200)
        self.tree.column("sftp_folder", anchor=tk.W, width=200)
        self.tree.column("sftp_host", anchor=tk.W, width=150)
        self.tree.column("sftp_port", anchor=tk.W, width=50)
        self.tree.column("sftp_username", anchor=tk.W, width=100)
        self.tree.column("sftp_password", anchor=tk.W, width=100)
        self.tree.column("filename_patterns", anchor=tk.W, width=150)
        self.tree.column("direction", anchor=tk.W, width=100)

        self.tree.heading("#0", text="", anchor=tk.W)
        self.tree.heading("local_folder", text="Local Folder", anchor=tk.W)
        self.tree.heading("sftp_folder", text="SFTP Folder", anchor=tk.W)
        self.tree.heading("sftp_host", text="SFTP Host", anchor=tk.W)
        self.tree.heading("sftp_port", text="SFTP Port", anchor=tk.W)
        self.tree.heading("sftp_username", text="SFTP Username", anchor=tk.W)
        self.tree.heading("sftp_password", text="SFTP Password", anchor=tk.W)
        self.tree.heading("filename_patterns", text="Filename Patterns", anchor=tk.W)
        self.tree.heading("direction", text="Direction", anchor=tk.W)

        self.tree.pack(pady=10)

        self.add_button = ttk.Button(root, text="Add Configuration", command=self.add_configuration)
        self.add_button.pack(pady=10)

        self.show_configurations()

    def load_configurations(self):
        try:
            with open("configurations.json", "r") as json_file:
                self.configurations = json.load(json_file)
        except FileNotFoundError:
            pass

    def save_configurations(self):
        with open("configurations.json", "w") as json_file:
            json.dump(self.configurations, json_file, indent=4)

    def show_configurations(self):
        for config in self.configurations:
            self.tree.insert("", "end", values=(
                config["local_folder"],
                config["sftp_folder"],
                config["sftp_host"],
                config["sftp_port"],
                config["sftp_username"],
                config["sftp_password"],
                ",".join(config["filename_patterns"]) if "filename_patterns" in config else "",
                config["direction"]
            ))

    def add_configuration(self):
        config_window = tk.Toplevel(self.root)
        config_window.title("Add Configuration")

        labels = ["Local Folder", "SFTP Folder", "SFTP Host", "SFTP Port", "SFTP Username", "SFTP Password", "Filename Patterns", "Direction"]

        entries = {}
        for i, label in enumerate(labels):
            tk.Label(config_window, text=label).grid(row=i, column=0, sticky=tk.W, pady=5)
            entries[label] = tk.Entry(config_window)
            entries[label].grid(row=i, column=1, padx=5, pady=5)

        tk.Button(config_window, text="Save Configuration", command=lambda: self.save_new_configuration(config_window, entries)).grid(row=len(labels), columnspan=2, pady=10)

    def save_new_configuration(self, config_window, entries):
        new_config = {
            "local_folder": entries["Local Folder"].get(),
            "sftp_folder": entries["SFTP Folder"].get(),
            "sftp_host": entries["SFTP Host"].get(),
            "sftp_port": int(entries["SFTP Port"].get()),
            "sftp_username": entries["SFTP Username"].get(),
            "sftp_password": entries["SFTP Password"].get(),
            "filename_patterns": entries["Filename Patterns"].get().split(",") if entries["Filename Patterns"].get() else [],
            "direction": entries["Direction"].get()
        }

        self.configurations.append(new_config)
        self.save_configurations()
        self.tree.delete(*self.tree.get_children())
        self.show_configurations()
        config_window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ConfigGUI(root)
    root.mainloop()