import json
from Mode import Mode
from Network import Network
from Device import Device
from Interface import Interface
from Packet import Packet
from Network_statistics import NetworkStatistics
from Network_persistence import save_network_config, load_network_config
from ErrorLog import ErrorLog
from BTree import BTree
from datetime import datetime

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
        self.btree = BTree()
        self.error_log = ErrorLog()
        self.network.error_log = self.error_log
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
                'load_config': self._load_config_key,
                'tick': self._process_tick,
                'process': self._process_tick,
                'exit': self._exit_privileged,
                'end': self._end_config,
                'help': self._show_help,
                'add_device': self._add_device,
                'remove_device': self._remove_device,
                'add_interface': self._add_interface,
                'console': self._console_device,
                'save_snapshot': self._save_snapshot,
                'load_config': self._load_config_key,
                'show_snapshots': self._show_snapshots,
                'btree_stats': self._btree_stats,
            },
            Mode.CONFIG: {
                'hostname': self._set_hostname,
                'interface': self._configure_interface,
                'ip': self._ip_command,
                'policy': self._policy_command,
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
        # Subcomandos válidos para show
        self.SHOW_COMMANDS = [
            'show history',
            'show interfaces',
            'show queue',
            'show statistics',
            'show ip',
            'show ip route',
            'show route avl-stats',
            'show ip route-tree',
            'show snapshots',
            'show ip prefix-tree',
            'show error-log'
        ]

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
        elif cmd == 'save' and len(parts) > 1 and parts[1].lower() == 'snapshot':
            cmd = 'save_snapshot'
            args = parts[2:]
        elif cmd == 'load' and len(parts) > 1 and parts[1].lower() == 'config':
            cmd = 'load_config'
            args = parts[2:]
        elif cmd == 'btree' and len(parts) > 1 and parts[1].lower() == 'stats':
            cmd = 'btree_stats'
            args = parts[2:]
        elif cmd == 'show' and len(parts) > 1:
            full_show = ' '.join(parts).lower()
            if full_show in self.SHOW_COMMANDS:
                cmd = 'show'
                args = parts[1:]

        if cmd in self.commands[self.current_device.mode]:
            try:
                self.commands[self.current_device.mode][cmd](args)
            except Exception as e:
                self.error_log.log_error("CommandError", str(e), command)
                print(f"Error ejecutando comando: {e}")
        else:
            self.error_log.log_error("CommandNotFound", f"Comando '{cmd}' no reconocido", command)
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
            self.error_log.log_error("InterfaceNotFound", f"La interfaz {iface_name} no existe", f"interface {iface_name}")
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
            self.error_log.log_error("HostnameInUse", f"El nombre {new_name} ya está en uso", f"hostname {new_name}")
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
                self.error_log.log_error("InvalidIP", f"Dirección IP inválida: {ip}", f"ip address {ip}")
                print("% Dirección IP inválida")
        else:
            self.error_log.log_error("NoInterfaceSelected", "Ninguna interfaz seleccionada", f"ip address {ip}")
            print("% Ninguna interfaz seleccionada")
        print(self.get_prompt(), end='')

    def _validate_ip(self, ip):
        """Valida formato básico de dirección IP"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        return all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)

    def _validate_mask(self, mask):
        """Valida formato de máscara de red"""
        if mask.startswith('/'):
            try:
                length = int(mask[1:])
                return 0 <= length <= 32
            except ValueError:
                return False
        else:
            parts = mask.split('.')
            if len(parts) != 4:
                return False
            try:
                return all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)
            except ValueError:
                return False

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

    def _ip_command(self, args):
        """Maneja comandos ip"""
        if not args or args[0] != 'route':
            print("Uso: ip route <add|del> <prefix> <mask> [via <next-hop>] [metric N]")
            return
        if len(args) < 4:
            print("Uso: ip route <add|del> <prefix> <mask> [via <next-hop>] [metric N]")
            return
        action = args[1]
        prefix = args[2]
        mask = args[3]
        next_hop = ""
        metric = 1
        if action == 'add':
            if len(args) > 4:
                if 'via' in args:
                    idx = args.index('via')
                    if idx + 1 < len(args):
                        next_hop = args[idx + 1]
                if 'metric' in args:
                    idx = args.index('metric')
                    if idx + 1 < len(args):
                        try:
                            metric = int(args[idx + 1])
                        except ValueError:
                            self.error_log.log_error("InvalidMetric", f"Métrica inválida: {args[idx + 1]}", f"ip route add {prefix} {mask} metric {args[idx + 1]}")
                            print("Métrica inválida")
                            return
            self.current_device.add_route(prefix, mask, next_hop, metric)
            print(f"Ruta añadida: {prefix}/{mask} via {next_hop} metric {metric}")
        elif action == 'del':
            self.current_device.del_route(prefix, mask)
            print(f"Ruta eliminada: {prefix}/{mask}")
        else:
            self.error_log.log_error("InvalidAction", f"Acción inválida: {action}", f"ip route {action} {prefix} {mask}")
            print("Acción inválida. Use 'add' o 'del'")
        print(self.get_prompt(), end='')

    def _policy_command(self, args):
        """Maneja comandos policy"""
        if not args:
            print("Uso: policy <set|unset> <prefix> <mask> [tipo valor]")
            return
        action = args[0]
        if action == 'set':
            if len(args) < 4:
                print("Uso: policy set <prefix> <mask> <tipo> [valor]")
                return
            prefix = args[1]
            mask = args[2]
            if not self._validate_ip(prefix):
                self.error_log.log_error("InvalidIP", f"Prefijo IP inválido: {prefix}", f"policy set {prefix} {mask}")
                print("% Prefijo IP inválido")
                return
            if not self._validate_mask(mask):
                self.error_log.log_error("InvalidMask", f"Máscara inválida: {mask}", f"policy set {prefix} {mask}")
                print("% Máscara inválida")
                return
            policy_type = args[3]
            policy_value = args[4] if len(args) > 4 else None
            if policy_type == 'block':
                self.current_device.set_policy(prefix, mask, policy_type)
                print(f"Política block aplicada a {prefix}/{mask}")
            elif policy_type == 'ttl-min':
                if policy_value is None:
                    print("Uso: policy set <prefix> <mask> ttl-min <valor>")
                    return
                try:
                    int(policy_value)
                except ValueError:
                    self.error_log.log_error("InvalidTTL", f"Valor de TTL inválido: {policy_value}", f"policy set {prefix} {mask} ttl-min {policy_value}")
                    print("% Valor de TTL inválido")
                    return
                self.current_device.set_policy(prefix, mask, policy_type, int(policy_value))
                print(f"Política ttl-min={policy_value} aplicada a {prefix}/{mask}")
            else:
                self.error_log.log_error("InvalidPolicyType", f"Tipo de política inválido: {policy_type}", f"policy set {prefix} {mask} {policy_type}")
                print("Tipo de política inválido")
        elif action == 'unset':
            if len(args) < 3:
                print("Uso: policy unset <prefix> <mask>")
                return
            prefix = args[1]
            mask = args[2]
            if not self._validate_ip(prefix):
                self.error_log.log_error("InvalidIP", f"Prefijo IP inválido: {prefix}", f"policy unset {prefix} {mask}")
                print("% Prefijo IP inválido")
                return
            if not self._validate_mask(mask):
                self.error_log.log_error("InvalidMask", f"Máscara inválida: {mask}", f"policy unset {prefix} {mask}")
                print("% Máscara inválida")
                return
            self.current_device.unset_policy(prefix, mask)
            print(f"Política eliminada de {prefix}/{mask}")
        else:
            self.error_log.log_error("InvalidPolicyAction", f"Acción inválida: {action}", f"policy {action}")
            print("Acción inválida. Use 'set' o 'unset'")
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
            self.error_log.log_error("ConnectionError", f"No se pudo establecer la conexión: {dev1}:{iface1} <-> {dev2}:{iface2}", f"connect {iface1} {dev2} {iface2}")
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
            self.error_log.log_error("DisconnectionError", f"No se pudo eliminar la conexión: {dev1}:{iface1} <-> {dev2}:{iface2}", f"disconnect {iface1} {dev2} {iface2}")
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
                self.error_log.log_error("DeviceNotFound", f"Dispositivo no encontrado: {dev}", f"set_device_status {dev} {status}")
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
            print("  show ip route - Muestra tabla de rutas")
            print("  show route avl-stats - Muestra estadísticas del AVL")
            print("  show ip route-tree - Muestra árbol de rutas")
            print("  show ip prefix-tree - Muestra árbol de prefijos")
            print("  show error-log - Muestra registro de errores")
            print("  show snapshots - Muestra snapshots indexados")
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
        elif subcmd == 'ip' and len(args) > 1 and args[1] == 'route':
            self.current_device.show_routing_table()
        elif subcmd == 'route' and len(args) > 1 and args[1] == 'avl-stats':
            self.current_device.show_avl_stats()
        elif subcmd == 'ip' and len(args) > 1 and args[1] == 'route-tree':
            self.current_device.show_route_tree()
        elif subcmd == 'ip' and len(args) > 1 and args[1] == 'prefix-tree':
            self.current_device.policy_trie.print_tree()
        elif subcmd == 'error-log':
            n = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
            errors = self.error_log.get_errors(n)
            if not errors:
                print("No hay errores registrados")
            else:
                for error in errors:
                    print(error)
        elif subcmd == 'ip':
            print("Comandos show ip disponibles:")
            print("  show ip route - Muestra tabla de rutas")
            print("  show ip route-tree - Muestra árbol de rutas")
            print("  show ip prefix-tree - Muestra árbol de prefijos")
        elif subcmd == 'snapshots':
            self._show_snapshots(args[1:])
        else:
            print("% Comando show no reconocido")
        print(self.get_prompt(), end='')

    def _show_history(self, args):
        """
        Muestra historial de paquetes enviados y recibidos por el dispositivo actual.
        """
        sent, received = self.current_device.get_history()

        print("Historial de paquetes enviados:")
        if sent:
            for i, packet in enumerate(sent, 1):
                path = ' → '.join(packet.path.to_list()) if hasattr(packet, 'path') and hasattr(packet.path, 'to_list') else 'N/A'
                ttl_expired = 'Sí' if getattr(packet, 'ttl', 1) == 0 else 'No'
                print(f"{i}) A {packet.destination_ip}: \"{packet.content}\" | TTL al enviar: {getattr(packet, 'ttl', 'N/A')} | Ruta: {path} | TTL expirado? {ttl_expired}")
        else:
            print("  (Ningún paquete enviado)")

        print("\nHistorial de paquetes recibidos:")
        if received:
            for i, packet in enumerate(received, 1):
                path = ' → '.join(packet.path.to_list()) if hasattr(packet, 'path') and hasattr(packet.path, 'to_list') else 'N/A'
                ttl_expired = 'Sí' if getattr(packet, 'ttl', 1) == 0 else 'No'
                print(f"{i}) De {packet.source_ip}: \"{packet.content}\" | TTL al recibir: {getattr(packet, 'ttl', 'N/A')} | Ruta: {path} | TTL expirado? {ttl_expired}")
        else:
            print("  (Ningún paquete recibido)")

    def _show_interfaces(self, args):
        """Muestra estado de las interfaces"""
        print("Interfaces:")
        for iface in self.current_device.get_interfaces():
            status = iface.status
            ip = iface.ip_address if iface.ip_address else "no asignada"
            neighbors = 'no conectada'
            if iface.neighbors:
                if hasattr(iface.neighbors, 'to_list'):
                    vecinos_list = iface.neighbors.to_list()
                    neighbors = ', '.join([n.name for n in vecinos_list]) if vecinos_list else 'no conectada'
                else:
                    neighbors = str(iface.neighbors)
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
        """Envía un paquete (simulado) y registra en historial de emisor y receptor"""
        if len(args) < 3:
            print("Uso: send <ip_origen> <ip_destino> <mensaje> [ttl]")
            return

        source, dest, message = args[0], args[1], ' '.join(args[2:-1]) if len(args) > 3 else args[2]
        ttl = int(args[-1]) if len(args) > 3 and args[-1].isdigit() else 5

        # Enviar el paquete usando la lógica de red
        sent = self.network.send_packet(source, dest, message, ttl)
        if sent:
            print(f"Mensaje en cola para entrega: '{message}' de {source} a {dest} (TTL={ttl})")
            # Registrar en historial de enviados del emisor
            from Packet import Packet
            pkt = Packet(source, dest, message, ttl)
            if hasattr(self.current_device, 'add_sent'):
                self.current_device.add_sent(pkt)

            # Buscar el receptor por IP de destino
            receptor = None
            for device in self.network.list_devices():
                for iface in device.get_interfaces():
                    if iface.ip_address == dest:
                        receptor = device
                        break
                if receptor:
                    break
            if receptor and hasattr(receptor, 'add_received'):
                from Packet import Packet
                pkt2 = Packet(source, dest, message, ttl)
                receptor.add_received(pkt2)
        else:
            self.error_log.log_error("SendError", f"No se encontró la interfaz con la IP de origen especificada: {source}", f"send {source} {dest} {message}")
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
            self.error_log.log_error("SaveConfigError", f"Error guardando configuración: {e}", f"save {filename}")
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
            # Cargar config manualmente para poder asignar status a interfaces
            import json
            from Interface import Interface
            from Device import Device
            with open(filename) as f:
                config = json.load(f)
            self.network = Network()
            for device_data in config['devices']:
                device = Device(device_data['name'], device_data['type'])
                device.set_status(device_data['status'])
                self.network.add_device(device)
                for iface_data in device_data['interfaces']:
                    iface = Interface(iface_data['name'])
                    if iface_data['ip']:
                        iface.set_ip(iface_data['ip'])
                    iface.status = iface_data['status']  # Asignar status directamente
                    device.add_interface(iface)
            for conn in config['connections']:
                self.network.connect(*conn)
            self.statistics = NetworkStatistics(self.network)
            devices = self.network.list_devices()
            if devices:
                self.current_device = devices[0]
            print(f"Configuración cargada desde {filename}")
        except Exception as e:
            self.error_log.log_error("LoadConfigError", f"Error cargando configuración: {e}", f"load {filename}")
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
            self.error_log.log_error("InvalidDeviceType", f"Tipo de dispositivo inválido: {dtype}", f"add_device {name} {dtype}")
            print("% Tipo de dispositivo inválido")
            return
            
        if self.network.get_device(name):
            self.error_log.log_error("DeviceExists", f"El dispositivo {name} ya existe", f"add_device {name} {dtype}")
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
            self.error_log.log_error("DeviceNotFound", f"Dispositivo {name} no encontrado", f"remove_device {name}")
            print(f"% Dispositivo {name} no encontrado")
            return
            
        # Verificar conexiones primero
        connections = [c for c in self.network.connections 
                    if c[0] == name or c[2] == name]
        
        if connections:
            self.error_log.log_error("DeviceHasConnections", f"El dispositivo {name} tiene conexiones activas", f"remove_device {name}")
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
            self.error_log.log_error("DeviceNotFound", f"Dispositivo {dev_name} no encontrado", f"add_interface {dev_name} {iface_name}")
            print(f"% Dispositivo {dev_name} no encontrado")
            return
            
        # Verificar si la interfaz ya existe
        if any(iface.name == iface_name for iface in device.get_interfaces()):
            self.error_log.log_error("InterfaceExists", f"La interfaz {iface_name} ya existe en {dev_name}", f"add_interface {dev_name} {iface_name}")
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
            self.error_log.log_error("DeviceNotFound", f"Dispositivo {device_name} no encontrado", f"console {device_name}")
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

    def _save_snapshot(self, args):
        """Guarda un snapshot con clave"""
        if len(args) != 1:
            print("Uso: save snapshot <key>")
            return
        key = args[0]
        # Generar nombre de archivo único
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"snap_{timestamp}.json"
        try:
            save_network_config(self.network, filename)
            self.btree.insert(key, filename)
            print(f"[OK] snapshot {key} -> file: {filename} (indexed)")
        except Exception as e:
            self.error_log.log_error("SaveSnapshotError", f"Error guardando snapshot: {e}", f"save snapshot {key}")
            print(f"% Error guardando snapshot: {e}")
        print(self.get_prompt(), end='')

    def _load_config_key(self, args):
        """Carga configuración por clave"""
        if len(args) != 1:
            print("Uso: load config <key>")
            return
        key = args[0]
        filename = self.btree.search(key)
        if filename:
            try:
                self.network = load_network_config(filename)
                self.statistics = NetworkStatistics(self.network)
                devices = self.network.list_devices()
                if devices:
                    self.current_device = devices[0]
                print(f"Configuración cargada desde {filename}")
            except Exception as e:
                self.error_log.log_error("LoadConfigKeyError", f"Error cargando configuración: {e}", f"load config {key}")
                print(f"% Error cargando configuración: {e}")
        else:
            self.error_log.log_error("KeyNotFound", f"Clave {key} no encontrada en el índice", f"load config {key}")
            print(f"% Clave {key} no encontrada en el índice")
        print(self.get_prompt(), end='')

    def _show_snapshots(self, args):
        """Muestra snapshots en orden"""
        snapshots = self.btree.get_snapshots()
        if not snapshots:
            print("No snapshots")
        else:
            for key, filename in snapshots:
                print(f"{key} -> {filename}")

    def _btree_stats(self, args):
        """Muestra estadísticas del B-tree"""
        stats = self.btree.get_stats()
        print(f"order={stats['order']} height={stats['height']} nodes={stats['nodes']} splits={stats['splits']} merges={stats['merges']}")
        print(self.get_prompt(), end='')


import os

def auto_load_config(cli, filename="running-config.json"):
    """Carga configuración automáticamente si existe el archivo JSON al iniciar."""
    if os.path.exists(filename):
        try:
            cli.network = load_network_config(filename)
            cli.statistics = NetworkStatistics(cli.network)
            devices = cli.network.list_devices()
            if devices:
                cli.current_device = devices[0]
            print(f"Configuración cargada automáticamente desde {filename}")
        except Exception as e:
            print(f"% Error cargando configuración automática: {e}")

def auto_save_config(cli, filename="running-config.json"):
    """Guarda configuración automáticamente al salir del programa."""
    try:
        save_network_config(cli.network, filename)
        print(f"Configuración guardada automáticamente en {filename}")
    except Exception as e:
        print(f"% Error guardando configuración automática: {e}")

if __name__ == "__main__":
    cli = CLI()
    auto_load_config(cli)
    try:
        cli.start()
    finally:
        auto_save_config(cli)