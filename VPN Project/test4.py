import tkinter as tk
from tkinter import ttk

class VPNClientApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VPN client")
        self.configure(bg="#2F3A45")
        self.geometry("400x300")

        self.create_widgets()

    def create_widgets(self):
        # Title label
        title_label = tk.Label(self, text="VPN client", bg="#2F3A45", fg="white", font=("Helvetica", 14))
        title_label.pack(pady=10)

        # Frames
        left_frame = tk.Frame(self, bg="#404B56", width=200, height=200)
        left_frame.pack(side="left", fill="y", padx=10, pady=10)
        left_frame.pack_propagate(False)

        right_frame = tk.Frame(self, bg="#4C5762", width=200, height=200)
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        right_frame.pack_propagate(False)

        # Scrollable list in the left frame
        self.ip_listbox = tk.Listbox(left_frame, bg="#333D45", fg="white", font=("Helvetica", 12))
        self.ip_listbox.pack(side="left", fill="y", expand=True)

        # Adding a scrollbar
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.ip_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.ip_listbox.config(yscrollcommand=scrollbar.set)

        # Adding IP addresses to the listbox
        ip_addresses = ["192.168.10.1:1234"] * 7
        for ip in ip_addresses:
            self.ip_listbox.insert(tk.END, ip)

if __name__ == "__main__":
    app = VPNClientApp()
    app.mainloop()