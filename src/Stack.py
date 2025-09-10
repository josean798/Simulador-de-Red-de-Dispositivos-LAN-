from Node import Node

class Stack:
    """Implementación de pila para historial de paquetes usando nodos enlazados"""
    def __init__(self, max_size=100):
        self.top = None
        self._size = 0
        self.max_size = max_size

    def push(self, item):
        """Apila un elemento, removiendo el más antiguo si se excede el tamaño máximo"""
        if self._size >= self.max_size:
            self._remove_bottom()
        new_node = Node(item)
        new_node.next = self.top
        self.top = new_node
        self._size += 1

    def pop(self):
        """Desapila un elemento"""
        if self.top:
            value = self.top.data
            self.top = self.top.next
            self._size -= 1
            return value
        return None

    def is_empty(self):
        """Verifica si la pila está vacía"""
        return self._size == 0

    def peek(self):
        """Mira el elemento superior sin desapilar"""
        if self.top:
            return self.top.data
        return None

    def size(self):
        """Tamaño actual de la pila"""
        return self._size

    def clear(self):
        """Vacía la pila"""
        self.top = None
        self._size = 0

    def get_all(self):
        """Obtiene todos los elementos en orden LIFO"""
        result = []
        current = self.top
        while current:
            result.append(current.data)
            current = current.next
        return result

    def _remove_bottom(self):
        """Remueve el nodo más antiguo (fondo de la pila) si se excede el tamaño máximo."""
        if self.top is None:
            return
        if self.top.next is None:
            self.top = None
            self._size -= 1
            return
        prev = None
        current = self.top
        while current.next:
            prev = current
            current = current.next
        if prev:
            prev.next = None
            self._size -= 1