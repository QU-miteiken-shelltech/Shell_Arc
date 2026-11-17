import time

starting_time = 0

def start_timer(clear: bool=False):
    global starting_time
    if not clear and starting_time == 0:
        return
    starting_time = time.time()

def capture_timer(text: str=""):
    global starting_time
    time_elasped = time.time() - starting_time
    print(f"{text} - {time_elasped}s")
