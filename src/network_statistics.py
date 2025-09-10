"""
Modulo 5: Estadísticas y Reportes
Este módulo proporciona funciones para recopilar y mostrar estadísticas globales de la red.
"""
import json

class NetworkStatistics:
    def __init__(self, network):
        self.network = network

    def get_statistics(self):
        total_sent = 0
        delivered = 0
        dropped_ttl = 0
        blocked_firewall = 0
        total_hops = 0
        packet_count = 0
        device_activity = {}

        for device in self.network.list_devices():
            device_activity[device.name] = 0
            for packet in device.get_history():
                total_sent += 1
                delivered += 1 if packet.ttl > 0 else 0
                dropped_ttl += 1 if packet.ttl == 0 else 0
                total_hops += len(packet.path) if hasattr(packet, 'path') else 0
                device_activity[device.name] += 1
            # You may want to count blocked_firewall if you implement firewall logic

        avg_hops = total_hops / delivered if delivered > 0 else 0
        top_talker = max(device_activity, key=device_activity.get) if device_activity else None

        stats = {
            'Total packets sent': total_sent,
            'Delivered': delivered,
            'Dropped (TTL)': dropped_ttl,
            'Blocked (Firewall)': blocked_firewall,
            'Average hops': round(avg_hops, 2),
            'Top talker': top_talker,
            'Device activity': device_activity
        }
        return stats

    def show_statistics(self):
        stats = self.get_statistics()
        print("Estadísticas de red:")
        for k, v in stats.items():
            print(f"{k}: {v}")

    def export_statistics(self, filename="network_stats.json"):
        stats = self.get_statistics()
        with open(filename, "w") as f:
            json.dump(stats, f, indent=2)
        print(f"Estadísticas exportadas a {filename}")
