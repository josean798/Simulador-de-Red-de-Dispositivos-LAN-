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
        self.interfaces = []  # Lista de objetos Interface
        self.status = 'up'    # 'up' (online) o 'down' (offline)
        self.packet_queue = []  # Cola de paquetes entrantes/salientes
        self.history_stack = []  # Pila de historial de recepción

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
        Devuelve la lista de interfaces del dispositivo.
        """
        return self.interfaces

    def receive_packet(self, packet):
        """
        Recibe un paquete y lo almacena en la pila de historial.
        """
        self.history_stack.append(packet)

    def enqueue_packet(self, packet):
        """
        Encola un paquete para ser procesado/salido.
        """
        self.packet_queue.append(packet)

    def dequeue_packet(self):
        """
        Extrae el siguiente paquete de la cola.
        """
        if self.packet_queue:
            return self.packet_queue.pop(0)
        return None

    def get_history(self):
        """
        Devuelve el historial de paquetes recibidos (último primero).
        """
        return list(reversed(self.history_stack))

    def get_queue(self):
        """
        Devuelve la cola de paquetes pendientes.
        """
        return self.packet_queue

    def __str__(self):
        """
        Representación en texto del dispositivo.
        """
        return f"{self.name} ({self.device_type}) - Estado: {self.status}"

