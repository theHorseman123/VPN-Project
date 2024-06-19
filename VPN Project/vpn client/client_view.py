from typing import Tuple
import customtkinter as ctk
from tkinter import Text, Scrollbar, END, ttk
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from client_controller import *
import threading
import socket as sock
import time

class MyTabView(ctk.CTkTabview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(command=lambda: self.update_graph())

        # create tabs
        self.add("Connection")
        self.scorllable_frame = ctk.CTkScrollableFrame(master=self.tab("Connection"))
        self.scorllable_frame.pack(expand=True, fill="both")

        self.canvas = None

        self.proxies = []
        self.proxy_button = None

        self.connected_proxies = [] # addresses of all connect proxies
        
        self.disconnect_event = None

    def update_graph(self):
        try:
            if self.get() not in self.connected_proxies:
                return

            proxy_addr = self.get()
            proxy_speed = self.master.client.proxies_speed[proxy_addr]

            if self.canvas:
                self.canvas.get_tk_widget().destroy()

            fig, ax = plt.subplots(figsize=(6, 4))
            ax.set_facecolor("#404B56")
            fig.patch.set_facecolor("#404B56")
            x = [i for i in range(max(len(proxy_speed)-30, 0), len(proxy_speed))]
            y = proxy_speed[-30:]
            ax.plot(x, y, marker='o', color='cyan')
            ax.set_xlabel("Time(s)", color='white')
            ax.set_ylabel("Proxy speed (mb/seconds)", color='white')
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            self.canvas = FigureCanvasTkAgg(fig, master=self.tab(proxy_addr))
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill="both", expand=True)
        except Exception as error:
            self.delete_proxy_tab(self.get())

    def add_proxy_tab(self, proxy_addr: str):
        try:
            self.add(proxy_addr)
        except:
            pass

    def delete_proxy_tab(self, proxy_addr):
        try:
            self.delete(proxy_addr)
        except:
            pass

    def connect(self, proxy_address, button, status):
        button.configure(state="disabled")
        if not self.disconnect_event:
            self.disconnect_event = threading.Event()
        
        event = threading.Event()
        time.sleep(0.1)
        secret_code=None
        if status == "1":
            dialog = ctk.CTkInputDialog(text="Enter secret password:", title="")
            secret_code = dialog.get_input()
            if not secret_code:
                button.configure(state="normal")
                return
        self.connected_proxies.append(proxy_address)
        self.master.console.write(f" *Attempting connection with: {proxy_address}")
        self.add_proxy_tab(proxy_address)
        button.configure(text="Disconnect", command=lambda: self.disconnect(proxy_address, button, status, event), fg_color="dark red", hover_color="red", state="normal")
        proxy_active = True
        try:
            while (not event.is_set()) and proxy_active:
                proxy_active = self.master.client.app_proxy_connect(proxy_addr=proxy_address, console=self.master.console, event=event, disconnect=self.disconnect_event, secret_code=secret_code)
        except Exception as error:
            print(f" ERROR: {error}")
        finally:
            if len(self.connected_proxies) == 1:
                return
            if not event.is_set():
                self.disconnect(proxy_address, button, status, event)
            else:
                self.delete_proxy_tab(proxy_address)

    def disconnect(self, proxy_address, button, status, event):
        event.set()
        self.master.console.write(f" *Closing connection with proxy: {proxy_address}")
        button.configure(text="Connect", command=lambda: start_new_thread(self.connect, (proxy_address, button, status)), fg_color="dark blue", hover_color="blue")
        self.delete_proxy_tab(proxy_address)
        self.connected_proxies.remove(proxy_address)
        if len(self.connected_proxies) == 0:
            self.disconnect_event.set()
            time.sleep(1)
            self.disconnect_event = None
            self.master.connected = False

    def create_proxy_frame(self, addr, status):
        if addr in self.connected_proxies:
            return
        frame = ctk.CTkFrame(self.scorllable_frame, bg_color="#2b2b2b")
        frame.pack(fill="x", pady=5, padx=5)

        addr_label =  ctk.CTkLabel(frame,text=addr, bg_color="#2b2b2b")
        addr_label.pack(side="left", padx=5)
        status_icon = "vpn client/unlocked.png" if status == "0" else "vpn client/locked.png"
        icon_image = Image.open(status_icon)
        icon_image = icon_image.resize((20, 20), Image.LANCZOS)
        icon_photo = ImageTk.PhotoImage(icon_image)
        label_icon = ctk.CTkLabel(frame, text="", image=icon_photo, bg_color="#2b2b2b")
        label_icon.image = icon_photo
        label_icon.pack(side="left", padx=5)

        button_connect = ctk.CTkButton(frame, text="Connect", bg_color="#2b2b2b", fg_color="dark blue", hover_color="blue")
        button_connect.configure(command=lambda: start_new_thread(self.connect, (addr, button_connect, status)))
        button_connect.pack(side="right", padx=5)
        self.proxies.append(frame)

    def update_table(self, proxies):
        for proxy in self.proxies:
            state = proxy.winfo_children()[-1].cget("text")
            if state == "Connect":
                proxy.destroy()
                self.proxies.remove(proxy)

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

        self.proxies = []

        self.title("VPN client")
        self.geometry("600x600")
        self.minsize(600, 600)

        self.columnconfigure((0, 1, 2, 3, 4, 5, 6, 7, 8, 9), weight=1, uniform="a")
        self.rowconfigure((0, 1, 2, 3, 4, 5, 6, 7, 8, 9), weight=1, uniform="a")

        self.console = Console(self)

        self.tab_view = MyTabView(master=self, segmented_button_selected_hover_color="blue")
        self.tab_view.grid(row=0, column=0, rowspan=6, columnspan=10, padx=15, pady=10, sticky="nsew")

        self.client = Client(**kargs)
        start_new_thread(self.start_client, ())

        self.mainloop()

    def start_client(self):
            while 1:
                self.console.write(" *Attempting connection with VPN server")
                status = self.client.connect_server()
                if status == "pass":
                    self.console.write(f" INFO: VPN server connection at: {self.client.server_address[0]}:{str(self.client.server_address[1])}")
                else:
                    self.console.write(status)
                    time.sleep(5)
                while 1:
                    proxies = self.client.get_proxies()
                    if proxies == "Server left":
                        self.console.write(" *Server has disconnected")
                        break
                    current_proxies = [i.winfo_children()[0].cget("text") for i in self.tab_view.proxies]
                    if sorted(current_proxies) != sorted([i[0] for i in proxies]):
                        self.tab_view.update_table(proxies)
                        self.proxies = proxies
                    time.sleep(1)
try:
    App(server_address=(sock.gethostbyname(sock.gethostname()), 1234))
except:
    disable_proxy()
disable_proxy()