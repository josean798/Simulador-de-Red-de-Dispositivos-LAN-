"""
Modulo 6: Pruebas automáticas del simulador de red LAN
Incluye pruebas unitarias para los módulos principales.
"""
import unittest
from src.device import Device
from src.interface import Interface
from src.network import Network
from src.packet import Packet

class TestDevice(unittest.TestCase):
    def test_add_interface(self):
        d = Device('R1', 'router')
        iface = Interface('g0/0')
        d.add_interface(iface)
        self.assertIn(iface, d.interfaces)
    def test_status(self):
        d = Device('H1', 'host')
        d.set_status('down')
        self.assertEqual(d.status, 'down')
        with self.assertRaises(ValueError):
            d.set_status('invalid')
    def test_packet_queue(self):
        d = Device('S1', 'switch')
        p = Packet('1.1.1.1', '2.2.2.2', 'msg')
        d.enqueue_packet(p)
        self.assertEqual(d.dequeue_packet(), p)

class TestInterface(unittest.TestCase):
    def test_ip_and_status(self):
        i = Interface('eth0')
        i.set_ip('10.0.0.1')
        self.assertEqual(i.ip_address, '10.0.0.1')
        i.shutdown()
        self.assertEqual(i.status, 'down')
        i.no_shutdown()
        self.assertEqual(i.status, 'up')
    def test_connect_disconnect(self):
        i1 = Interface('eth0')
        i2 = Interface('eth1')
        i1.connect(i2)
        self.assertIn(i2, i1.neighbors)
        i1.disconnect(i2)
        self.assertNotIn(i2, i1.neighbors)
    def test_packet_queue(self):
        i = Interface('eth0')
        p = Packet('a', 'b', 'c')
        i.enqueue_packet(p)
        self.assertEqual(i.dequeue_packet(), p)

class TestNetwork(unittest.TestCase):
    def setUp(self):
        self.net = Network()
        d1 = Device('R1', 'router')
        d2 = Device('H1', 'host')
        i1 = Interface('g0/0')
        i2 = Interface('eth0')
        d1.add_interface(i1)
        d2.add_interface(i2)
        self.net.add_device(d1)
        self.net.add_device(d2)
        i1.set_ip('10.0.0.1')
        i2.set_ip('10.0.0.2')
        i1.connect(i2)
    def test_connect_disconnect(self):
        self.assertTrue(self.net.connect('R1', 'g0/0', 'H1', 'eth0'))
        self.assertTrue(self.net.disconnect('R1', 'g0/0', 'H1', 'eth0'))
    def test_send_and_tick(self):
        sent = self.net.send_packet('10.0.0.1', '10.0.0.2', 'Hola', ttl=3)
        self.assertTrue(sent)
        self.net.tick()
        d2 = self.net.get_device('H1')
        self.assertTrue(d2.get_history())
    def test_statistics(self):
        self.net.send_packet('10.0.0.1', '10.0.0.2', 'Hola')
        self.net.tick()
        stats = self.net.show_statistics()
        self.assertIn('Total packets sent', stats)

if __name__ == "__main__":
    unittest.main()
