# console.py
import json
from enum import Enum, auto
from stack import Stack
from queue import Queue
from node import LinkedList

class Mode(Enum):
    """Enumeración de modos de operación del CLI"""
    USER = auto()        # Modo usuario (Ejemplo: Router>)
    PRIVILEGED = auto()  # Modo privilegiado (Ejemplo: Router#)
    CONFIG = auto()      # Modo configuración global (Ejemplo: Router(config)#)
    CONFIG_IF = auto()   # Modo configuración de interfaz (Ejemplo: Router(config-if)#)

class Interface:
    """Representa una interfaz de red"""
    def __init__(self, name):
        self.name = name
        self.ip_address = None
        self.connected_to = None  # Tupla (dispositivo, interfaz)
        self.status = 'down'      # 'up' o 'down'
        self.neighbors = LinkedList()  # Dispositivos conectados

    def set_ip(self, ip):
        """Configura dirección IP"""
        if self.validate_ip(ip):
            self.ip_address = ip
            return True
        return False

    def validate_ip(self, ip):
        """Valida formato de IP (simplificado)"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        return all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)

    def set_status(self, status):
        """Configura estado de la interfaz"""
        if status in ('up', 'down'):
            self.status = status
            return True
        return False

class Device:
    """Representa un dispositivo de red"""
    def __init__(self, name, device_type):
        self.name = name
        self.type = device_type  # 'router', 'switch', 'host', 'firewall'
        self.mode = Mode.USER
        self.interfaces = {}     # Diccionario de interfaces
        self.packet_history = Stack()  # Historial de paquetes
        self.packet_queue = Queue()    # Cola de paquetes
        self.online = True
        self.config = []         # Configuración acumulada
        
    def add_interface(self, name):
        """Añade una nueva interfaz"""
        if name not in self.interfaces:
            self.interfaces[name] = Interface(name)
            return True
        return False

    def get_interface(self, name):
        """Obtiene una interfaz por nombre"""
        return self.interfaces.get(name)

    def process_packets(self):
        """Procesa paquetes en la cola"""
        processed = []
        while not self.packet_queue.is_empty():
            packet = self.packet_queue.dequeue()
            if packet:
                processed.append(packet)
                self.packet_history.push(packet)
        return processed

    def get_prompt(self):
        """Genera el prompt según el modo actual"""
        if self.mode == Mode.USER:
            return f"{self.name}>"
        elif self.mode == Mode.PRIVILEGED:
            return f"{self.name}#"
        elif self.mode == Mode.CONFIG:
            return f"{self.name}(config)#"
        elif self.mode == Mode.CONFIG_IF:
            return f"{self.name}(config-if)#"
        return ">"

class Network:
    """Representa la red completa"""
    def __init__(self):
        self.devices = {}        # Diccionario de dispositivos
        self.connections = []    # Lista de conexiones
        self.stats = {
            'total_packets': 0,
            'delivered': 0,
            'dropped': 0,
            'avg_hops': 0.0,
            'top_talker': None
        }

    def add_device(self, name, device_type):
        """Añade un nuevo dispositivo"""
        if name not in self.devices and device_type in ['router', 'switch', 'host', 'firewall']:
            self.devices[name] = Device(name, device_type)
            return True
        return False

    def connect_interfaces(self, dev1, iface1, dev2, iface2):
        """Conecta dos interfaces de dispositivos"""
        if (dev1 in self.devices and dev2 in self.devices and 
            iface1 in self.devices[dev1].interfaces and 
            iface2 in self.devices[dev2].interfaces):
            
            # Establecer conexión bidireccional
            self.devices[dev1].get_interface(iface1).connected_to = (dev2, iface2)
            self.devices[dev2].get_interface(iface2).connected_to = (dev1, iface1)
            
            # Añadir a lista de vecinos
            self.devices[dev1].get_interface(iface1).neighbors.append(dev2)
            self.devices[dev2].get_interface(iface2).neighbors.append(dev1)
            
            # Registrar conexión
            self.connections.append((dev1, iface1, dev2, iface2))
            return True
        return False

    def disconnect_interfaces(self, dev1, iface1, dev2, iface2):
        """Desconecta dos interfaces"""
        connection = (dev1, iface1, dev2, iface2)
        if connection in self.connections:
            # Eliminar conexión bidireccional
            self.devices[dev1].get_interface(iface1).connected_to = None
            self.devices[dev2].get_interface(iface2).connected_to = None
            
            # Eliminar de lista de vecinos
            self.devices[dev1].get_interface(iface1).neighbors.remove(dev2)
            self.devices[dev2].get_interface(iface2).neighbors.remove(dev1)
            
            # Eliminar de conexiones
            self.connections.remove(connection)
            return True
        return False

class CLI:
    """Interfaz de línea de comandos completa"""
    def __init__(self):
        self.current_device = None
        self.network = Network()
        self.current_interface = None  # Interfaz actual en modo config-if
        self.init_commands()
        
        # Dispositivo por defecto para pruebas
        self.network.add_device("Router1", "router")
        self.network.devices["Router1"].add_interface("g0/0")
        self.current_device = self.network.devices["Router1"]

    def init_commands(self):
        """Inicializa todos los comandos disponibles por modo"""
        self.commands = {
            Mode.USER: {
                'enable': self._enable,
                'send': self._send_packet,
                'ping': self._ping,
                'show': self._show_user
            },
            Mode.PRIVILEGED: {
                'disable': self._disable,
                'configure': self._configure_terminal,
                'show': self._show_privileged,
                'connect': self._connect,
                'disconnect': self._disconnect,
                'list_devices': self._list_devices,
                'set_device_status': self._set_device_status,
                'save': self._save_config,
                'load': self._load_config,
                'exit': self._exit_privileged,
                'end': lambda _: None  # No hace nada en este modo
            },
            Mode.CONFIG: {
                'hostname': self._set_hostname,
                'interface': self._configure_interface,
                'exit': self._exit_config,
                'end': self._end_config
            },
            Mode.CONFIG_IF: {
                'ip': self._set_ip_address,
                'shutdown': self._shutdown_interface,
                'no': self._no_shutdown,
                'exit': self._exit_interface,
                'end': self._end_config
            }
        }

    def parse_command(self, command):
        """Procesa un comando ingresado por el usuario"""
        if not command.strip():
            print(self.current_device.get_prompt(), end='')
            return

        parts = command.strip().split()
        cmd = parts[0].lower()
        args = parts[1:]

        # Manejo de comandos compuestos
        if cmd == 'configure' and len(parts) > 1 and parts[1].lower() == 'terminal':
            cmd = 'configure'
        elif cmd == 'no' and len(parts) > 1 and parts[1].lower() == 'shutdown':
            cmd = 'no'
        elif cmd == 'show' and len(parts) > 1:
            # Manejar subcomandos de show
            show_cmd = ' '.join(parts[:2]).lower()
            if show_cmd in ['show history', 'show interfaces', 'show queue', 'show statistics']:
                cmd = 'show'
                args = parts[1:]

        # Ejecutar comando si existe en el modo actual
        if cmd in self.commands[self.current_device.mode]:
            try:
                self.commands[self.current_device.mode][cmd](args)
            except Exception as e:
                print(f"Error ejecutando comando: {e}")
        else:
            print(f"% Comando '{cmd}' no reconocido o no disponible en el modo actual")

    # --- Implementación de comandos ---

    def _enable(self, args):
        """Cambia a modo privilegiado"""
        if self.current_device.mode == Mode.USER:
            self.current_device.mode = Mode.PRIVILEGED
        print(self.current_device.get_prompt(), end='')

    def _disable(self, args):
        """Regresa a modo usuario"""
        self.current_device.mode = Mode.USER
        print(self.current_device.get_prompt(), end='')

    def _configure_terminal(self, args):
        """Entra en modo configuración global"""
        if self.current_device.mode == Mode.PRIVILEGED:
            self.current_device.mode = Mode.CONFIG
        print(self.current_device.get_prompt(), end='')

    def _exit_privileged(self, args):
        """Sale del modo privilegiado"""
        self._disable(args)

    def _exit_config(self, args):
        """Sale del modo configuración global"""
        if self.current_device.mode == Mode.CONFIG:
            self.current_device.mode = Mode.PRIVILEGED
        print(self.current_device.get_prompt(), end='')

    def _end_config(self, args):
        """Termina configuración y regresa a modo privilegiado"""
        self.current_device.mode = Mode.PRIVILEGED
        print(self.current_device.get_prompt(), end='')

    def _configure_interface(self, args):
        """Entra en modo configuración de interfaz"""
        if len(args) != 1:
            print("Uso: interface <nombre_interfaz>")
            return
            
        iface_name = args[0]
        if iface_name in self.current_device.interfaces:
            self.current_interface = self.current_device.get_interface(iface_name)
            self.current_device.mode = Mode.CONFIG_IF
        else:
            print(f"% La interfaz {iface_name} no existe")
        print(self.current_device.get_prompt(), end='')

    def _exit_interface(self, args):
        """Sale del modo configuración de interfaz"""
        self.current_device.mode = Mode.CONFIG
        self.current_interface = None
        print(self.current_device.get_prompt(), end='')

    def _set_hostname(self, args):
        """Configura el nombre del dispositivo"""
        if len(args) != 1:
            print("Uso: hostname <nuevo_nombre>")
            return
            
        new_name = args[0]
        if new_name in self.network.devices:
            print(f"% El nombre {new_name} ya está en uso")
        else:
            old_name = self.current_device.name
            self.network.devices[new_name] = self.network.devices.pop(old_name)
            self.current_device.name = new_name
        print(self.current_device.get_prompt(), end='')

    def _set_ip_address(self, args):
        """Configura dirección IP de la interfaz actual"""
        if len(args) < 2 or args[0] != 'address':
            print("Uso: ip address <dirección_ip>")
            return
            
        ip = args[1]
        if self.current_interface and self.current_interface.set_ip(ip):
            print(f"Interface {self.current_interface.name} configurada con IP {ip}")
        else:
            print("% Dirección IP inválida o ninguna interfaz seleccionada")
        print(self.current_device.get_prompt(), end='')

    def _shutdown_interface(self, args):
        """Desactiva la interfaz actual"""
        if self.current_interface and self.current_interface.set_status('down'):
            print(f"Interface {self.current_interface.name} desactivada")
        print(self.current_device.get_prompt(), end='')

    def _no_shutdown(self, args):
        """Activa la interfaz actual"""
        if self.current_interface and self.current_interface.set_status('up'):
            print(f"Interface {self.current_interface.name} activada")
        print(self.current_device.get_prompt(), end='')

    def _connect(self, args):
        """Conecta dos interfaces de dispositivos"""
        if len(args) != 3:
            print("Uso: connect <interfaz_local> <dispositivo_remoto> <interfaz_remota>")
            return
            
        iface1, dev2, iface2 = args
        dev1 = self.current_device.name
        
        if self.network.connect_interfaces(dev1, iface1, dev2, iface2):
            print(f"Conexión establecida: {dev1}:{iface1} <-> {dev2}:{iface2}")
        else:
            print("% No se pudo establecer la conexión. Verifique los nombres.")
        print(self.current_device.get_prompt(), end='')

    def _disconnect(self, args):
        """Desconecta dos interfaces"""
        if len(args) != 3:
            print("Uso: disconnect <interfaz_local> <dispositivo_remoto> <interfaz_remota>")
            return
            
        iface1, dev2, iface2 = args
        dev1 = self.current_device.name
        
        if self.network.disconnect_interfaces(dev1, iface1, dev2, iface2):
            print(f"Conexión eliminada: {dev1}:{iface1} <-> {dev2}:{iface2}")
        else:
            print("% No se pudo eliminar la conexión. Verifique los nombres.")
        print(self.current_device.get_prompt(), end='')

    def _set_device_status(self, args):
        """Configura estado de un dispositivo (online/offline)"""
        if len(args) != 2:
            print("Uso: set_device_status <dispositivo> <online|offline>")
            return
            
        dev, status = args
        if dev in self.network.devices and status in ['online', 'offline']:
            self.network.devices[dev].online = (status == 'online')
            print(f"Estado de {dev} cambiado a {status}")
        else:
            print("% Dispositivo no encontrado o estado inválido")
        print(self.current_device.get_prompt(), end='')

    def _list_devices(self, args):
        """Lista todos los dispositivos en la red"""
        print("Dispositivos en la red:")
        for name, device in self.network.devices.items():
            status = "online" if device.online else "offline"
            print(f"- {name} ({device.type}, {status})")
        print(self.current_device.get_prompt(), end='')

    def _show_user(self, args):
        """Comandos show disponibles en modo usuario"""
        if not args:
            print("Comandos show disponibles en modo usuario:")
            print("  show interfaces - Muestra interfaces del dispositivo")
            return
            
        subcmd = args[0].lower()
        if subcmd == 'interfaces':
            self._show_interfaces(args[1:])
        else:
            print("% Comando show no reconocido")

    def _show_privileged(self, args):
        """Comandos show disponibles en modo privilegiado"""
        if not args:
            print("Comandos show disponibles:")
            print("  show history - Muestra historial de paquetes")
            print("  show interfaces - Muestra interfaces del dispositivo")
            print("  show queue - Muestra cola de paquetes pendientes")
            print("  show statistics - Muestra estadísticas de red")
            return
            
        subcmd = args[0].lower()
        if subcmd == 'history':
            self._show_history(args[1:])
        elif subcmd == 'interfaces':
            self._show_interfaces(args[1:])
        elif subcmd == 'queue':
            self._show_queue(args[1:])
        elif subcmd == 'statistics':
            self._show_statistics(args[1:])
        else:
            print("% Comando show no reconocido")
        print(self.current_device.get_prompt(), end='')

    def _show_history(self, args):
        """Muestra historial de paquetes"""
        print("Historial de paquetes:")
        for i, packet in enumerate(self.current_device.packet_history.get_all(), 1):
            print(f"{i}) De {packet['source']} a {packet['destination']}: {packet['message']}")

    def _show_interfaces(self, args):
        """Muestra estado de las interfaces"""
        print("Interfaces:")
        for name, iface in self.current_device.interfaces.items():
            status = iface.status
            ip = iface.ip_address if iface.ip_address else "no asignada"
            connected = f"conectada a {iface.connected_to[0]}:{iface.connected_to[1]}" if iface.connected_to else "no conectada"
            print(f"- {name}: IP {ip}, estado {status}, {connected}")

    def _show_queue(self, args):
        """Muestra paquetes en cola"""
        print("Paquetes en cola:")
        for i, packet in enumerate(self.current_device.packet_queue.get_all(), 1):
            print(f"{i}) De {packet['source']} a {packet['destination']}: {packet['message']}")

    def _show_statistics(self, args):
        """Muestra estadísticas de red"""
        stats = self.network.stats
        print("Estadísticas de red:")
        print(f"Paquetes totales: {stats['total_packets']}")
        print(f"Entregados: {stats['delivered']}")
        print(f"Descartados: {stats['dropped']}")
        print(f"Promedio de saltos: {stats['avg_hops']:.1f}")
        if stats['top_talker']:
            print(f"Dispositivo más activo: {stats['top_talker']}")

    def _send_packet(self, args):
        """Envía un paquete (simulado)"""
        if len(args) < 3:
            print("Uso: send <ip_origen> <ip_destino> <mensaje> [ttl]")
            return
            
        source, dest, message = args[0], args[1], ' '.join(args[2:-1]) if len(args) > 3 else args[2]
        ttl = int(args[-1]) if args[-1].isdigit() else 5
        
        packet = {
            'source': source,
            'destination': dest,
            'message': message,
            'ttl': ttl,
            'path': []
        }
        
        # Simular envío (en una implementación real esto iría a la cola)
        print(f"Mensaje en cola para entrega: '{message}' de {source} a {dest} (TTL={ttl})")
        print(self.current_device.get_prompt(), end='')

    def _ping(self, args):
        """Simula comando ping"""
        if len(args) != 1:
            print("Uso: ping <ip_destino>")
            return
            
        print(f"Enviando ping a {args[0]}... (simulado)")
        print(self.current_device.get_prompt(), end='')

    def _save_config(self, args):
        """Guarda configuración actual a archivo"""
        filename = args[0] if args else 'running-config.json'
        try:
            config = {
                'devices': {},
                'connections': self.network.connections
            }
            
            for name, device in self.network.devices.items():
                config['devices'][name] = {
                    'type': device.type,
                    'interfaces': {
                        ifname: {
                            'ip': iface.ip_address,
                            'status': iface.status
                        } 
                        for ifname, iface in device.interfaces.items()
                    }
                }
            
            with open(filename, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"Configuración guardada en {filename}")
        except Exception as e:
            print(f"% Error guardando configuración: {e}")
        print(self.current_device.get_prompt(), end='')

    def _load_config(self, args):
        """Carga configuración desde archivo"""
        if not args:
            print("Uso: load config <archivo>")
            return
            
        filename = args[0]
        try:
            with open(filename) as f:
                config = json.load(f)
            
            # Limpiar red actual
            self.network = Network()
            
            # Cargar dispositivos
            for name, data in config['devices'].items():
                self.network.add_device(name, data['type'])
                device = self.network.devices[name]
                for ifname, ifdata in data['interfaces'].items():
                    device.add_interface(ifname)
                    iface = device.get_interface(ifname)
                    if ifdata['ip']:
                        iface.set_ip(ifdata['ip'])
                    iface.set_status(ifdata['status'])
            
            # Establecer conexiones
            for conn in config['connections']:
                self.network.connect_interfaces(*conn)
            
            print(f"Configuración cargada desde {filename}")
            self.current_device = next(iter(self.network.devices.values()))  # Seleccionar primer dispositivo
        except Exception as e:
            print(f"% Error cargando configuración: {e}")
        print(self.current_device.get_prompt(), end='')

    def start(self):
        """Inicia la interfaz de línea de comandos"""
        print("Simulador de Red LAN - CLI estilo Router")
        print("Escriba 'help' para ver comandos disponibles o 'exit' para salir\n")
        
        while True:
            try:
                command = input(self.current_device.get_prompt()).strip()
                if command.lower() == 'exit':
                    break
                self.parse_command(command)
            except KeyboardInterrupt:
                print("\nSaliendo...")
                break
            except Exception as e:
                print(f"\nError: {e}")

# Ejemplo de uso
if __name__ == "__main__":
    cli = CLI()
    cli.start()