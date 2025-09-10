from Mode import Mode
from LinkedList import LinkedList
from Queue import Queue
from Stack import Stack
from AVLTree import AVLTree, Route
from Trie import Trie
from BST import BST

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
        self.routing_table = AVLTree()  # Tabla de rutas AVL
        self.policy_trie = Trie()  # Trie para políticas de prefijos  
        self.arp_table = BST()  # BST para tabla ARP  

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

    def add_route(self, prefix, mask, next_hop, metric=1):
        """
        Agrega una ruta a la tabla de rutas.
        """
        route = Route(prefix, mask, next_hop, metric)
        self.routing_table.add_route(route)

    def del_route(self, prefix, mask):
        """
        Elimina una ruta de la tabla de rutas.
        """
        route = Route(prefix, mask, "", 1)  # dummy
        self.routing_table.del_route(route)

    def lookup_route(self, dest_ip):
        """
        Busca la mejor ruta para el destino.
        """
        return self.routing_table.lookup(dest_ip)

    def get_routes(self):
        """
        Devuelve todas las rutas.
        """
        return self.routing_table.get_routes()

    def show_routing_table(self):
        """
        Muestra la tabla de rutas.
        """
        routes = self.get_routes()
        if not routes:
            print("No routes configured")
        else:
            for route in routes:
                print(route)
        print("Default: none")

    def show_avl_stats(self):
        """
        Muestra estadísticas del AVL.
        """
        stats = self.routing_table.get_stats()
        print(f"nodes={stats['nodes']} height={stats['height']} rotations: LL={stats['rotations']['LL']} LR={stats['rotations']['LR']} RL={stats['rotations']['RL']} RR={stats['rotations']['RR']}")

    def get_routing_table_data(self):
        """
        Devuelve la tabla de rutas como lista de diccionarios para serialización.
        """
        routes = self.get_routes()
        return [{'prefix': r.prefix, 'mask': r.mask, 'next_hop': r.next_hop, 'metric': r.metric} for r in routes]

    def show_route_tree(self):
        """
        Muestra el árbol de rutas.
        """
        self.routing_table.print_tree(self.routing_table.root)

    def set_policy(self, prefix, mask, policy_type, policy_value=None):
        """
        Establece una política para un prefijo.
        """
        try:
            self.policy_trie.insert(prefix, mask, policy_type, policy_value)
        except ValueError as e:
            print(f"% Error: {e}")

    def unset_policy(self, prefix, mask):
        """
        Elimina la política para un prefijo.
        """
        try:
            self.policy_trie.delete(prefix, mask)
        except ValueError as e:
            print(f"% Error: {e}")

    def get_policy(self, ip):
        """
        Obtiene la política para una IP (longest match).
        """
        return self.policy_trie.search(ip)

    def get_policy_data(self):
        """
        Devuelve la lista de políticas para serialización.
        """
        return self.policy_trie.get_policies()

