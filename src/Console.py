import json
from Mode import Mode
from Network import Network
from Device import Device
from Interface import Interface
from Packet import Packet
from network_statistics import NetworkStatistics
from network_persistence import save_network_config, load_network_config

class CLI:
    """
    Interfaz de línea de comandos mejorada para el simulador de red
    Incluye integración de módulos de estadísticas y persistencia.
    """
    
    def __init__(self):
        self.current_device = Device("HostRouter", "host")  # Dispositivo temporal
        self.network = Network()
        self.current_interface = None
        self.statistics = NetworkStatistics(self.network)
        self.init_commands()
    
    def init_commands(self):
        """Inicializa todos los comandos disponibles organizados por modo"""
        self.commands = {
            Mode.USER: {
                'enable': self._enable,
                'ping': self._ping,
                'send': self._send_packet,
                'show': self._show_user,
                'help': self._show_help
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
                'tick': self._process_tick,
                'process': self._process_tick,
                'exit': self._exit_privileged,
                'end': self._end_config,
                'help': self._show_help,
                'add_device': self._add_device,
                'remove_device': self._remove_device,
                'add_interface': self._add_interface,
                'console': self._console_device,
            },
            Mode.CONFIG: {
                'hostname': self._set_hostname,
                'interface': self._configure_interface,
                'exit': self._exit_config,
                'end': self._end_config,
                'help': self._show_help
            },
            Mode.CONFIG_IF: {
                'ip': self._set_ip_address,
                'shutdown': self._shutdown_interface,
                'no': self._no_shutdown,
                'exit': self._exit_interface,
                'end': self._end_config,
                'help': self._show_help
            }
        }

    def parse_command(self, command):
        """Procesa un comando ingresado por el usuario"""
        if not command.strip():
            print(self.get_prompt(), end='')
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
            show_cmd = ' '.join(parts[:2]).lower()
            if show_cmd in self.SHOW_COMMANDS:
                cmd = 'show'
                args = parts[1:]

        if cmd in self.commands[self.current_device.mode]:
            try:
                self.commands[self.current_device.mode][cmd](args)
            except Exception as e:
                print(f"Error ejecutando comando: {e}")
        else:
            print(f"% Comando '{cmd}' no reconocido o no disponible en el modo actual")

    def get_prompt(self):
        """Genera el prompt según el modo actual"""
        if self.current_device.mode == Mode.USER:
            return f"{self.current_device.name}>"
        elif self.current_device.mode == Mode.PRIVILEGED:
            return f"{self.current_device.name}#"
        elif self.current_device.mode == Mode.CONFIG:
            return f"{self.current_device.name}(config)#"
        elif self.current_device.mode == Mode.CONFIG_IF:
            return f"{self.current_device.name}(config-if)#"
        return ">"

    # Implementación de comandos
    def _enable(self, args):
        """Cambia a modo privilegiado"""
        if self.current_device.mode == Mode.USER:
            self.current_device.mode = Mode.PRIVILEGED
        print(self.get_prompt(), end='')

    def _disable(self, args):
        """Regresa a modo usuario"""
        self.current_device.mode = Mode.USER
        print(self.get_prompt(), end='')

    def _configure_terminal(self, args):
        """Entra en modo configuración global"""
        if self.current_device.mode == Mode.PRIVILEGED:
            self.current_device.mode = Mode.CONFIG
        print(self.get_prompt(), end='')

    def _exit_privileged(self, args):
        """Sale del modo privilegiado"""
        self._disable(args)

    def _exit_config(self, args):
        """Sale del modo configuración global"""
        if self.current_device.mode == Mode.CONFIG:
            self.current_device.mode = Mode.PRIVILEGED
        print(self.get_prompt(), end='')

    def _end_config(self, args):
        """Termina configuración y regresa a modo privilegiado"""
        self.current_device.mode = Mode.PRIVILEGED
        print(self.get_prompt(), end='')

    def _configure_interface(self, args):
        """Entra en modo configuración de interfaz"""
        if len(args) != 1:
            print("Uso: interface <nombre_interfaz>")
            return
            
        iface_name = args[0]
        iface = next((i for i in self.current_device.get_interfaces() if i.name == iface_name), None)
        
        if iface:
            self.current_interface = iface
            self.current_device.mode = Mode.CONFIG_IF
        else:
            print(f"% La interfaz {iface_name} no existe")
        print(self.get_prompt(), end='')

    def _exit_interface(self, args):
        """Sale del modo configuración de interfaz"""
        self.current_device.mode = Mode.CONFIG
        self.current_interface = None
        print(self.get_prompt(), end='')

    def _set_hostname(self, args):
        """Configura el nombre del dispositivo"""
        if len(args) != 1:
            print("Uso: hostname <nuevo_nombre>")
            return
            
        new_name = args[0]
        if self.network.get_device(new_name):
            print(f"% El nombre {new_name} ya está en uso")
        else:
            old_name = self.current_device.name
            self.current_device.name = new_name
            # Actualizar en la red
            device = self.network.get_device(old_name)
            if device:
                device.name = new_name
        print(self.get_prompt(), end='')

    def _set_ip_address(self, args):
        """Configura dirección IP de la interfaz actual"""
        if len(args) < 2 or args[0] != 'address':
            print("Uso: ip address <dirección_ip>")
            return
            
        ip = args[1]
        if self.current_interface:
            if self._validate_ip(ip):
                self.current_interface.set_ip(ip)
                print(f"Interface {self.current_interface.name} configurada con IP {ip}")
            else:
                print("% Dirección IP inválida")
        else:
            print("% Ninguna interfaz seleccionada")
        print(self.get_prompt(), end='')

    def _validate_ip(self, ip):
        """Valida formato básico de dirección IP"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        return all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)

    def _shutdown_interface(self, args):
        """Desactiva la interfaz actual"""
        if self.current_interface:
            self.current_interface.shutdown()
            print(f"Interface {self.current_interface.name} desactivada")
        print(self.get_prompt(), end='')

    def _no_shutdown(self, args):
        """Activa la interfaz actual"""
        if self.current_interface:
            self.current_interface.no_shutdown()
            print(f"Interface {self.current_interface.name} activada")
        print(self.get_prompt(), end='')

    def _connect(self, args):
        """Conecta dos interfaces de dispositivos"""
        if len(args) != 3:
            print("Uso: connect <interfaz_local> <dispositivo_remoto> <interfaz_remota>")
            return
            
        iface1, dev2, iface2 = args
        dev1 = self.current_device.name
        
        if self.network.connect(dev1, iface1, dev2, iface2):
            print(f"Conexión establecida: {dev1}:{iface1} <-> {dev2}:{iface2}")
        else:
            print("% No se pudo establecer la conexión. Verifique los nombres.")
        print(self.get_prompt(), end='')

    def _disconnect(self, args):
        """Desconecta dos interfaces"""
        if len(args) != 3:
            print("Uso: disconnect <interfaz_local> <dispositivo_remoto> <interfaz_remota>")
            return
            
        iface1, dev2, iface2 = args
        dev1 = self.current_device.name
        
        if self.network.disconnect(dev1, iface1, dev2, iface2):
            print(f"Conexión eliminada: {dev1}:{iface1} <-> {dev2}:{iface2}")
        else:
            print("% No se pudo eliminar la conexión. Verifique los nombres.")
        print(self.get_prompt(), end='')

    def _set_device_status(self, args):
        """Configura estado de un dispositivo (online/offline)"""
        if len(args) != 2:
            print("Uso: set_device_status <dispositivo> <online|offline>")
            return
            
        dev, status = args
        if status in ['online', 'offline']:
            if self.network.set_device_status(dev, 'up' if status == 'online' else 'down'):
                print(f"Estado de {dev} cambiado a {status}")
            else:
                print("% Dispositivo no encontrado")
        else:
            print("% Estado inválido. Use 'online' u 'offline'")
        print(self.get_prompt(), end='')

    def _list_devices(self, args):
        """Lista todos los dispositivos en la red"""
        print("Dispositivos en la red:")
        for device in self.network.list_devices():
            status = "online" if device.status == 'up' else "offline"
            print(f"- {device.name} ({device.device_type}, {status})")
        print(self.get_prompt(), end='')

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
        print(self.get_prompt(), end='')

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
        print(self.get_prompt(), end='')

    def _show_history(self, args):
        """Muestra historial de paquetes"""
        print("Historial de paquetes:")
        for i, packet in enumerate(self.current_device.get_history(), 1):
            print(f"{i}) De {packet.source_ip} a {packet.destination_ip}: {packet.content}")

    def _show_interfaces(self, args):
        """Muestra estado de las interfaces"""
        print("Interfaces:")
        for iface in self.current_device.get_interfaces():
            status = iface.status
            ip = iface.ip_address if iface.ip_address else "no asignada"
            neighbors = ', '.join([n.name for n in iface.neighbors.to_list()]) if iface.neighbors else "no conectada"
            print(f"- {iface.name}: IP {ip}, estado {status}, vecinos: {neighbors}")

    def _show_queue(self, args):
        """Muestra paquetes en cola"""
        print("Paquetes en cola:")
        for i, packet in enumerate(self.current_device.get_queue(), 1):
            print(f"{i}) De {packet.source_ip} a {packet.destination_ip}: {packet.content}")

    def _show_statistics(self, args):
        """
        Muestra estadísticas de red y permite exportarlas si se indica un archivo.
        Uso: show statistics [export <archivo>]
        """
        if args and args[0] == 'export' and len(args) > 1:
            filename = args[1]
            self.statistics.export_statistics(filename)
        else:
            self.statistics.show_statistics()
        print(self.get_prompt(), end='')

    def _send_packet(self, args):
        """Envía un paquete (simulado)"""
        if len(args) < 3:
            print("Uso: send <ip_origen> <ip_destino> <mensaje> [ttl]")
            return
            
        source, dest, message = args[0], args[1], ' '.join(args[2:-1]) if len(args) > 3 else args[2]
        ttl = int(args[-1]) if len(args) > 3 and args[-1].isdigit() else 5
        
        if self.network.send_packet(source, dest, message, ttl):
            print(f"Mensaje en cola para entrega: '{message}' de {source} a {dest} (TTL={ttl})")
        else:
            print("% No se encontró la interfaz con la IP de origen especificada")
        print(self.get_prompt(), end='')

    def _ping(self, args):
        """Simula comando ping"""
        if len(args) != 1:
            print("Uso: ping <ip_destino>")
            return
            
        print(f"Enviando ping a {args[0]}... (simulado)")
        print(self.get_prompt(), end='')

    def _process_tick(self, args):
        """Procesa un paso de simulación"""
        self.network.tick()
        print("Paso de simulación completado")
        print(self.get_prompt(), end='')

    def _save_config(self, args):
        """
        Guarda configuración actual a archivo usando el módulo de persistencia.
        Uso: save [archivo]
        """
        filename = args[0] if args else 'running-config.json'
        try:
            save_network_config(self.network, filename)
        except Exception as e:
            print(f"% Error guardando configuración: {e}")
        print(self.get_prompt(), end='')

    def _load_config(self, args):
        """
        Carga configuración desde archivo usando el módulo de persistencia.
        Uso: load <archivo>
        """
        if not args:
            print("Uso: load <archivo>")
            print(self.get_prompt(), end='')
            return
        filename = args[0]
        try:
            self.network = load_network_config(filename)
            self.statistics = NetworkStatistics(self.network)
            # Seleccionar primer dispositivo si existe
            devices = self.network.list_devices()
            if devices:
                self.current_device = devices[0]
            print(f"Configuración cargada desde {filename}")
        except Exception as e:
            print(f"% Error cargando configuración: {e}")
        print(self.get_prompt(), end='')

    def _show_help(self, args):
        """Muestra ayuda para los comandos disponibles"""
        print("Comandos disponibles:")
        for cmd, func in self.commands[self.current_device.mode].items():
            if cmd not in ['help', 'exit', 'end']:
                print(f"- {cmd}")

    def start(self):
        """Inicia la interfaz de línea de comandos"""
        print("Red LAN - CLI")
        print("Escriba 'help' para ver comandos disponibles o 'exit' para salir\n")
        
        while True:
            try:
                command = input(self.get_prompt()).strip()
                if not command:
                    continue
                if command.lower() == 'exit':
                    if self.current_device.mode in [Mode.USER, Mode.PRIVILEGED]:
                        break
                    else:
                        self.parse_command(command)
                else:
                    self.parse_command(command)
                    
            except KeyboardInterrupt:
                print("\nSaliendo...")
                break
            except Exception as e:
                print(f"\nError: {e}")

    def _add_device(self, args):
        """Añade un nuevo dispositivo a la red"""
        if len(args) != 2:
            print("Uso: add_device <nombre> <tipo>")
            print("Tipos válidos: router, switch, host, firewall")
            return
    
        name, dtype = args[0], args[1].lower()
        
        if dtype not in ['router', 'switch', 'host', 'firewall']:
            print("% Tipo de dispositivo inválido")
            return
            
        if self.network.get_device(name):
            print(f"% El dispositivo {name} ya existe")
            return
            
        device = Device(name, dtype)
        self.network.add_device(device)
        print(f"Dispositivo {name} ({dtype}) añadido")
        print(self.get_prompt(), end='')

    def _remove_device(self, args):
        """Elimina un dispositivo de la red"""
        if len(args) != 1:
            print("Uso: remove_device <nombre>")
            return
        
        name = args[0]
        device = self.network.get_device(name)
        
        if not device:
            print(f"% Dispositivo {name} no encontrado")
            return
            
        # Verificar conexiones primero
        connections = [c for c in self.network.connections 
                    if c[0] == name or c[2] == name]
        
        if connections:
            print("% Error: El dispositivo tiene conexiones activas")
            print("Desconéctelo primero con 'disconnect'")
            return
            
        self.network.remove_device(device)
        print(f"Dispositivo {name} eliminado")
        print(self.get_prompt(), end='')

    def _add_interface(self, args):
        """Añade una interfaz a un dispositivo"""
        if len(args) != 2:
            print("Uso: add_interface <dispositivo> <nombre_interfaz>")
            return
        
        dev_name, iface_name = args[0], args[1]
        device = self.network.get_device(dev_name)
        
        if not device:
            print(f"% Dispositivo {dev_name} no encontrado")
            return
            
        # Verificar si la interfaz ya existe
        if any(iface.name == iface_name for iface in device.get_interfaces()):
            print(f"% La interfaz {iface_name} ya existe en {dev_name}")
            return
            
        iface = Interface(iface_name)
        device.add_interface(iface)
        print(f"Interfaz {iface_name} añadida a {dev_name}")
        print(self.get_prompt(), end='')

    def _console_device(self, args):
        if not args:
            print("Dispositivos disponibles:")
            for device in self.network.list_devices():
                print(f"- {device.name} ({device.device_type})")
            return
        """Cambia al contexto de otro dispositivo"""
        if len(args) != 1:
            print("Uso: console <nombre_dispositivo>")
            return
        
        device_name = args[0]
        device = self.network.get_device(device_name)
        
        if not device:
            print(f"% Dispositivo {device_name} no encontrado")
            return
        # Guardar el modo actual antes de cambiar
        current_mode = self.current_device.mode
        # Cambiar al nuevo dispositivo
        self.current_device = device
        # Restaurar el modo en el nuevo dispositivo
        self.current_device.mode = current_mode
        print(f"Cambiado al dispositivo {device_name}")
        print(self.get_prompt(), end='')


if __name__ == "__main__":
    cli = CLI()
    cli.start()