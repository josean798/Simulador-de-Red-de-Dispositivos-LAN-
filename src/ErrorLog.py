from Queue import Queue
from datetime import datetime

class ErrorEntry:
    def __init__(self, error_type, message, command=None):
        self.timestamp = datetime.now()
        self.error_type = error_type
        self.message = message
        self.command = command

    def __str__(self):
        time_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        cmd_str = f" (Comando: {self.command})" if self.command else ""
        return f"[{time_str}] {self.error_type}: {self.message}{cmd_str}"

class ErrorLog:
    def __init__(self, max_entries=100):
        self.queue = Queue(max_entries)

    def log_error(self, error_type, message, command=None):
        entry = ErrorEntry(error_type, message, command)
        self.queue.enqueue(entry)

    def get_errors(self, n=None):
        all_errors = self.queue.get_all()
        if n is None:
            return all_errors
        return all_errors[-n:]  # Últimos n

    def clear(self):
        self.queue.clear()

    def size(self):
        return self.queue.size()
