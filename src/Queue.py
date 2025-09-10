from Node import Node

class Queue:
    """Implementación de cola para manejo de paquetes usando nodos enlazados"""
    def __init__(self, max_size=100):
        self.front = None
        self.rear = None
        self.max_size = max_size
        self._size = 0

    def enqueue(self, item):
        """Encola un elemento, removiendo el más antiguo si se excede el tamaño máximo"""
        new_node = Node(item)
        if self._size >= self.max_size:
            self.dequeue()
        if not self.front:
            self.front = self.rear = new_node
        else:
            self.rear.next = new_node
            self.rear = new_node
        self._size += 1

    def dequeue(self):
        """Desencola un elemento"""
        if self.front:
            value = self.front.data
            self.front = self.front.next
            self._size -= 1
            if not self.front:
                self.rear = None
            return value
        return None

    def is_empty(self):
        """Verifica si la cola está vacía"""
        return self._size == 0

    def size(self):
        """Tamaño actual de la cola"""
        return self._size

    def clear(self):
        """Vacía la cola"""
        self.front = None
        self.rear = None
        self._size = 0

    def peek(self):
        """Mira el primer elemento sin desencolar"""
        if self.front:
            return self.front.data
        return None

    def get_all(self):
        """Obtiene todos los elementos en orden FIFO"""
        result = []
        current = self.front
        while current:
            result.append(current.data)
            current = current.next
        return result