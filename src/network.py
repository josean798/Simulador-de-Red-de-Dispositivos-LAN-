from LinkedList import LinkedList
from packet import Packet
from error_log import ErrorLog # Importar ErrorLog

class Network:
    """
    Orquesta el conjunto de dispositivos y conexiones en la red LAN simulada.
    Gestiona la topología, el envío y procesamiento de paquetes, y las estadísticas globales.
    """

    def __init__(self, error_log: ErrorLog): # Recibir error_log en el constructor
        """
        Inicializa la red con una lista enlazada de dispositivos y variables para estadísticas.
        - devices: LinkedList de objetos Device presentes en la red.
        - total_packets_sent: total de paquetes enviados.
        - total_packets_delivered: total de paquetes entregados exitosamente.
        - total_packets_dropped: total de paquetes descartados por TTL.
        - hops_sum: suma total de saltos realizados por los paquetes entregados.
        - device_activity: diccionario con la cantidad de paquetes procesados por cada dispositivo.
        - error_log: Instancia de ErrorLog para registrar eventos.
        """
        self.devices = LinkedList()  # LinkedList de objetos Device
        self.connections = [] # Almacena tuplas (dev1_name, iface1_name, dev2_name, iface2_name)
        self.total_packets_sent = 0
        self.total_packets_delivered = 0
        self.total_packets_dropped = 0
        self.hops_sum = 0
        self.device_activity = {}  # device_name: cantidad de paquetes procesados
        self.error_log = error_log # Asignar la instancia de ErrorLog

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
        # Eliminar primero todas sus conexiones
        connections_to_remove = [c for c in self.connections 
                                 if c[0] == device.name or c[2] == device.name]
        
        for conn in connections_to_remove:
            # Necesitamos obtener los objetos de interfaz para desconectarlos
            d1 = self.get_device(conn[0])
            d2 = self.get_device(conn[2])
            if d1 and d2:
                iface1 = next((i for i in d1.interfaces if i.name == conn[1]), None)
                iface2 = next((i for i in d2.interfaces if i.name == conn[3]), None)
                if iface1 and iface2:
                    iface1.disconnect(iface2)
            self.connections.remove(conn) # Eliminar de la lista de conexiones de la red

        if self.devices.find(device):
            self.devices.remove(device)
            self.device_activity.pop(device.name, None)
            return True
        return False

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
                # Almacenar la conexión en la lista de la red
                self.connections.append((device1_name, iface1_name, device2_name, iface2_name))
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
                # Eliminar la conexión de la lista de la red
                conn_to_remove = (device1_name, iface1_name, device2_name, iface2_name)
                if conn_to_remove in self.connections:
                    self.connections.remove(conn_to_remove)
                # También considerar la conexión inversa si se almacenó así
                conn_to_remove_rev = (device2_name, iface2_name, device1_name, iface1_name)
                if conn_to_remove_rev in self.connections:
                    self.connections.remove(conn_to_remove_rev)
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
        self.error_log.log_error(
            "PacketError", 
            f"No se encontró la interfaz con la IP de origen {source_ip} para enviar el paquete.",
            f"send {source_ip} {destination_ip} \"{content}\" {ttl}"
        )
        return False

    def tick(self):
        """
        Procesa todas las colas de cada dispositivo e interfaz, avanza los paquetes un paso en la simulación.
        - Si el dispositivo y la interfaz están 'up', procesa el siguiente paquete de la cola.
        - Si el paquete llega a su destino, se almacena en el historial del dispositivo.
        - Si el TTL expira, el paquete se descarta.
        - Si no, se reenvía al siguiente salto según la tabla de rutas o vecinos directos.
        """
        for device in self.devices:
            if device.status == 'up':
                for iface in device.interfaces:
                    if iface.status == 'up':
                        packet = iface.dequeue_packet()
                        if packet:
                            # Incrementar actividad del dispositivo
                            self.device_activity[device.name] += 1
                            
                            # --- Módulo 3: Aplicar políticas del Trie ---
                            policy = device.prefix_trie.lookup_policy(packet.destination_ip)
                            if policy:
                                if policy.get('block'):
                                    self.error_log.log_error(
                                        "PolicyViolation",
                                        f"Paquete de {packet.source_ip} a {packet.destination_ip} bloqueado por política en {device.name}.",
                                        f"policy block {packet.destination_ip}"
                                    )
                                    self.total_packets_dropped += 1
                                    continue # Descartar paquete
                                
                                ttl_min = policy.get('ttl-min')
                                if ttl_min is not None and packet.ttl < ttl_min:
                                    self.error_log.log_error(
                                        "PolicyViolation",
                                        f"Paquete de {packet.source_ip} a {packet.destination_ip} descartado por TTL ({packet.ttl}) menor que el mínimo ({ttl_min}) en {device.name}.",
                                        f"policy ttl-min {packet.destination_ip} {ttl_min}"
                                    )
                                    self.total_packets_dropped += 1
                                    continue # Descartar paquete

                            packet.hop(device.name) # Decrementar TTL y añadir a la ruta

                            # Si llegó al destino final
                            if packet.destination_ip == iface.ip_address:
                                device.receive_packet(packet)
                                self.total_packets_delivered += 1
                                self.hops_sum += len(packet.path.to_list()) # Usar to_list() para obtener la longitud
                                continue # Paquete entregado, no necesita reenvío
                            
                            # Si el TTL expiró después del hop
                            if packet.is_expired():
                                self.error_log.log_error(
                                    "PacketDropped",
                                    f"Paquete de {packet.source_ip} a {packet.destination_ip} descartado por TTL expirado en {device.name}.",
                                    f"tick (TTL expired)"
                                )
                                self.total_packets_dropped += 1
                                continue # Descartar paquete

                            # --- Módulo 1: Reenvío basado en AVL Route Table ---
                            next_hop_iface = None
                            route = device.route_table.lookup(packet.destination_ip)
                            
                            if route:
                                # Si hay una ruta en la tabla AVL, buscar la interfaz de salida
                                # Esto asume que next_hop es una IP de una interfaz vecina
                                for neighbor_iface in iface.neighbors.to_list():
                                    if neighbor_iface.ip_address == route.next_hop:
                                        next_hop_iface = neighbor_iface
                                        break
                                if not next_hop_iface:
                                    # Si el next_hop de la ruta no es un vecino directo de esta interfaz
                                    # Esto podría requerir una lógica de reenvío más compleja (ej. ARP, recursividad)
                                    # Por ahora, lo tratamos como un error o descarte si no es vecino directo.
                                    self.error_log.log_error(
                                        "RoutingError",
                                        f"Ruta encontrada para {packet.destination_ip} via {route.next_hop}, pero next-hop no es vecino directo de {device.name}:{iface.name}.",
                                        f"tick (routing lookup)"
                                    )
                                    self.total_packets_dropped += 1
                                    continue
                            else:
                                # Si no hay ruta en la tabla AVL, intentar reenvío a vecinos directos
                                # Esto simula un comportamiento de "connected route" o ARP
                                for neighbor_iface in iface.neighbors.to_list():
                                    # Buscar si la IP de destino es la IP de alguna interfaz vecina
                                    if neighbor_iface.ip_address == packet.destination_ip:
                                        next_hop_iface = neighbor_iface
                                        break
                                if not next_hop_iface:
                                    self.error_log.log_error(
                                        "RoutingError",
                                        f"No se encontró ruta para {packet.destination_ip} en {device.name} y no es vecino directo.",
                                        f"tick (no route)"
                                    )
                                    self.total_packets_dropped += 1
                                    continue # Descartar si no hay ruta ni es vecino directo

                            # Reenviar el paquete al siguiente salto
                            if next_hop_iface and next_hop_iface.status == 'up':
                                next_hop_iface.enqueue_packet(packet)
                            else:
                                self.error_log.log_error(
                                    "ForwardingError",
                                    f"No se pudo reenviar paquete de {packet.source_ip} a {packet.destination_ip} desde {device.name}:{iface.name}. Interfaz de salida inactiva o no encontrada.",
                                    f"tick (forwarding)"
                                )
                                self.total_packets_dropped += 1
                                
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
        
        # Asegurarse de que top_talker tenga un valor por defecto si no hay actividad
        top_talker_info = f"{top_talker} (processed {self.device_activity.get(top_talker, 0)} packets)" if top_talker else "N/A"

        stats = (
            f"Total packets sent: {self.total_packets_sent}\n"
            f"Delivered: {self.total_packets_delivered}\n"
            f"Dropped (TTL): {self.total_packets_dropped}\n"
            f"Average hops: {avg_hops:.1f}\n"
            f"Top talker: {top_talker_info}"
        )
        return stats

