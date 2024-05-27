import customtkinter as ctk
from tkinter import messagebox, Canvas, Scrollbar
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random

# Sample proxy list
proxies = [
    {"ip": "192.168.1.1", "status": "open"},
    {"ip": "192.168.1.2", "status": "closed"},
    {"ip": "192.168.1.3", "status": "open"},
    {"ip": "192.168.1.4", "status": "closed"},
    {"ip": "192.168.1.5", "status": "open"},
    {"ip": "192.168.1.6", "status": "closed"},
    {"ip": "192.168.1.7", "status": "open"},
]

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("VPN Client")
        self.root.geometry("800x600")
        
        # Configure grid layout
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=4)
        self.root.grid_columnconfigure(0, weight=1)
        
        self.create_widgets()

    def create_widgets(self):
        self.label_status = ctk.CTkLabel(self.root, text="Status: Disconnected", text_color="red")
        self.label_status.grid(row=0, column=0, pady=10, sticky="n")

        self.proxy_list_frame = ctk.CTkFrame(self.root)
        self.proxy_list_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.canvas_frame = ctk.CTkFrame(self.root)
        self.canvas_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        self.populate_proxy_list()

        self.canvas = None

    def populate_proxy_list(self):
        canvas = Canvas(self.proxy_list_frame)
        scrollbar = Scrollbar(self.proxy_list_frame, command=canvas.yview)
        scrollable_frame = ctk.CTkFrame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for proxy in proxies:
            frame = ctk.CTkFrame(scrollable_frame)
            frame.pack(fill="x", pady=5, padx=5)

            label_ip = ctk.CTkLabel(frame, text=f"IP: {proxy['ip']}")
            label_ip.pack(side="left", padx=5)

            status_icon = "vpn client/unlocked.png" if proxy["status"] == "open" else "vpn client/locked.png"
            icon_image = Image.open(status_icon)
            icon_image = icon_image.resize((20, 20), Image.ANTIALIAS)
            icon_photo = ImageTk.PhotoImage(icon_image)
            label_icon = ctk.CTkLabel(frame, text="", image=icon_photo)
            label_icon.image = icon_photo
            label_icon.pack(side="left", padx=5)

            button_connect = ctk.CTkButton(frame, text="Connect", command=lambda ip=proxy['ip']: self.connect_vpn(ip))
            button_connect.pack(side="right", padx=5)

            proxy["label_status"] = ctk.CTkLabel(frame, text="")
            proxy["label_status"].pack(side="right", padx=5)

    def connect_vpn(self, ip):
        proxy = next((p for p in proxies if p["ip"] == ip), None)
        if proxy:
            proxy["label_status"].configure(text="Connecting...", text_color="blue")
            self.root.after(2000, self.update_connection_status, proxy)

    def update_connection_status(self, proxy):
        # Simulate successful connection
        proxy["label_status"].configure(text="Connected", text_color="green")
        self.label_status.configure(text=f"Status: Connected to {proxy['ip']}", text_color="green")
        self.show_rtt_graph()

    def show_rtt_graph(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.set_facecolor("#2b2b2b")
        fig.patch.set_facecolor("#2b2b2b")
        x = list(range(1, 11))
        y = [random.randint(10, 100) for _ in range(10)]
        ax.plot(x, y, marker='o', color='cyan')
        ax.set_xlabel("Message Number", color='white')
        ax.set_ylabel("RTT (ms)", color='white')
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')

        self.canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

if __name__ == "__main__":
    root = ctk.CTk()
    app = App(root)
    root.mainloop()