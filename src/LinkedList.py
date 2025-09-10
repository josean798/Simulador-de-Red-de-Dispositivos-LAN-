from Node import Node

class LinkedList:
    """
    Implementa una lista enlazada simple.
    """
    def __init__(self):
        self.head = None
        self.size = 0

    def __iter__(self):  # <-- Añade este método
        current = self.head
        while current:
            yield current.data
            current = current.next

    def append(self, data):
        """
        Agrega un elemento al final de la lista.
        """
        new_node = Node(data)
        if not self.head:
            self.head = new_node
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = new_node
        self.size += 1

    def prepend(self, data):
        """
        Agrega un elemento al inicio de la lista.
        """
        new_node = Node(data)
        new_node.next = self.head
        self.head = new_node
        self.size += 1

    def remove(self, data):
        """
        Elimina el primer nodo que contiene el dato especificado.
        """
        current = self.head
        prev = None
        while current:
            if current.data == data:
                if prev:
                    prev.next = current.next
                else:
                    self.head = current.next
                self.size -= 1
                return True
            prev = current
            current = current.next
        return False

    def find(self, data):
        """
        Busca un nodo por su dato y lo retorna.
        """
        current = self.head
        while current:
            if current.data == data:
                return current
            current = current.next
        return None

    def to_list(self):
        """
        Devuelve una lista con todos los datos de la lista enlazada.
        """
        result = []
        current = self.head
        while current:
            result.append(current.data)
            current = current.next
        return result

    def __len__(self):
        return self.size

    def __str__(self):
        return ' -> '.join(str(x) for x in self.to_list())
