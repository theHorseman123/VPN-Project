from typing import Tuple
import customtkinter as ctk
from tkinter import Text, Scrollbar, END, ttk
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from client_controller import *
import time
import _thread

class MyTabView(ctk.CTkTabview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # create tabs
        self.add("Connection")
        self.scorllable_frame = ctk.CTkScrollableFrame(master=self.tab("Connection"))
        self.scorllable_frame.pack(expand=True, fill="both")
        self.proxies = []

    def add_proxy_tab(self, proxy_addr: str):
        # create tabs
        self.add(proxy_addr)

    def close_proxy_tab(self, proxy_addr: str):
        self.delete(proxy_addr)

    def connect(self, proxy_address, button):
        pass

    def create_proxy_frame(self, addr, status):
        frame = ctk.CTkFrame(self.scorllable_frame, bg_color="#404B56")
        frame.pack(fill="x", pady=5, padx=5)

        addr_label =  ctk.CTkLabel(frame,text=addr, bg_color="transparent")
        addr_label.pack(side="left", padx=5)
        status_icon = "vpn client/unlocked.png" if status == "0" else "vpn client/locked.png"
        icon_image = Image.open(status_icon)
        icon_image = icon_image.resize((20, 20), Image.LANCZOS)
        icon_photo = ImageTk.PhotoImage(icon_image)
        label_icon = ctk.CTkLabel(frame, text="", image=icon_photo, bg_color="transparent")
        label_icon.image = icon_photo
        label_icon.pack(side="left", padx=5)

        button_connect = ctk.CTkButton(frame, text="Connect", command=lambda proxy_address=addr: self.master.request_proxy(addr), bg_color="transparent")
        button_connect.pack(side="right", padx=5)
        self.proxies.append(frame)

    def update_table(self, proxies):
        for proxy in self.proxies:
            proxy.destroy()
        
        for proxy in proxies:
            self.create_proxy_frame(proxy[0], proxy[1])

class Console(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.pack_propagate(False)
        self.console_output = Text(self, wrap="word", foreground="white")
        self.console_output.config(bg="#2b2b2b")
        self.console_output.pack(expand=True, fill="both", padx=5, pady=5)
        self.grid(row=6, column=0, rowspan=4, columnspan=10, padx=15, pady=10, sticky="nsew")

    def write(self, text):
        self.console_output.config(state="normal")  # Allow text insertion
        self.console_output.insert(END, text + "\n")
        self.console_output.see(END)  # Scroll to the end
        self.console_output.config(state="disabled")  # Disable text editing

class App(ctk.CTk):
    def __init__(self, **kargs):
        super().__init__()

        self.connected = False
        self.proxies = []

        self.title("VPN client")
        self.geometry("600x600")
        self.minsize(600, 600)

        self.columnconfigure((0, 1, 2, 3, 4, 5, 6, 7, 8, 9), weight=1, uniform="a")
        self.rowconfigure((0, 1, 2, 3, 4, 5, 6, 7, 8, 9), weight=1, uniform="a")

        self.console = Console(self)

        self.tab_view = MyTabView(master=self)
        self.tab_view.grid(row=0, column=0, rowspan=6, columnspan=10, padx=15, pady=10, sticky="nsew")

        self.client = Client(**kargs)
        _thread.start_new_thread(self.start_client, ())

        self.mainloop()

    def request_proxy(self, proxy_address):
        print(proxy_address)

    def start_client(self):
        for i in range(5):
            if i == 4:
                self.console.write(" INFO: VPN server unreachable")
                return

            self.console.write(" *Attempting connection with VPN server")
            status = self.client.connect_server()
            if status == "pass":
                self.console.write(f" INFO: VPN server connection at: {self.client.server_address[0]}:{str(self.client.server_address[1])}")
                break
            else:
                self.console.write(status)
                time.sleep(5)
        while 1:
            proxies = self.client.get_proxies()
            if proxies == "Server left":
                self.console.write(" *Server has disconnected")
                break
            if proxies != self.proxies:
                print(proxies)
                self.tab_view.update_table(proxies)
                self.proxies = proxies
            time.sleep(1)

App(server_address=(sock.gethostbyname(sock.gethostname()), 1234))