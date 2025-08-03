class Interface:
    """
    Representa una interfaz de red de un dispositivo (ej: g0/0, eth0).
    """

    def __init__(self, name):
        """
        Inicializa la interfaz con nombre, sin IP y estado 'up'.
        """
        self.name = name
        self.ip_address = None
        self.status = 'up'  # 'up' (activa) o 'down' (inactiva)
        self.neighbors = []  # Interfaces conectadas (lista enlazada)
        self.packet_queue = []  # Cola de paquetes para la interfaz

    def set_ip(self, ip):
        """
        Asigna una dirección IP a la interfaz.
        """
        self.ip_address = ip

    def shutdown(self):
        """
        Desactiva la interfaz.
        """
        self.status = 'down'

    def no_shutdown(self):
        """
        Activa la interfaz.
        """
        self.status = 'up'

    def connect(self, other_interface):
        """
        Conecta esta interfaz con otra interfaz (enlaza físicamente).
        """
        if other_interface not in self.neighbors:
            self.neighbors.append(other_interface)
            other_interface.neighbors.append(self)

    def disconnect(self, other_interface):
        """
        Desconecta esta interfaz de otra interfaz.
        """
        if other_interface in self.neighbors:
            self.neighbors.remove(other_interface)
            other_interface.neighbors.remove(self)

    def enqueue_packet(self, packet):
        """
        Encola un paquete en la interfaz.
        """
        self.packet_queue.append(packet)

    def dequeue_packet(self):
        """
        Extrae el siguiente paquete de la cola de la interfaz.
        """
        if self.packet_queue:
            return self.packet_queue.pop(0)
        return None

    def get_queue(self):
        """
        Devuelve la cola de paquetes pendientes en la interfaz.
        """
        return self.packet_queue

    def __str__(self):
        """
        Representación en texto de la interfaz.
        """
        ip = self.ip_address if self.ip_address else "Sin IP"
        estado = "Activa" if self.status == 'up' else "Inactiva"
        vecinos = ', '.join([n.name for n in self.neighbors]) if self.neighbors else "Sin conexiones"
        return f"{self.name} | IP: {ip} | Estado: {estado} | Vecinos: {vecinos}"
