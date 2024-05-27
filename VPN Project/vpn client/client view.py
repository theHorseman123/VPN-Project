import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageTk
from client_controller import *

# Sample proxy list
proxies = [
    {"ip": "192.168.1.1", "status": "open"},
    {"ip": "192.168.1.2", "status": "closed"},
    {"ip": "192.168.1.3", "status": "open"},
]

class App:
    def __init__(self, root):

        self.root = root
        self.root.title("VPN Client")
        self.root.geometry("500x400")
        self.current_connection = None
        self.create_widgets()

    def create_widgets(self):
        self.label_status = ctk.CTkLabel(self.root, text="Status: Disconnected", text_color="red")
        self.label_status.pack(pady=10)

        self.proxy_list_frame = ctk.CTkFrame(self.root)
        self.proxy_list_frame.pack(pady=10, fill="both", expand=True)

        self.populate_proxy_list()

    def populate_proxy_list(self):
        self.proxy_frames = []
        for proxy in proxies:
            frame = ctk.CTkFrame(self.proxy_list_frame)
            frame.pack(fill="x", pady=5, padx=10)

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

            proxy["button_connect"] = button_connect
            self.proxy_frames.append(proxy)

    def connect_vpn(self, ip):
        if self.current_connection:
            messagebox.showinfo("VPN Client", f"Already connected to {self.current_connection}. Disconnect first.")
            return
        
        proxy = next((p for p in proxies if p["ip"] == ip), None)
        if proxy:
            proxy["label_status"].configure(text="Connecting...", text_color="blue")
            self.root.after(2000, self.update_connection_status, proxy)

    def update_connection_status(self, proxy):
        self.current_connection = proxy["ip"]
        proxy["label_status"].configure(text="Connected", text_color="green")
        self.label_status.configure(text=f"Status: Connected to {proxy['ip']}", text_color="green")

        # Disable other connect buttons
        for p in self.proxy_frames:
            if p["ip"] != proxy["ip"]:
                p["button_connect"].configure(state="disabled")

    def disconnect_vpn(self):
        if self.current_connection:
            proxy = next((p for p in proxies if p["ip"] == self.current_connection), None)
            if proxy:
                proxy["label_status"].configure(text="", text_color="black")
                self.label_status.configure(text="Status: Disconnected", text_color="red")

                # Enable all connect buttons
                for p in self.proxy_frames:
                    p["button_connect"].configure(state="normal")

                self.current_connection = None

if __name__ == "__main__":
    root = ctk.CTk()
    app = App(root)
    root.mainloop()