import subprocess
import time
import sys
import os
from datetime import datetime
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def run_command(command, log_file):
    """Run a command and log its output"""
    with open(log_file, 'a') as f:
        f.write(f"\n{'='*50}\n")
        f.write(f"Starting {command} at {datetime.now()}\n")
        f.write(f"{'='*50}\n")
        
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            shell=True
        )
        
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(f"[{command}] {output.strip()}")
                f.write(output)
                f.flush()

def create_logs_directory():
    """Create logs directory if it doesn't exist"""
    if not os.path.exists('logs'):
        os.makedirs('logs')

class UrlJsonHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_modified = time.time()
        
    def on_modified(self, event):
        if event.src_path.endswith('url.json'):
            # Prevent duplicate events
            if time.time() - self.last_modified > 1:
                print("\nurl.json changed, restarting services...")
                self.last_modified = time.time()
                # Kill existing processes and restart
                main()

def watch_url_json():
    event_handler = UrlJsonHandler()
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()
    return observer

def main():
    create_logs_directory()
    
    # Define commands and their log files
    commands = [
        ("python 20scrap.py", "logs/scraper.log"),
        ("python 30sum.py", "logs/summarizer.log"),
        ("python 10server.py", "logs/server.log")
    ]
    
    try:
        print("Starting services sequentially...")
        # Start file watcher
        observer = watch_url_json()
        
        # Run commands one after another
        for cmd, log_file in commands:
            print(f"\nStarting {cmd}...")
            run_command(cmd, log_file)
            print(f"Finished {cmd}")
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        observer.stop()
        observer.join()
        sys.exit(0)

if __name__ == "__main__":
    main() 