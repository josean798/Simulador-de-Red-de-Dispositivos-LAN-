"""
Modulo 5: CLI para la simulación de red LAN
Permite la interacción con el usuario para gestionar dispositivos, interfaces y simular el envío de paquetes.
"""
import sys
from src.network import Network
from src.device import Device
from src.interface import Interface

def print_menu():
    print("""
--- Simulador de Red LAN ---
1. Agregar dispositivo
2. Eliminar dispositivo
3. Listar dispositivos
4. Conectar interfaces
5. Desconectar interfaces
6. Cambiar estado de dispositivo
7. Asignar IP a interfaz
8. Enviar paquete
9. Avanzar simulación (tick)
10. Mostrar estadísticas
0. Salir
""")

def main():
    network = Network()
    while True:
        print_menu()
        choice = input("Seleccione una opción: ").strip()
        if choice == '1':
            name = input("Nombre del dispositivo: ").strip()
            dtype = input("Tipo (router/switch/host/firewall): ").strip()
            device = Device(name, dtype)
            n = int(input("¿Cuántas interfaces agregar?: "))
            for i in range(n):
                iname = input(f"Nombre de la interfaz #{i+1}: ").strip()
                iface = Interface(iname)
                device.add_interface(iface)
            network.add_device(device)
            print(f"Dispositivo {name} agregado.")
        elif choice == '2':
            name = input("Nombre del dispositivo a eliminar: ").strip()
            device = network.get_device(name)
            if device:
                network.remove_device(device)
                print(f"Dispositivo {name} eliminado.")
            else:
                print("No encontrado.")
        elif choice == '3':
            for d in network.list_devices():
                print(d)
                for iface in d.get_interfaces():
                    print(f"  - {iface}")
        elif choice == '4':
            d1 = input("Dispositivo 1: ").strip()
            i1 = input("Interfaz 1: ").strip()
            d2 = input("Dispositivo 2: ").strip()
            i2 = input("Interfaz 2: ").strip()
            if network.connect(d1, i1, d2, i2):
                print("Interfaces conectadas.")
            else:
                print("Error en la conexión.")
        elif choice == '5':
            d1 = input("Dispositivo 1: ").strip()
            i1 = input("Interfaz 1: ").strip()
            d2 = input("Dispositivo 2: ").strip()
            i2 = input("Interfaz 2: ").strip()
            if network.disconnect(d1, i1, d2, i2):
                print("Interfaces desconectadas.")
            else:
                print("Error en la desconexión.")
        elif choice == '6':
            name = input("Nombre del dispositivo: ").strip()
            status = input("Estado (up/down): ").strip()
            if network.set_device_status(name, status):
                print("Estado actualizado.")
            else:
                print("No encontrado o estado inválido.")
        elif choice == '7':
            dname = input("Nombre del dispositivo: ").strip()
            iname = input("Nombre de la interfaz: ").strip()
            ip = input("IP a asignar: ").strip()
            device = network.get_device(dname)
            if device:
                iface = next((i for i in device.interfaces if i.name == iname), None)
                if iface:
                    iface.set_ip(ip)
                    print("IP asignada.")
                else:
                    print("Interfaz no encontrada.")
            else:
                print("Dispositivo no encontrado.")
        elif choice == '8':
            src = input("IP origen: ").strip()
            dst = input("IP destino: ").strip()
            msg = input("Mensaje: ").strip()
            ttl = input("TTL (opcional, default 5): ").strip()
            ttl = int(ttl) if ttl else 5
            if network.send_packet(src, dst, msg, ttl):
                print("Paquete encolado.")
            else:
                print("No se encontró la interfaz de origen.")
        elif choice == '9':
            network.tick()
            print("Simulación avanzada un paso.")
        elif choice == '10':
            print(network.show_statistics())
        elif choice == '0':
            print("Saliendo...")
            sys.exit(0)
        else:
            print("Opción inválida.")

if __name__ == "__main__":
    main()
