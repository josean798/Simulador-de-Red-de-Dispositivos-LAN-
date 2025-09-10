"""
Modulo 1: Tabla de Rutas Balanceada con AVL
Implementa una tabla de rutas por dispositivo usando AVL.
Cada nodo representa una ruta: prefijo, máscara, next-hop, métrica.
"""
import json
from typing import Optional, List, Dict

class AVLNode:
    def __init__(self, prefix: str, mask: str, next_hop: str, metric: int):
        self.prefix = prefix
        self.mask = mask
        self.next_hop = next_hop
        self.metric = metric
        self.left: Optional['AVLNode'] = None
        self.right: Optional['AVLNode'] = None
        self.height: int = 1

class AVLRouteTable:
    def __init__(self):
        self.root: Optional[AVLNode] = None
        self.stats = {'LL': 0, 'LR': 0, 'RL': 0, 'RR': 0}

    def add_route(self, prefix: str, mask: str, next_hop: str, metric: int):
        """Agrega una ruta al árbol AVL."""
        self.root = self._insert(self.root, prefix, mask, next_hop, metric)

    def del_route(self, prefix: str, mask: str):
        """Elimina una ruta del árbol AVL."""
        self.root = self._delete(self.root, prefix, mask)

    def lookup(self, dest_ip: str) -> Optional[AVLNode]:
        """
        Busca la mejor ruta (longest-prefix match) para la IP de destino.
        """
        best_match = None
        current_node = self.root
        
        # Convertir la IP de destino a su representación binaria para comparación
        dest_ip_bin = self._ip_to_binary(dest_ip)

        while current_node:
            prefix_bin = self._ip_to_binary(current_node.prefix)
            mask_len = sum(bin(int(x)).count('1') for x in current_node.mask.split('.'))

            # Verificar si la IP de destino coincide con el prefijo actual
            if self._ip_match(dest_ip_bin, prefix_bin, mask_len):
                # Si coincide, es un candidato. Si es más específico que el actual mejor, lo actualizamos.
                if best_match is None or \
                   sum(bin(int(x)).count('1') for x in best_match.mask.split('.')) < mask_len:
                    best_match = current_node
            
            # Decidir si ir a la izquierda o a la derecha (basado en la clave del nodo)
            # Para un LPM, la navegación del árbol es más compleja que una simple comparación de claves.
            # Aquí, simplificamos la navegación para buscar posibles coincidencias en ambos subárboles
            # o basándonos en la comparación de la IP de destino con el prefijo del nodo.
            # Una implementación más robusta de LPM en un AVL podría requerir un recorrido más exhaustivo
            # o una estructura de árbol diferente (como un Trie).
            
            # Para este AVL, la comparación de claves es (prefix, mask).
            # Si la IP de destino es "menor" que el prefijo del nodo, intentamos ir a la izquierda.
            # Si es "mayor", intentamos ir a la derecha.
            # Esto no es estrictamente un LPM, pero es una aproximación para la estructura AVL.
            
            # Una forma más simple para AVL es buscar el nodo que contiene la IP y luego
            # recorrer hacia arriba o hacia abajo para encontrar el LPM.
            # La implementación actual de _lookup es una búsqueda directa que se beneficia
            # de la estructura del árbol para encontrar una coincidencia, y luego se refina.

            # Para una búsqueda de LPM en un AVL, a menudo se recorre el árbol y se mantiene
            # el mejor prefijo encontrado hasta el momento.
            
            # La siguiente lógica es una simplificación para la navegación del AVL
            # basada en la comparación de la IP de destino con el prefijo del nodo actual.
            # No es un recorrido óptimo para LPM en todos los casos, pero es un punto de partida.
            
            # Convertir la IP de destino y el prefijo del nodo a enteros para una comparación simple
            dest_ip_int = int(''.join(f'{int(x):08b}' for x in dest_ip.split('.')), 2)
            node_prefix_int = int(''.join(f'{int(x):08b}' for x in current_node.prefix.split('.')), 2)

            if dest_ip_int < node_prefix_int:
                current_node = current_node.left
            else:
                current_node = current_node.right

        return best_match

    def _ip_to_binary(self, ip_address: str) -> str:
        """Convierte una dirección IP a su representación binaria de 32 bits."""
        octets = map(int, ip_address.split('.'))
        binary_octets = [f'{octet:08b}' for octet in octets]
        return ''.join(binary_octets)

    def _ip_match(self, ip_bin: str, prefix_bin: str, mask_len: int) -> bool:
        """
        Verifica si una IP binaria coincide con un prefijo binario dada una longitud de máscara.
        """
        return ip_bin[:mask_len] == prefix_bin[:mask_len]

    def show_routes(self) -> List[str]:
        """Devuelve la lista de rutas en orden."""
        routes = []
        self._inorder(self.root, routes)
        return routes

    def show_stats(self) -> Dict:
        """Devuelve estadísticas del árbol AVL."""
        return {
            'nodes': self._count_nodes(self.root),
            'height': self._get_height(self.root),
            'rotations': self.stats
        }

    def show_tree(self) -> str:
        """Devuelve un diagrama ASCII del árbol."""
        return self._ascii_tree(self.root)

    # Métodos internos para AVL
    def _insert(self, node, prefix, mask, next_hop, metric):
        if not node:
            return AVLNode(prefix, mask, next_hop, metric)
        
        # Comparación basada en (prefix, mask) para mantener el orden en el AVL
        # Convertir a tuplas de enteros para una comparación lexicográfica
        node_key = (tuple(map(int, node.prefix.split('.'))), tuple(map(int, node.mask.split('.'))))
        new_key = (tuple(map(int, prefix.split('.'))), tuple(map(int, mask.split('.'))))

        if new_key < node_key:
            node.left = self._insert(node.left, prefix, mask, next_hop, metric)
        elif new_key > node_key:
            node.right = self._insert(node.right, prefix, mask, next_hop, metric)
        else:
            # Si la clave ya existe, actualizar next_hop y metric
            node.next_hop = next_hop
            node.metric = metric
            return node
        
        node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))
        balance = self._get_balance(node)
        
        # Rotaciones
        if balance > 1 and new_key < (tuple(map(int, node.left.prefix.split('.'))), tuple(map(int, node.left.mask.split('.')))):
            self.stats['LL'] += 1
            return self._right_rotate(node)
        if balance < -1 and new_key > (tuple(map(int, node.right.prefix.split('.'))), tuple(map(int, node.right.mask.split('.')))):
            self.stats['RR'] += 1
            return self._left_rotate(node)
        if balance > 1 and new_key > (tuple(map(int, node.left.prefix.split('.'))), tuple(map(int, node.left.mask.split('.')))):
            self.stats['LR'] += 1
            node.left = self._left_rotate(node.left)
            return self._right_rotate(node)
        if balance < -1 and new_key < (tuple(map(int, node.right.prefix.split('.'))), tuple(map(int, node.right.mask.split('.')))):
            self.stats['RL'] += 1
            node.right = self._right_rotate(node.right)
            return self._left_rotate(node)
        return node

    def _delete(self, node, prefix, mask):
        if not node:
            return node
        
        node_key = (tuple(map(int, node.prefix.split('.'))), tuple(map(int, node.mask.split('.'))))
        del_key = (tuple(map(int, prefix.split('.'))), tuple(map(int, mask.split('.'))))

        if del_key < node_key:
            node.left = self._delete(node.left, prefix, mask)
        elif del_key > node_key:
            node.right = self._delete(node.right, prefix, mask)
        else:
            if not node.left:
                return node.right
            elif not node.right:
                return node.left
            temp = self._min_value_node(node.right)
            node.prefix, node.mask, node.next_hop, node.metric = temp.prefix, temp.mask, temp.next_hop, temp.metric
            node.right = self._delete(node.right, temp.prefix, temp.mask)
        
        if not node: # Si el nodo fue eliminado y era una hoja o tenía un solo hijo
            return node

        node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))
        balance = self._get_balance(node)
        
        # Rotaciones después de la eliminación
        if balance > 1 and self._get_balance(node.left) >= 0:
            self.stats['LL'] += 1
            return self._right_rotate(node)
        if balance > 1 and self._get_balance(node.left) < 0:
            self.stats['LR'] += 1
            node.left = self._left_rotate(node.left)
            return self._right_rotate(node)
        if balance < -1 and self._get_balance(node.right) <= 0:
            self.stats['RR'] += 1
            return self._left_rotate(node)
        if balance < -1 and self._get_balance(node.right) > 0:
            self.stats['RL'] += 1
            node.right = self._right_rotate(node.right)
            return self._left_rotate(node)
        return node

    def _inorder(self, node, routes):
        if node:
            self._inorder(node.left, routes)
            routes.append(f"{node.prefix}/{self._mask_to_cidr(node.mask)} via {node.next_hop} metric {node.metric}")
            self._inorder(node.right, routes)

    def _mask_to_cidr(self, mask):
        return sum(bin(int(x)).count('1') for x in mask.split('.'))

    def _count_nodes(self, node):
        if not node:
            return 0
        return 1 + self._count_nodes(node.left) + self._count_nodes(node.right)

    def _get_height(self, node):
        if not node:
            return 0
        return node.height

    def _get_balance(self, node):
        if not node:
            return 0
        return self._get_height(node.left) - self._get_height(node.right)

    def _right_rotate(self, y):
        x = y.left
        T2 = x.right
        x.right = y
        y.left = T2
        y.height = 1 + max(self._get_height(y.left), self._get_height(y.right))
        x.height = 1 + max(self._get_height(x.left), self._get_height(x.right))
        return x

    def _left_rotate(self, x):
        y = x.right
        T2 = y.left
        y.left = x
        x.right = T2
        x.height = 1 + max(self._get_height(x.left), self._get_height(x.right))
        y.height = 1 + max(self._get_height(y.left), self._get_height(y.right))
        return y

    def _min_value_node(self, node):
        current = node
        while current.left:
            current = current.left
        return current

    def _ascii_tree(self, node, prefix="", is_left=True):
        if not node:
            return ""
        result = ""
        
        # Recorrer el subárbol derecho primero para imprimir de forma más intuitiva
        if node.right:
            result += self._ascii_tree(node.right, prefix + ("│   " if is_left else "    "), False)
        
        result += prefix
        result += "└── " if is_left else "┌── "
        result += f"[{node.prefix}/{self._mask_to_cidr(node.mask)}]"
        result += "\n"
        
        if node.left:
            result += self._ascii_tree(node.left, prefix + ("    " if is_left else "│   "), True)
            
        return result

    def save_to_json(self, filename):
        """Guarda la tabla de rutas en un archivo JSON."""
        routes = []
        self._collect_routes(self.root, routes)
        with open(filename, 'w') as f:
            json.dump(routes, f, indent=2)

    def load_from_json(self, filename):
        """Carga la tabla de rutas desde un archivo JSON."""
        try:
            with open(filename, 'r') as f:
                routes = json.load(f)
            # Limpiar el árbol actual antes de cargar nuevas rutas
            self.root = None
            self.stats = {'LL': 0, 'LR': 0, 'RL': 0, 'RR': 0}
            for r in routes:
                self.add_route(r['prefix'], r['mask'], r['next_hop'], r['metric'])
        except FileNotFoundError:
            pass

    def _collect_routes(self, node, routes):
        if node:
            self._collect_routes(node.left, routes)
            routes.append({
                'prefix': node.prefix,
                'mask': node.mask,
                'next_hop': node.next_hop,
                'metric': node.metric
            })
            self._collect_routes(node.right, routes)