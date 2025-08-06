class Node:
    """Nodo para lista enlazada que almacena dispositivos conectados"""
    def __init__(self, data):
        self.data = data 
        self.next = None

class LinkedList:
    """Lista enlazada para manejar conexiones entre dispositivos"""
    def __init__(self):
        self.head = None

    def append(self, data):
        """Añade un nuevo dispositivo a la lista de conexiones"""
        new_node = Node(data)
        if not self.head:
            self.head = new_node
            return
        last = self.head
        while last.next:
            last = last.next
        last.next = new_node

    def remove(self, data):
        """Elimina un dispositivo de la lista de conexiones"""
        current = self.head
        prev = None
        
        while current:
            if current.data == data:
                if prev:
                    prev.next = current.next
                else:
                    self.head = current.next
                return True
            prev = current
            current = current.next
        return False

    def display(self):
        """Muestra todas las conexiones"""
        connections = []
        current = self.head
        while current:
            connections.append(str(current.data))
            current = current.next
        return " -> ".join(connections) if connections else "None"

    def __contains__(self, data):
        """Verifica si un dispositivo está en la lista"""
        current = self.head
        while current:
            if current.data == data:
                return True
            current = current.next
        return False