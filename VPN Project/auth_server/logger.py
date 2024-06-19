import time
import os

class Logger:
    def __init__(self) -> None:
        if not os.path.isfile("logs.txt"):
            with open("logs.txt", "w") as f:
                pass
            

    def write(self, log_msg):
        with open("logs.txt", "a") as f:
            current_time = time.localtime()
            formatted_time = time.strftime("[%m/%d/%Y:%H:%M:%S]", current_time)
            log_msg = formatted_time+log_msg
            f.write(log_msg)