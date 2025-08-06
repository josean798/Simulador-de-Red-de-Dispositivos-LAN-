class Stack:
    """Implementación de pila para historial de paquetes"""
    def __init__(self, max_size=100):
        self.items = []
        self.max_size = max_size  # Límite para evitar crecimiento indefinido

    def push(self, item):
        """Apila un elemento, removiendo el más antiguo si se excede el tamaño máximo"""
        if len(self.items) >= self.max_size:
            self.items.pop(0)
        self.items.append(item)

    def pop(self):
        """Desapila un elemento"""
        if not self.is_empty():
            return self.items.pop()
        return None

    def is_empty(self):
        """Verifica si la pila está vacía"""
        return len(self.items) == 0

    def peek(self):
        """Mira el elemento superior sin desapilar"""
        if not self.is_empty():
            return self.items[-1]
        return None

    def size(self):
        """Tamaño actual de la pila"""
        return len(self.items)

    def clear(self):
        """Vacía la pila"""
        self.items = []

    def get_all(self):
        """Obtiene todos los elementos en orden LIFO"""
        return self.items[::-1]