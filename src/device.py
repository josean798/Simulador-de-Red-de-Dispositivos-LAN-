from Mode import Mode
from LinkedList import LinkedList
from Queue import Queue
from Stack import Stack
# Importar las nuevas estructuras de datos
from avl_route_table import AVLRouteTable
from prefix_trie import PrefixTrie

class Device:
    """
    Representa un dispositivo de red (router, switch, host, firewall).
    """

    def __init__(self, name, device_type):
        """
        Inicializa el dispositivo con nombre, tipo y estado.
        """
        self.name = name
        self.device_type = device_type
        self.interfaces = LinkedList()  # Lista enlazada de objetos Interface
        self.status = 'up'    # 'up' (online) o 'down' (offline)
        self.packet_queue = Queue()  # Cola de paquetes entrantes/salientes
        self.history_stack = Stack()  # Pila de historial de recepción
        self.mode = Mode.USER  
        
        # Nuevas estructuras para Módulos 1 y 3 del Proyecto 2
        self.route_table = AVLRouteTable() # Tabla de rutas AVL para este dispositivo
        self.prefix_trie = PrefixTrie()    # Trie de políticas para este dispositivo

    def add_interface(self, interface):
        """
        Agrega una interfaz al dispositivo.
        """
        self.interfaces.append(interface)

    def set_status(self, status):
        """
        Cambia el estado del dispositivo ('up' o 'down').
        """
        if status in ['up', 'down']:
            self.status = status
        else:
            raise ValueError("Estado inválido. Usa 'up' o 'down'.")

    def get_interfaces(self):
        """
        Devuelve la lista de interfaces del dispositivo como lista de Python.
        """
        return self.interfaces.to_list()

    def receive_packet(self, packet):
        """
        Recibe un paquete y lo almacena en la pila de historial.
        """
        self.history_stack.push(packet)

    def enqueue_packet(self, packet):
        """
        Encola un paquete para ser procesado/salido.
        """
        self.packet_queue.enqueue(packet)

    def dequeue_packet(self):
        """
        Extrae el siguiente paquete de la cola.
        """
        return self.packet_queue.dequeue()

    def get_history(self):
        """
        Devuelve el historial de paquetes recibidos (último primero).
        """
        # Retorna una copia invertida para que el más reciente sea el primero
        return self.history_stack.get_all()[::-1] 

    def get_queue(self):
        """
        Devuelve la cola de paquetes pendientes como lista de Python.
        """
        return self.packet_queue.get_all()

    def __str__(self):
        """
        Representación en texto del dispositivo.
        """
        return f"{self.name} ({self.device_type}) - Estado: {self.status}"

