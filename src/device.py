from Mode import Mode
from LinkedList import LinkedList
from Queue import Queue
from Stack import Stack

class Device:
    """
    Representa un dispositivo de red (router, switch, host, firewall)..
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
        self.sent_stack = Stack()      # Pila de historial de enviados
        self.received_stack = Stack()  # Pila de historial de recibidos
        self.mode = Mode.USER  

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
        Recibe un paquete y lo almacena en el historial de recibidos.
        """
        self.received_stack.push(packet)

    def add_sent(self, packet):
        """
        Agrega un paquete al historial de enviados.
        """
        self.sent_stack.push(packet)

    def add_received(self, packet):
        """
        Agrega un paquete al historial de recibidos.
        """
        self.received_stack.push(packet)

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


    def get_sent(self):
        """
        Devuelve el historial de paquetes enviados (último primero).
        """
        return self.sent_stack.get_all()

    def get_received(self):
        """
        Devuelve el historial de paquetes recibidos (último primero).
        """
        return self.received_stack.get_all()

    def get_history(self):
        """
        Devuelve ambos historiales (enviados, recibidos) como tupla.
        """
        return (self.get_sent(), self.get_received())

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

