"""
Modulo 4: Registro de Errores (cola enlazada)
Implementa un sistema de registro de errores en tiempo real usando una cola enlazada.
Cada nodo almacena timestamp, tipo de error, mensaje y comando.
"""
import json
from typing import Optional, List, Dict
from datetime import datetime

class ErrorNode:
    def __init__(self, timestamp: str, error_type: str, message: str, command: Optional[str]):
        self.timestamp = timestamp
        self.error_type = error_type
        self.message = message
        self.command = command
        self.next: Optional['ErrorNode'] = None

class ErrorLog:
    def __init__(self):
        self.head: Optional[ErrorNode] = None
        self.tail: Optional[ErrorNode] = None
        self.size: int = 0

    def log_error(self, error_type: str, message: str, command: Optional[str] = None):
        """Agrega un error al final de la cola."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        node = ErrorNode(timestamp, error_type, message, command)
        if not self.head:
            self.head = self.tail = node
        else:
            self.tail.next = node
            self.tail = node
        self.size += 1

    def show_log(self, n: Optional[int] = None) -> List[Dict]:
        """Devuelve los últimos n errores (o todos si n es None)."""
        result = []
        current = self.head
        count = 0
        while current and (n is None or count < n):
            result.append({
                'timestamp': current.timestamp,
                'type': current.error_type,
                'message': current.message,
                'command': current.command
            })
            current = current.next
            count += 1
        return result

    def save_to_json(self, filename):
        """Guarda el log de errores en un archivo JSON."""
        errors = self.show_log()
        with open(filename, 'w') as f:
            json.dump(errors, f, indent=2)

    def load_from_json(self, filename):
        """Carga el log de errores desde un archivo JSON."""
        try:
            with open(filename, 'r') as f:
                errors = json.load(f)
            for e in errors:
                self.log_error(e['type'], e['message'], e.get('command'))
        except FileNotFoundError:
            pass

