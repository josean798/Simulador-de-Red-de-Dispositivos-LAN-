
from LinkedList import LinkedList
from Packet import Packet

class Network:
    """
    Orquesta el conjunto de dispositivos y conexiones en la red LAN simulada.
    Gestiona la topología, el envío y procesamiento de paquetes, y las estadísticas globales.
    """

    def __init__(self):
        """
        Inicializa la red con una lista enlazada de dispositivos y variables para estadísticas.
        - devices: LinkedList de objetos Device presentes en la red.
        - total_packets_sent: total de paquetes enviados.
        - total_packets_delivered: total de paquetes entregados exitosamente.
        - total_packets_dropped: total de paquetes descartados por TTL.
        - hops_sum: suma total de saltos realizados por los paquetes entregados.
        - device_activity: diccionario con la cantidad de paquetes procesados por cada dispositivo.
        """
        self.devices = LinkedList()  # LinkedList de objetos Device
        self.connections = []
        self.total_packets_sent = 0
        self.total_packets_delivered = 0
        self.total_packets_dropped = 0
        self.hops_sum = 0
        self.device_activity = {}  # device_name: cantidad de paquetes procesados

    def add_device(self, device):
        """
        Agrega un nuevo dispositivo a la red y lo registra en las estadísticas.
        """
        self.devices.append(device)
        self.device_activity[device.name] = 0

    def remove_device(self, device):
        """
        Elimina un dispositivo de la red y de las estadísticas.
        """
        if self.devices.find(device):
            self.devices.remove(device)
            self.device_activity.pop(device.name, None)

    def get_device(self, name):
        """
        Busca y retorna un dispositivo por su nombre.
        Si no existe, retorna None.
        """
        for d in self.devices.to_list():
            if d.name == name:
                return d
        return None

    def connect(self, device1_name, iface1_name, device2_name, iface2_name):
        """
        Conecta dos interfaces de dos dispositivos distintos.
        Retorna True si la conexión fue exitosa, False en caso contrario.
        """
        d1 = self.get_device(device1_name)
        d2 = self.get_device(device2_name)
        if d1 and d2:
            iface1 = next((i for i in d1.interfaces if i.name == iface1_name), None)
            iface2 = next((i for i in d2.interfaces if i.name == iface2_name), None)
            if iface1 and iface2:
                iface1.connect(iface2)
                return True
        return False

    def disconnect(self, device1_name, iface1_name, device2_name, iface2_name):
        """
        Desconecta dos interfaces de dos dispositivos distintos.
        Retorna True si la desconexión fue exitosa, False en caso contrario.
        """
        d1 = self.get_device(device1_name)
        d2 = self.get_device(device2_name)
        if d1 and d2:
            iface1 = next((i for i in d1.interfaces if i.name == iface1_name), None)
            iface2 = next((i for i in d2.interfaces if i.name == iface2_name), None)
            if iface1 and iface2:
                iface1.disconnect(iface2)
                return True
        return False

    def list_devices(self):
        """
        Devuelve la lista de todos los dispositivos presentes en la red como lista de Python.
        """
        return self.devices.to_list()

    def set_device_status(self, device_name, status):
        """
        Cambia el estado ('up' o 'down') de un dispositivo por su nombre.
        Retorna True si el cambio fue exitoso, False en caso contrario.
        """
        device = self.get_device(device_name)
        if device:
            device.set_status(status)
            return True
        return False

    def send_packet(self, source_ip, destination_ip, content, ttl=5):
        """
        Crea y encola un paquete en la interfaz correspondiente al source_ip.
        Retorna True si el paquete fue encolado, False si no se encontró la interfaz.
        """
        for device in self.devices:
            for iface in device.interfaces:
                if iface.ip_address == source_ip:
                    packet = Packet(source_ip, destination_ip, content, ttl)
                    iface.enqueue_packet(packet)
                    self.total_packets_sent += 1
                    return True
        return False

    def tick(self):
        """
        Procesa todas las colas de cada dispositivo e interfaz, avanza los paquetes un paso en la simulación.
        - Si el dispositivo y la interfaz están 'up', procesa el siguiente paquete de la cola.
        - Si el paquete llega a su destino, se almacena en el historial del dispositivo.
        - Si el TTL expira, el paquete se descarta.
        - Si no, se reenvía a los vecinos conectados.
        """
        for device in self.devices:
            if device.status == 'up':
                for iface in device.interfaces:
                    if iface.status == 'up':
                        packet = iface.dequeue_packet()
                        if packet:
                            packet.hop(device.name)
                            self.device_activity[device.name] += 1
                            # Si llegó al destino
                            if packet.destination_ip == iface.ip_address:
                                device.receive_packet(packet)
                                self.total_packets_delivered += 1
                                self.hops_sum += len(packet.path)
                            elif packet.is_expired():
                                self.total_packets_dropped += 1
                            else:
                                # Reenviar a vecinos
                                for neighbor in iface.neighbors:
                                    if neighbor.status == 'up':
                                        neighbor.enqueue_packet(packet)
        # No retorna nada, solo procesa un paso de simulación

    def show_statistics(self):
        """
        Devuelve un string con las estadísticas globales de la red:
        - Total de paquetes enviados
        - Entregados
        - Descargados por TTL
        - Promedio de saltos por paquete
        - Dispositivo con más actividad
        """
        avg_hops = self.hops_sum / self.total_packets_delivered if self.total_packets_delivered else 0
        top_talker = max(self.device_activity, key=self.device_activity.get) if self.device_activity else None
        stats = (
            f"Total packets sent: {self.total_packets_sent}\n"
            f"Delivered: {self.total_packets_delivered}\n"
            f"Dropped (TTL): {self.total_packets_dropped}\n"
            f"Average hops: {avg_hops:.1f}\n"
            f"Top talker: {top_talker} (processed {self.device_activity.get(top_talker, 0)} packets)"
        )
        return stats
    
    def remove_device(self, device):
        """Elimina un dispositivo de la red"""
        # Eliminar primero todas sus conexiones
        connections = [c for c in self.connections 
                    if c[0] == device.name or c[2] == device.name]
        
        for conn in connections:
            self.disconnect(*conn)
        
        # Luego eliminar el dispositivo
        if self.devices.find(device):
            self.devices.remove(device)
            self.device_activity.pop(device.name, None)
            return True
        return False
