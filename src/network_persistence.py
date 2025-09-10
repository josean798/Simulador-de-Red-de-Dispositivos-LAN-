"""
Modulo 6: Persistencia de Configuración
Este módulo proporciona funciones para guardar y cargar la configuración de la red en archivos JSON.
"""
import json
from device import Device
from interface import Interface
from network import Network

def save_network_config(network, filename="running-config.json"):
    config = {
        'devices': [],
        'connections': []
    }
    for device in network.list_devices():
        device_data = {
            'name': device.name,
            'type': device.device_type,
            'status': device.status,
            'interfaces': []
        }
        for iface in device.get_interfaces():
            iface_data = {
                'name': iface.name,
                'ip': iface.ip_address,
                'status': iface.status
            }
            device_data['interfaces'].append(iface_data)
        config['devices'].append(device_data)
    for conn in network.connections:
        config['connections'].append(conn)
    with open(filename, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"Configuración guardada en {filename}")

def load_network_config(filename, errorlog):
    with open(filename) as f:
        config = json.load(f)
    network = Network(errorlog)
    for device_data in config['devices']:
        device = Device(device_data['name'], device_data['type'])
        device.set_status(device_data['status'])
        network.add_device(device)
        for iface_data in device_data['interfaces']:
            iface = Interface(iface_data['name'])
            if iface_data['ip']:
                iface.set_ip(iface_data['ip'])
            iface.set_status(iface_data['status'])
            device.add_interface(iface)
    for conn in config['connections']:
        network.connect(*conn)
    print(f"Configuración cargada desde {filename}")
    return network
