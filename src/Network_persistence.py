"""
Modulo 6: Persistencia de Configuración
Este módulo proporciona funciones para guardar y cargar la configuración de la red en archivos JSON.
"""
import json
from Device import Device
from Interface import Interface
from Network import Network

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
            'interfaces': [],
            'routing_table': device.get_routing_table_data(),
            'policies': device.get_policy_data()
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

def load_network_config(filename):
    with open(filename) as f:
        config = json.load(f)
    network = Network()
    for device_data in config['devices']:
        device = Device(device_data['name'], device_data['type'])
        device.set_status(device_data['status'])
        network.add_device(device)
        for iface_data in device_data['interfaces']:
            iface = Interface(iface_data['name'])
            if iface_data['ip']:
                iface.set_ip(iface_data['ip'])
            iface.status = iface_data['status']
            device.add_interface(iface)
        for route_data in device_data.get('routing_table', []):
            device.add_route(route_data['prefix'], route_data['mask'], route_data['next_hop'], route_data['metric'])
        for policy_data in device_data.get('policies', []):
            prefix, mask, policy_type, policy_value = policy_data
            device.set_policy(prefix, mask, policy_type, policy_value)
    for conn in config['connections']:
        network.connect(*conn)
    return network
