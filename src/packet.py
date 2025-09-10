import uuid
from LinkedList import LinkedList

class Packet:
    """
    Representa un paquete de red virtual para el simulador LAN..
    """
    def __init__(self, source_ip, destination_ip, content, ttl=5):
        """
        Inicializa el paquete con origen, destino, contenido, TTL y ruta.
        """
        self.id = str(uuid.uuid4())  # Identificador único
        self.source_ip = source_ip
        self.destination_ip = destination_ip
        self.content = content
        self.ttl = ttl
        self.path = LinkedList()  # LinkedList de nombres de dispositivos por los que ha pasado

    def hop(self, device_name):
        """
        Registra el salto por un dispositivo y decrementa el TTL.
        """
        self.path.append(device_name)
        self.ttl -= 1

    def is_expired(self):
        """
        Indica si el TTL ha expirado.
        """
        return self.ttl <= 0

    def __str__(self):
        """
        Representación en texto del paquete.
        """
        ruta_list = self.path.to_list()
        ruta = ' → '.join(ruta_list) if ruta_list else 'Sin ruta'
        return (f"Packet {self.id}\n"
                f"De: {self.source_ip} a {self.destination_ip}\n"
                f"Mensaje: {self.content}\n"
                f"TTL: {self.ttl}\n"
                f"Ruta: {ruta}")
