import customtkinter as ctk
from tkinter import Text, END

class ConsoleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Custom Console")
        self.root.geometry("800x600")
        self.root.configure(bg="#2b2b2b")
        
        # Create a frame for the console display
        self.console_frame = ctk.CTkFrame(self.root, fg_color="#2b2b2b")
        self.console_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create a text widget for console output
        self.console_output = Text(self.console_frame, wrap="word", bg="#2b2b2b", fg="white")
        self.console_output.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create an entry widget for user input
        self.console_input = ctk.CTkEntry(self.root, fg_color="#2b2b2b", text_color="white")
        self.console_input.pack(fill="x", padx=10, pady=(0, 10))
        self.console_input.bind("<Return>", self.handle_input)
        
        # Set initial focus to the input widget
        self.console_input.focus_set()
        
    def handle_input(self, event):
        command = self.console_input.get()
        self.console_output.insert(END, f"> {command}\n")
        self.console_input.delete(0, END)
        
        # Process command (here just echoing back the input)
        response = self.process_command(command)
        self.console_output.insert(END, f"{response}\n")
        self.console_output.see(END)
        
    def process_command(self, command):
        # This is where you would handle the command
        # For now, we just echo the command back as the response
        return f"Echo: {command}"

if __name__ == "__main__":
    root = ctk.CTk()
    app = ConsoleApp(root)
    root.mainloop()