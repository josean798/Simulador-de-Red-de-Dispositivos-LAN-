class Queue:
    """Implementación de cola para manejo de paquetes"""
    def __init__(self, max_size=100):
        self.items = []

    def enqueue(self, item):
        """Encola un elemento, removiendo el más antiguo si se excede el tamaño máximo"""
        if len(self.items) >= self.max_size:
            self.dequeue()
        self.items.append(item)

    def dequeue(self):
        """Desencola un elemento"""
        if not self.is_empty():
            return self.items.pop(0)
        return None

    def is_empty(self):
        """Verifica si la cola está vacía"""
        return len(self.items) == 0

    def size(self):
        """Tamaño actual de la cola"""
        return len(self.items)

    def clear(self):
        """Vacía la cola"""
        self.items = []

    def peek(self):
        """Mira el primer elemento sin desencolar"""
        if not self.is_empty():
            return self.items[0]
        return None

    def get_all(self):
        """Obtiene todos los elementos en orden FIFO"""
        return self.items.copy()