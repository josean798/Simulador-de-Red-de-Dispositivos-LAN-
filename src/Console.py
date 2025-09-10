import json
from Mode import Mode
from network import Network
from device import Device
from interface import Interface
from packet import Packet
from network_statistics import NetworkStatistics
from network_persistence import save_network_config, load_network_config
from avl_route_table import AVLRouteTable
from btree_index import BTreeIndex
from prefix_trie import PrefixTrie
from error_log import ErrorLog # Importar ErrorLog

class CLI:
    """
    Interfaz de línea de comandos mejorada para el simulador de red
    Incluye integración de módulos de estadísticas y persistencia.
    """
    
    def __init__(self):
        # Inicializar las nuevas estructuras de datos
        self.route_table = AVLRouteTable() # Esta es una tabla de rutas global para el CLI, no por dispositivo
        self.btree_index = BTreeIndex(order=4)
        self.prefix_trie = PrefixTrie() # Este es un trie global para el CLI, no por dispositivo
        self.error_log = ErrorLog() # Instancia global para el registro de errores

        # La red ahora recibe la instancia de error_log
        self.network = Network(self.error_log)
        self.statistics = NetworkStatistics(self.network)
        
        # Dispositivo actual y interfaz actual
        self.current_device = Device("HostRouter", "host")  # Dispositivo temporal
        self.current_interface = None
        
        self.init_commands()

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
    
    def init_commands(self):
        """Inicializa todos los comandos disponibles organizados por modo"""
        self.commands = {
            Mode.USER: {
                'enable': self._enable,
                'ping': self._ping,
                'send': self._send_packet,
                'show': self._show_user,
                'help': self._show_help,
                'console': self._console_device, # Mover console a modo USER para facilitar el cambio de contexto
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
                'add_device': self._add_device, # Comandos de gestión de dispositivos
                'remove_device': self._remove_device,
                'add_interface': self._add_interface,
                # Comandos de los módulos del Proyecto 2
                'ip': self._ip_route_cmd, # Para ip route add/del
                'policy': self._policy_cmd, # Para policy set/unset
                'btree': self._btree_cmd, # Para btree stats
                'save_snapshot': self._save_snapshot_cmd, # Para save snapshot
                'load_config': self._load_config_cmd, # Para load config (desde btree)
                'show_error_log': self._show_error_log_cmd # Para show error-log
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
        # Subcomandos válidos para show (para el parser)
        self.SHOW_COMMANDS = [
            'show history',
            'show interfaces',
            'show queue',
            'show statistics',
            'show ip route',
            'show route avl-stats',
            'show ip route-tree',
            'show snapshots',
            'show ip prefix-tree',
            'show error-log' # Añadir al parser de show
        ]

    def parse_command(self, command):
        """Procesa un comando ingresado por el usuario"""
        if not command.strip():
            print(self.get_prompt(), end='')
            return

        parts = command.strip().split()
        cmd = parts[0].lower()
        args = parts[1:]

        # Manejo de comandos compuestos y específicos de módulos
        full_command = command.strip()

        if full_command.startswith('configure terminal'):
            cmd = 'configure'
            args = ['terminal']
        elif full_command.startswith('no shutdown'):
            cmd = 'no'
            args = ['shutdown']
        elif full_command.startswith('show'):
            # Manejar todos los subcomandos de show
            for scmd in self.SHOW_COMMANDS:
                if full_command.startswith(scmd):
                    cmd = 'show'
                    args = full_command[len('show '):].split()
                    break
            else: # Si no coincide con ningún show conocido
                self.error_log.log_error(
                    "SyntaxError",
                    f"Comando 'show {full_command[len('show '):]}' no reconocido.",
                    command
                )
                print(f"% Comando '{full_command}' no reconocido o no disponible en el modo actual")
                return
        elif full_command.startswith('ip route'):
            cmd = 'ip'
            args = full_command[len('ip '):].split()
        elif full_command.startswith('policy'):
            cmd = 'policy'
            args = full_command[len('policy '):].split()
        elif full_command.startswith('btree'):
            cmd = 'btree'
            args = full_command[len('btree '):].split()
        elif full_command.startswith('save snapshot'):
            cmd = 'save_snapshot'
            args = full_command[len('save '):].split()
        elif full_command.startswith('load config'):
            cmd = 'load'
            args = full_command[len('load '):].split()
        elif full_command.startswith('console'):
            cmd = 'console'
            args = full_command[len('console '):].split()
        elif full_command.startswith('show error-log'): # Comando específico para el log de errores
            cmd = 'show_error_log'
            args = full_command[len('show error-log '):].split() if len(full_command) > len('show error-log ') else []
        
        # Ejecutar el comando
        if cmd in self.commands[self.current_device.mode]:
            try:
                self.commands[self.current_device.mode][cmd](args)
            except Exception as e:
                self.error_log.log_error(
                    "RuntimeError",
                    f"Error ejecutando comando '{cmd}': {e}",
                    command
                )
                print(f"Error ejecutando comando: {e}")
        else:
            self.error_log.log_error(
                "CommandError",
                f"Comando '{cmd}' no reconocido o no disponible en el modo actual.",
                command
            )
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
    
    # Módulo 1: AVL Route Table
    def _ip_route_cmd(self, args):
        if not args:
            print("Uso: ip route <add|del> ...")
            self.error_log.log_error("SyntaxError", "Uso incorrecto de 'ip route'.", "ip route")
            return
        
        subcmd = args[0]
        if subcmd == 'add':
            if len(args) >= 5 and args[3].lower() == 'via':
                prefix, mask, _, next_hop = args[1:5]
                metric = 10 # Valor por defecto
                if len(args) > 5 and args[5].lower() == 'metric' and len(args) > 6 and args[6].isdigit():
                    metric = int(args[6])
                
                # Añadir la ruta a la tabla AVL del dispositivo actual
                self.current_device.route_table.add_route(prefix, mask, next_hop, metric)
                print(f"Ruta agregada: {prefix}/{mask} via {next_hop} metric {metric}")
            else:
                print("Uso: ip route add <prefix> <mask> via <next-hop> [metric N]")
                self.error_log.log_error("SyntaxError", "Sintaxis incorrecta para 'ip route add'.", " ".join(['ip'] + args))
        elif subcmd == 'del':
            if len(args) >= 3:
                prefix, mask = args[1:3]
                # Eliminar la ruta de la tabla AVL del dispositivo actual
                self.current_device.route_table.del_route(prefix, mask)
                print(f"Ruta eliminada: {prefix}/{mask}")
            else:
                print("Uso: ip route del <prefix> <mask>")
                self.error_log.log_error("SyntaxError", "Sintaxis incorrecta para 'ip route del'.", " ".join(['ip'] + args))
        else:
            print("Uso: ip route add <prefix> <mask> via <next-hop> [metric N] | ip route del <prefix> <mask>")
            self.error_log.log_error("SyntaxError", f"Subcomando '{subcmd}' no reconocido para 'ip route'.", " ".join(['ip'] + args))
        print(self.get_prompt(), end='')

    def _show_privileged(self, args):
        if not args:
            print("Comandos show disponibles:")
            print("  show history - Muestra historial de paquetes")
            print("  show interfaces - Muestra interfaces del dispositivo")
            print("  show queue - Muestra cola de paquetes pendientes")
            print("  show statistics - Muestra estadísticas de red")
            print("  show ip route - Muestra tabla de rutas AVL")
            print("  show route avl-stats - Estadísticas AVL")
            print("  show ip route-tree - Diagrama AVL")
            print("  show snapshots - Snapshots B-tree")
            print("  show ip prefix-tree - Trie de prefijos")
            print("  show error-log [n] - Registro de errores")
            return
        
        subcmd = ' '.join(args).lower() # Unir todos los argumentos para comparar con SHOW_COMMANDS
        
        if subcmd == 'history':
            self._show_history()
        elif subcmd == 'interfaces':
            self._show_interfaces()
        elif subcmd == 'queue':
            self._show_queue()
        elif subcmd == 'statistics':
            self._show_statistics(args[1:] if len(args) > 1 else []) # Pasar solo los args adicionales
        elif subcmd == 'ip route':
            for r in self.current_device.route_table.show_routes():
                print(r)
        elif subcmd == 'route avl-stats':
            stats = self.current_device.route_table.show_stats()
            print(f"nodes={stats['nodes']} height={stats['height']} rotations: LL={stats['rotations']['LL']} LR={stats['rotations']['LR']} RL={stats['rotations']['RL']} RR={stats['rotations']['RR']}")
        elif subcmd == 'ip route-tree':
            print(self.current_device.route_table.show_tree())
        elif subcmd == 'snapshots':
            snapshots = self.btree_index.inorder()
            if snapshots:
                for k, v in snapshots:
                    print(f"{k} -> {v}")
            else:
                print("No hay snapshots guardados.")
        elif subcmd == 'ip prefix-tree':
            print(self.current_device.prefix_trie.show_tree())
        elif subcmd.startswith('error-log'): # Ya manejado por _show_error_log_cmd
            # Este caso ya debería ser capturado por el parser y redirigido a _show_error_log_cmd
            # Pero si llega aquí, es un error de lógica del parser o un uso directo incorrecto.
            n = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
            self._show_error_log_cmd([str(n)] if n is not None else [])
        else:
            print("% Comando show no reconocido")
            self.error_log.log_error("SyntaxError", f"Comando 'show {subcmd}' no reconocido.", " ".join(['show'] + args))
        print(self.get_prompt(), end='')

    # Módulo 2: B-tree Index
    def _save_snapshot_cmd(self, args):
        if len(args) < 2 or args[0].lower() != 'snapshot':
            print("Uso: save snapshot <key>")
            self.error_log.log_error("SyntaxError", "Sintaxis incorrecta para 'save snapshot'.", " ".join(['save'] + args))
            return
        key = args[1]
        filename = f"snap_{key}.json" # Usar .json para consistencia con persistencia
        
        # Guardar la configuración actual de la red en el archivo
        try:
            save_network_config(self.network, filename)
            self.btree_index.insert(key, filename)
            print(f"[OK] snapshot {key} -> file: {filename} (indexed)")
        except Exception as e:
            self.error_log.log_error(
                "PersistenceError",
                f"Error al guardar snapshot '{key}': {e}",
                " ".join(['save'] + args)
            )
            print(f"% Error al guardar snapshot: {e}")
        print(self.get_prompt(), end='')

    def _load_config_cmd(self, args):
        if len(args) < 2 or args[0].lower() != 'config':
            print("Uso: load config <key>")
            self.error_log.log_error("SyntaxError", "Sintaxis incorrecta para 'load config'.", " ".join(['load'] + args))
            return
        key = args[1]
        filename = self.btree_index.search(key)
        if filename:
            try:
                # Cargar la configuración real de la red desde el archivo
                self.network = load_network_config(filename, self.error_log)
                self.statistics = NetworkStatistics(self.network) # Actualizar estadísticas con la nueva red
                # Asegurarse de que el current_device apunte a un dispositivo válido en la nueva red
                devices = self.network.list_devices()
                if devices:
                    self.current_device = devices[0]
                else:
                    self.current_device = Device("HostRouter", "host") # Reset si no hay dispositivos
                print(f"Configuración cargada desde {filename}")
            except Exception as e:
                self.error_log.log_error(
                    "PersistenceError",
                    f"Error al cargar configuración desde '{filename}' (clave '{key}'): {e}",
                    " ".join(['load'] + args)
                )
                print(f"% Error al cargar configuración: {e}")
        else:
            print(f"% No se encontró snapshot para clave {key}")
            self.error_log.log_error(
                "NotFoundError",
                f"No se encontró snapshot para clave '{key}'.",
                " ".join(['load'] + args)
            )
        print(self.get_prompt(), end='')

    def _btree_cmd(self, args):
        if args and args[0].lower() == 'stats':
            stats = self.btree_index.show_stats()
            print(f"order={stats['order']} height={stats['height']} nodes={stats['nodes']} splits={stats['splits']} merges={stats['merges']}")
        else:
            print("Uso: btree stats")
            self.error_log.log_error("SyntaxError", "Sintaxis incorrecta para 'btree'.", " ".join(['btree'] + args))
        print(self.get_prompt(), end='')

    # Módulo 3: Prefix Trie
    def _policy_cmd(self, args):
        if not args or len(args) < 3:
            print("Uso: policy set <prefix> <mask> <ttl-min N|block> | policy unset <prefix> <mask>")
            self.error_log.log_error("SyntaxError", "Sintaxis incorrecta para 'policy'.", " ".join(['policy'] + args))
            return
        
        subcmd = args[0].lower()
        prefix, mask = args[1], args[2]

        # Validar formato IP/máscara básico
        if not (self._validate_ip(prefix) and self._validate_ip(mask)):
            print("% Prefijo o máscara IP inválida.")
            self.error_log.log_error("ValidationError", "Prefijo o máscara IP inválida en comando 'policy'.", " ".join(['policy'] + args))
            return

        if subcmd == 'set':
            if len(args) >= 4:
                policy_type = args[3].lower()
                if policy_type == 'ttl-min':
                    if len(args) > 4 and args[4].isdigit():
                        value = int(args[4])
                        self.current_device.prefix_trie.set_policy(prefix, mask, 'ttl-min', value)
                        print(f"Política ttl-min={value} aplicada a {prefix}/{mask}")
                    else:
                        print("Uso: policy set <prefix> <mask> ttl-min <N>")
                        self.error_log.log_error("SyntaxError", "Sintaxis incorrecta para 'policy set ttl-min'.", " ".join(['policy'] + args))
                elif policy_type == 'block':
                    self.current_device.prefix_trie.set_policy(prefix, mask, 'block')
                    print(f"Política block aplicada a {prefix}/{mask}")
                else:
                    print("Uso: policy set <prefix> <mask> ttl-min <N>|block")
                    self.error_log.log_error("SyntaxError", f"Tipo de política '{policy_type}' no reconocido.", " ".join(['policy'] + args))
            else:
                print("Uso: policy set <prefix> <mask> ttl-min <N>|block")
                self.error_log.log_error("SyntaxError", "Faltan argumentos para 'policy set'.", " ".join(['policy'] + args))
        elif subcmd == 'unset':
            self.current_device.prefix_trie.unset_policy(prefix, mask)
            print(f"Política eliminada de {prefix}/{mask}")
        else:
            print("Uso: policy set <prefix> <mask> ttl-min <N>|block | policy unset <prefix> <mask>")
            self.error_log.log_error("SyntaxError", f"Subcomando '{subcmd}' no reconocido para 'policy'.", " ".join(['policy'] + args))
        print(self.get_prompt(), end='')

    # Módulo 4: Error Log
    def _show_error_log_cmd(self, args):
        n = None
        if args and args[0].isdigit():
            n = int(args[0])
        
        errors = self.error_log.show_log(n)
        if errors:
            print("Registro de Errores:")
            for i, e in enumerate(errors):
                cmd_info = f" (Comando: '{e['command']}')" if e['command'] else ""
                print(f"{i+1}) [{e['timestamp']}] {e['type']}: {e['message']}{cmd_info}")
        else:
            print("El registro de errores está vacío.")
        print(self.get_prompt(), end='')
        
    # Implementación de comandos existentes (con adición de error_log)
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
            self.error_log.log_error("SyntaxError", "Sintaxis incorrecta para 'interface'.", " ".join(['interface'] + args))
            return
            
        iface_name = args[0]
        iface = next((i for i in self.current_device.get_interfaces() if i.name == iface_name), None)
        
        if iface:
            self.current_interface = iface
            self.current_device.mode = Mode.CONFIG_IF
        else:
            print(f"% La interfaz {iface_name} no existe en {self.current_device.name}")
            self.error_log.log_error(
                "ConfigurationError",
                f"La interfaz '{iface_name}' no existe en el dispositivo '{self.current_device.name}'.",
                " ".join(['interface'] + args)
            )
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
            self.error_log.log_error("SyntaxError", "Sintaxis incorrecta para 'hostname'.", " ".join(['hostname'] + args))
            return
            
        new_name = args[0]
        # Verificar si el nuevo nombre ya está en uso por otro dispositivo en la red
        existing_device = self.network.get_device(new_name)
        if existing_device and existing_device != self.current_device:
            print(f"% El nombre {new_name} ya está en uso por otro dispositivo.")
            self.error_log.log_error(
                "ConfigurationError",
                f"El nombre de host '{new_name}' ya está en uso.",
                " ".join(['hostname'] + args)
            )
        else:
            old_name = self.current_device.name
            self.current_device.name = new_name
            # Actualizar el nombre en el diccionario de actividad de la red
            if old_name in self.network.device_activity:
                self.network.device_activity[new_name] = self.network.device_activity.pop(old_name)
            print(f"Nombre del dispositivo cambiado a {new_name}")
        print(self.get_prompt(), end='')

    def _set_ip_address(self, args):
        """Configura dirección IP de la interfaz actual"""
        if len(args) < 2 or args[0].lower() != 'address':
            print("Uso: ip address <dirección_ip>")
            self.error_log.log_error("SyntaxError", "Sintaxis incorrecta para 'ip address'.", " ".join(['ip'] + args))
            return
            
        ip = args[1]
        if self.current_interface:
            if self._validate_ip(ip):
                self.current_interface.set_ip(ip)
                print(f"Interface {self.current_interface.name} configurada con IP {ip}")
            else:
                print("% Dirección IP inválida")
                self.error_log.log_error(
                    "ValidationError",
                    f"Dirección IP '{ip}' inválida para la interfaz '{self.current_interface.name}'.",
                    " ".join(['ip'] + args)
                )
        else:
            print("% Ninguna interfaz seleccionada. Use 'interface <nombre>' primero.")
            self.error_log.log_error(
                "ConfigurationError",
                "Intento de configurar IP sin interfaz seleccionada.",
                " ".join(['ip'] + args)
            )
        print(self.get_prompt(), end='')

    def _validate_ip(self, ip):
        """Valida formato básico de dirección IP"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        for part in parts:
            if not part.isdigit():
                return False
            num = int(part)
            if not (0 <= num <= 255):
                return False
        return True

    def _shutdown_interface(self, args):
        """Desactiva la interfaz actual"""
        if self.current_interface:
            self.current_interface.shutdown()
            print(f"Interface {self.current_interface.name} desactivada")
        else:
            print("% Ninguna interfaz seleccionada.")
            self.error_log.log_error(
                "ConfigurationError",
                "Intento de 'shutdown' sin interfaz seleccionada.",
                "shutdown"
            )
        print(self.get_prompt(), end='')

    def _no_shutdown(self, args):
        """Activa la interfaz actual"""
        if self.current_interface:
            self.current_interface.no_shutdown()
            print(f"Interface {self.current_interface.name} activada")
        else:
            print("% Ninguna interfaz seleccionada.")
            self.error_log.log_error(
                "ConfigurationError",
                "Intento de 'no shutdown' sin interfaz seleccionada.",
                "no shutdown"
            )
        print(self.get_prompt(), end='')

    def _connect(self, args):
        """Conecta dos interfaces de dispositivos"""
        if len(args) != 3:
            print("Uso: connect <interfaz_local> <dispositivo_remoto> <interfaz_remota>")
            self.error_log.log_error("SyntaxError", "Sintaxis incorrecta para 'connect'.", " ".join(['connect'] + args))
            return
            
        iface1, dev2_name, iface2 = args
        dev1_name = self.current_device.name
        
        if self.network.connect(dev1_name, iface1, dev2_name, iface2):
            print(f"Conexión establecida: {dev1_name}:{iface1} <-> {dev2_name}:{iface2}")
        else:
            print("% No se pudo establecer la conexión. Verifique los nombres de dispositivos e interfaces, y que no estén ya conectadas.")
            self.error_log.log_error(
                "ConnectionError",
                f"Fallo al conectar {dev1_name}:{iface1} con {dev2_name}:{iface2}.",
                " ".join(['connect'] + args)
            )
        print(self.get_prompt(), end='')

    def _disconnect(self, args):
        """Desconecta dos interfaces"""
        if len(args) != 3:
            print("Uso: disconnect <interfaz_local> <dispositivo_remoto> <interfaz_remota>")
            self.error_log.log_error("SyntaxError", "Sintaxis incorrecta para 'disconnect'.", " ".join(['disconnect'] + args))
            return
            
        iface1, dev2_name, iface2 = args
        dev1_name = self.current_device.name
        
        if self.network.disconnect(dev1_name, iface1, dev2_name, iface2):
            print(f"Conexión eliminada: {dev1_name}:{iface1} <-> {dev2_name}:{iface2}")
        else:
            print("% No se pudo eliminar la conexión. Verifique los nombres de dispositivos e interfaces.")
            self.error_log.log_error(
                "ConnectionError",
                f"Fallo al desconectar {dev1_name}:{iface1} de {dev2_name}:{iface2}.",
                " ".join(['disconnect'] + args)
            )
        print(self.get_prompt(), end='')

    def _set_device_status(self, args):
        """Configura estado de un dispositivo (online/offline)"""
        if len(args) != 2:
            print("Uso: set_device_status <dispositivo> <online|offline>")
            self.error_log.log_error("SyntaxError", "Sintaxis incorrecta para 'set_device_status'.", " ".join(['set_device_status'] + args))
            return
            
        dev_name, status = args
        if status.lower() in ['online', 'offline']:
            if self.network.set_device_status(dev_name, 'up' if status.lower() == 'online' else 'down'):
                print(f"Estado de {dev_name} cambiado a {status.lower()}")
            else:
                print(f"% Dispositivo {dev_name} no encontrado.")
                self.error_log.log_error(
                    "NotFoundError",
                    f"Dispositivo '{dev_name}' no encontrado para cambiar estado.",
                    " ".join(['set_device_status'] + args)
                )
        else:
            print("% Estado inválido. Use 'online' u 'offline'")
            self.error_log.log_error(
                "ValidationError",
                f"Estado '{status}' inválido. Use 'online' u 'offline'.",
                " ".join(['set_device_status'] + args)
            )
        print(self.get_prompt(), end='')

    def _list_devices(self, args):
        """Lista todos los dispositivos en la red"""
        print("Dispositivos en la red:")
        devices = self.network.list_devices()
        if devices:
            for device in devices:
                status = "online" if device.status == 'up' else "offline"
                print(f"- {device.name} ({device.device_type}, {status})")
        else:
            print("  (No hay dispositivos en la red)")
        print(self.get_prompt(), end='')

    def _show_user(self, args):
        """Comandos show disponibles en modo usuario"""
        if not args:
            print("Comandos show disponibles en modo usuario:")
            print("  show interfaces - Muestra interfaces del dispositivo")
            return
            
        subcmd = args[0].lower()
        if subcmd == 'interfaces':
            self._show_interfaces()
        else:
            print("% Comando show no reconocido")
            self.error_log.log_error("SyntaxError", f"Comando 'show {subcmd}' no reconocido en modo usuario.", " ".join(['show'] + args))
        print(self.get_prompt(), end='')

    def _show_history(self):
        """
        Muestra historial de paquetes recibidos por el dispositivo actual.
        """
        received = self.current_device.get_history()

        print(f"Historial de paquetes recibidos en {self.current_device.name}:")
        if received:
            for i, packet in enumerate(received, 1):
                path = ' → '.join(packet.path.to_list()) if packet.path and packet.path.size > 0 else 'N/A'
                ttl_at_arrival = packet.ttl + 1 # TTL al llegar al destino (antes de decrementar el último hop)
                print(f"{i}) From {packet.source_ip} to {packet.destination_ip}: \"{packet.content}\" | TTL at arrival: {ttl_at_arrival} | Path: {path}")
        else:
            print("  (Ningún paquete recibido)")
        
    def _show_interfaces(self):
        """Muestra estado de las interfaces"""
        print(f"Interfaces de {self.current_device.name}:")
        interfaces = self.current_device.get_interfaces()
        if interfaces:
            for iface in interfaces:
                status = "up" if iface.status == 'up' else "down"
                ip = iface.ip_address if iface.ip_address else "no asignada"
                neighbors_list = iface.neighbors.to_list()
                neighbors_info = ', '.join([n.name for n in neighbors_list]) if neighbors_list else "ninguno"
                print(f"- {iface.name}: IP {ip}, estado {status}, vecinos: {neighbors_info}")
        else:
            print("  (No hay interfaces configuradas)")

    def _show_queue(self):
        """Muestra paquetes en cola"""
        print(f"Paquetes en cola de {self.current_device.name}:")
        queue_packets = self.current_device.get_queue()
        if queue_packets:
            for i, packet in enumerate(queue_packets, 1):
                print(f"{i}) De {packet.source_ip} a {packet.destination_ip}: \"{packet.content}\" (TTL: {packet.ttl})")
        else:
            print("  (Cola vacía)")

    def _show_statistics(self, args):
        """
        Muestra estadísticas de red y permite exportarlas si se indica un archivo.
        Uso: show statistics [export <archivo>]
        """
        if args and args[0].lower() == 'export':
            if len(args) > 1:
                filename = args[1]
                self.statistics.export_statistics(filename)
            else:
                print("Uso: show statistics export <archivo>")
                self.error_log.log_error("SyntaxError", "Falta nombre de archivo para 'show statistics export'.", " ".join(['show statistics'] + args))
        else:
            self.statistics.show_statistics()
        
    def _send_packet(self, args):
        """Envía un paquete (simulado) y registra en historial de emisor y receptor"""
        if len(args) < 3:
            print("Uso: send <ip_origen> <ip_destino> <mensaje> [ttl]")
            self.error_log.log_error("SyntaxError", "Sintaxis incorrecta para 'send'.", " ".join(['send'] + args))
            return

        source_ip = args[0]
        destination_ip = args[1]
        
        # Reconstruir el mensaje, que puede contener espacios
        message_parts = []
        ttl_str = None
        
        # Buscar el TTL al final
        if args[-1].isdigit():
            ttl_str = args[-1]
            message_parts = args[2:-1]
        else:
            message_parts = args[2:]
        
        message = ' '.join(message_parts)
        ttl = int(ttl_str) if ttl_str else 5

        # Validar IPs
        if not self._validate_ip(source_ip) or not self._validate_ip(destination_ip):
            print("% Dirección IP de origen o destino inválida.")
            self.error_log.log_error(
                "ValidationError",
                f"IP de origen '{source_ip}' o destino '{destination_ip}' inválida.",
                " ".join(['send'] + args)
            )
            return

        # Enviar el paquete usando la lógica de red
        sent = self.network.send_packet(source_ip, destination_ip, message, ttl)
        if sent:
            print(f"Mensaje en cola para entrega: '{message}' de {source_ip} a {destination_ip} (TTL={ttl})")
        else:
            # El error ya se registra en network.send_packet
            pass # Mensaje de error ya impreso por network.send_packet
        print(self.get_prompt(), end='')

    def _ping(self, args):
        """Simula comando ping"""
        if len(args) != 1:
            print("Uso: ping <ip_destino>")
            self.error_log.log_error("SyntaxError", "Sintaxis incorrecta para 'ping'.", " ".join(['ping'] + args))
            return
        
        dest_ip = args[0]
        if not self._validate_ip(dest_ip):
            print("% Dirección IP de destino inválida.")
            self.error_log.log_error(
                "ValidationError",
                f"Dirección IP de destino '{dest_ip}' inválida para ping.",
                " ".join(['ping'] + args)
            )
            return
            
        print(f"Enviando ping a {dest_ip}... (simulado)")
        print(self.get_prompt(), end='')

    def _process_tick(self, args):
        """Procesa un paso de simulación"""
        self.network.tick()
        print("Paso de simulación completado")
        print(self.get_prompt(), end='')

    def _save_config(self, args):
        """
        Guarda configuración actual a archivo usando el módulo de persistencia.
        Uso: save running-config [archivo]
        """
        if not args or args[0].lower() != 'running-config':
            print("Uso: save running-config [archivo]")
            self.error_log.log_error("SyntaxError", "Sintaxis incorrecta para 'save'.", " ".join(['save'] + args))
            return
        
        filename = args[1] if len(args) > 1 else 'running-config.json'
        try:
            save_network_config(self.network, filename)
        except Exception as e:
            self.error_log.log_error(
                "PersistenceError",
                f"Error guardando configuración en '{filename}': {e}",
                " ".join(['save'] + args)
            )
            print(f"% Error guardando configuración: {e}")
        print(self.get_prompt(), end='')

    def _load_config(self, args):
        """
        Carga configuración desde archivo usando el módulo de persistencia.
        Uso: load config <archivo>
        """
        if not args or args[0].lower() != 'config' or len(args) < 2:
            print("Uso: load config <archivo>")
            self.error_log.log_error("SyntaxError", "Sintaxis incorrecta para 'load'.", " ".join(['load'] + args))
            return
        filename = args[1]
        try:
            self.network = load_network_config(filename, self.error_log)
            self.statistics = NetworkStatistics(self.network)
            # Asegurarse de que el current_device apunte a un dispositivo válido en la nueva red
            devices = self.network.list_devices()
            if devices:
                self.current_device = devices[0]
            else:
                self.current_device = Device("HostRouter", "host") # Reset si no hay dispositivos
            print(f"Configuración cargada desde {filename}")
        except FileNotFoundError:
            print(f"% Archivo '{filename}' no encontrado.")
            self.error_log.log_error(
                "FileNotFoundError",
                f"Archivo de configuración '{filename}' no encontrado.",
                " ".join(['load'] + args)
            )
        except Exception as e:
            print(f"% Error cargando configuración: {e}")
            self.error_log.log_error(
                "PersistenceError",
                f"Error cargando configuración desde '{filename}': {e}",
                " ".join(['load'] + args)
            )
        print(self.get_prompt(), end='')

    def _show_help(self, args):
        """Muestra ayuda para los comandos disponibles"""
        print("Comandos disponibles en el modo actual:")
        for cmd, func in self.commands[self.current_device.mode].items():
            # Evitar mostrar comandos internos o alias
            if cmd not in ['help', 'exit', 'end', 'configure', 'no', 'ip', 'policy', 'btree', 'save_snapshot', 'load_config', 'show_error_log']:
                print(f"- {cmd}")
        # Mostrar comandos especiales que se parsean
        if self.current_device.mode == Mode.PRIVILEGED:
            print("- configure terminal")
            print("- save running-config [file]")
            print("- load config <file>")
            print("- ip route add/del ...")
            print("- policy set/unset ...")
            print("- btree stats")
            print("- save snapshot <key>")
            print("- load config <key> (desde btree)")
            print("- show error-log [n]")
        elif self.current_device.mode == Mode.CONFIG_IF:
            print("- ip address <ip>")
            print("- no shutdown")
        print(self.get_prompt(), end='')

    def _add_device(self, args):
        """Añade un nuevo dispositivo a la red"""
        if len(args) != 2:
            print("Uso: add_device <nombre> <tipo>")
            print("Tipos válidos: router, switch, host, firewall")
            self.error_log.log_error("SyntaxError", "Sintaxis incorrecta para 'add_device'.", " ".join(['add_device'] + args))
            return
    
        name, dtype = args[0], args[1].lower()
        
        if dtype not in ['router', 'switch', 'host', 'firewall']:
            print("% Tipo de dispositivo inválido")
            self.error_log.log_error("ValidationError", f"Tipo de dispositivo '{dtype}' inválido.", " ".join(['add_device'] + args))
            return
            
        if self.network.get_device(name):
            print(f"% El dispositivo {name} ya existe")
            self.error_log.log_error("ConfigurationError", f"El dispositivo '{name}' ya existe.", " ".join(['add_device'] + args))
            return
            
        device = Device(name, dtype)
        self.network.add_device(device)
        print(f"Dispositivo {name} ({dtype}) añadido")
        print(self.get_prompt(), end='')

    def _remove_device(self, args):
        """Elimina un dispositivo de la red"""
        if len(args) != 1:
            print("Uso: remove_device <nombre>")
            self.error_log.log_error("SyntaxError", "Sintaxis incorrecta para 'remove_device'.", " ".join(['remove_device'] + args))
            return
        
        name = args[0]
        device = self.network.get_device(name)
        
        if not device:
            print(f"% Dispositivo {name} no encontrado")
            self.error_log.log_error("NotFoundError", f"Dispositivo '{name}' no encontrado para eliminar.", " ".join(['remove_device'] + args))
            return
            
        # Verificar conexiones primero (la lógica de remove_device en Network ya maneja esto)
        if self.network.remove_device(device):
            print(f"Dispositivo {name} eliminado")
            # Si el dispositivo eliminado era el current_device, cambiar a un dispositivo temporal
            if self.current_device == device:
                devices_in_network = self.network.list_devices()
                if devices_in_network:
                    self.current_device = devices_in_network[0]
                else:
                    self.current_device = Device("HostRouter", "host") # Dispositivo temporal si no quedan más
        else:
            print(f"% No se pudo eliminar el dispositivo {name}. Asegúrese de que no tenga conexiones activas.")
            self.error_log.log_error(
                "ConfigurationError",
                f"Fallo al eliminar el dispositivo '{name}'. Puede tener conexiones activas.",
                " ".join(['remove_device'] + args)
            )
        print(self.get_prompt(), end='')

    def _add_interface(self, args):
        """Añade una interfaz a un dispositivo"""
        if len(args) != 2:
            print("Uso: add_interface <dispositivo> <nombre_interfaz>")
            self.error_log.log_error("SyntaxError", "Sintaxis incorrecta para 'add_interface'.", " ".join(['add_interface'] + args))
            return
        
        dev_name, iface_name = args[0], args[1]
        device = self.network.get_device(dev_name)
        
        if not device:
            print(f"% Dispositivo {dev_name} no encontrado")
            self.error_log.log_error("NotFoundError", f"Dispositivo '{dev_name}' no encontrado para añadir interfaz.", " ".join(['add_interface'] + args))
            return
            
        # Verificar si la interfaz ya existe
        if any(iface.name == iface_name for iface in device.get_interfaces()):
            print(f"% La interfaz {iface_name} ya existe en {dev_name}")
            self.error_log.log_error(
                "ConfigurationError",
                f"La interfaz '{iface_name}' ya existe en el dispositivo '{dev_name}'.",
                " ".join(['add_interface'] + args)
            )
            return
            
        iface = Interface(iface_name)
        device.add_interface(iface)
        print(f"Interfaz {iface_name} añadida a {dev_name}")
        print(self.get_prompt(), end='')

    def _console_device(self, args):
        if not args:
            print("Dispositivos disponibles:")
            devices = self.network.list_devices()
            if devices:
                for device in devices:
                    print(f"- {device.name} ({device.device_type})")
            else:
                print("  (No hay dispositivos en la red)")
            print(self.get_prompt(), end='')
            return
        """Cambia al contexto de otro dispositivo"""
        if len(args) != 1:
            print("Uso: console <nombre_dispositivo>")
            self.error_log.log_error("SyntaxError", "Sintaxis incorrecta para 'console'.", " ".join(['console'] + args))
            return
        
        device_name = args[0]
        device = self.network.get_device(device_name)
        
        if not device:
            print(f"% Dispositivo {device_name} no encontrado")
            self.error_log.log_error("NotFoundError", f"Dispositivo '{device_name}' no encontrado para cambiar contexto.", " ".join(['console'] + args))
            return
        
        # Guardar el modo actual del dispositivo anterior antes de cambiar
        # No es necesario si cada dispositivo tiene su propio modo, pero el CLI gestiona un current_device
        # y su modo. Al cambiar current_device, el modo se mantiene.
        # Si se quisiera que cada dispositivo "recordara" su último modo, la lógica sería diferente.
        
        self.current_device = device
        # El modo del CLI se mantiene, pero el prompt reflejará el nuevo dispositivo
        print(f"Cambiado al dispositivo {device_name}")
        print(self.get_prompt(), end='')


import os

def auto_load_config(cli, filename="running-config.json"):
    """Carga configuración automáticamente si existe el archivo JSON al iniciar."""
    if os.path.exists(filename):
        try:
            # Usar la función load_network_config que ya actualiza la red y estadísticas
            cli.network = load_network_config(filename, cli.error_log)
            cli.statistics = NetworkStatistics(cli.network)
            devices = cli.network.list_devices()
            if devices:
                cli.current_device = devices[0]
            print(f"Configuración cargada automáticamente desde {filename}")
        except Exception as e:
            cli.error_log.log_error(
                "StartupError",
                f"Error cargando configuración automática desde '{filename}': {e}",
                "auto_load_config"
            )
            print(f"% Error cargando configuración automática: {e}")

def auto_save_config(cli, filename="running-config.json"):
    """Guarda configuración automáticamente al salir del programa."""
    try:
        save_network_config(cli.network, filename)
        print(f"Configuración guardada automáticamente en {filename}")
    except Exception as e:
        cli.error_log.log_error(
            "ShutdownError",
            f"Error guardando configuración automática en '{filename}': {e}",
            "auto_save_config"
        )
        print(f"% Error guardando configuración automática: {e}")

if __name__ == "__main__":
    cli = CLI()
    auto_load_config(cli)
    try:
        cli.start()
    finally:
        auto_save_config(cli)
        # Opcional: Guardar el log de errores al salir
        cli.error_log.save_to_json("error_log.json")
        print("Registro de errores guardado en error_log.json")

