from Queue import Queue
from LinkedList import LinkedList

class Interface:
    """
    Representa una interfaz de red de un dispositivo (ej: g0/0, eth0)..
    """

    def __init__(self, name):
        """
        Inicializa la interfaz con nombre, sin IP y estado 'up'.
        """
        self.name = name
        self.ip_address = None
        self.status = 'up'  # 'up' (activa) o 'down' (inactiva)
        self.neighbors = LinkedList()  # Interfaces conectadas (lista enlazada)
        self.packet_queue = Queue()  # Cola de paquetes para la interfaz

    def set_ip(self, ip):
        """Asigna una dirección IP a la interfaz"""
        if self._validate_ip(ip):
            self.ip_address = ip
            return True
        return False

    def _validate_ip(self, ip):
        """Valida formato básico de dirección IP"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        return all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)

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
        if not self.neighbors.find(other_interface):
            self.neighbors.append(other_interface)
            other_interface.neighbors.append(self)

    def disconnect(self, other_interface):
        """
        Desconecta esta interfaz de otra interfaz.
        """
        if self.neighbors.find(other_interface):
            self.neighbors.remove(other_interface)
            other_interface.neighbors.remove(self)

    def enqueue_packet(self, packet):
        """
        Encola un paquete en la interfaz.
        """
        self.packet_queue.enqueue(packet)

    def dequeue_packet(self):
        """
        Extrae el siguiente paquete de la cola de la interfaz.
        """
        return self.packet_queue.dequeue()

    def get_queue(self):
        """
        Devuelve la cola de paquetes pendientes en la interfaz como lista de Python.
        """
        return self.packet_queue.get_all()

    def __str__(self):
        """
        Representación en texto de la interfaz.
        """
        ip = self.ip_address if self.ip_address else "Sin IP"
        estado = "Activa" if self.status == 'up' else "Inactiva"
        vecinos = "Sin conexiones"
        if hasattr(self.neighbors, 'to_list'):
            vecinos_list = self.neighbors.to_list()
            vecinos = ', '.join([n.name for n in vecinos_list]) if vecinos_list else "Sin conexiones"
        return f"{self.name} | IP: {ip} | Estado: {estado} | Vecinos: {vecinos}"
