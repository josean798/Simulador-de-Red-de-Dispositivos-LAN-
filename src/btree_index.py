"""
Modulo 2: Índice Persistente de Configuraciones con B-tree
Implementa un índice B-tree para snapshots y logs de configuración.
Cada clave es un timestamp o nombre, y el valor es el archivo asociado.
"""
import json
from typing import Optional, List, Dict, Any

class BTreeNode:
    def __init__(self, order: int):
        self.order = order
        self.keys: List[str] = []
        self.values: List[str] = []
        self.children: List['BTreeNode'] = []
        self.leaf: bool = True

class BTreeIndex:
    def __init__(self, order: int = 4):
        self.root = BTreeNode(order)
        self.order = order
        self.stats = {'splits': 0, 'merges': 0}

    def insert(self, key: str, value: str):
        """Inserta una clave y valor en el B-tree."""
        root = self.root
        if len(root.keys) == (2 * self.order) - 1:
            new_root = BTreeNode(self.order)
            new_root.leaf = False
            new_root.children.append(root)
            self._split_child(new_root, 0)
            self.root = new_root
            self.stats['splits'] += 1
            self._insert_non_full(new_root, key, value)
        else:
            self._insert_non_full(root, key, value)

    def _insert_non_full(self, node: BTreeNode, key: str, value: str):
        i = len(node.keys) - 1
        if node.leaf:
            while i >= 0 and key < node.keys[i]:
                i -= 1
            node.keys.insert(i + 1, key)
            node.values.insert(i + 1, value)
        else:
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            if len(node.children[i].keys) == (2 * self.order) - 1:
                self._split_child(node, i)
                self.stats['splits'] += 1
                if key > node.keys[i]:
                    i += 1
            self._insert_non_full(node.children[i], key, value)

    def _split_child(self, parent: BTreeNode, i: int):
        order = self.order
        y = parent.children[i]
        z = BTreeNode(order)
        z.leaf = y.leaf
        parent.keys.insert(i, y.keys[order - 1])
        parent.values.insert(i, y.values[order - 1])
        parent.children.insert(i + 1, z)
        z.keys = y.keys[order:(2 * order - 1)]
        z.values = y.values[order:(2 * order - 1)]
        y.keys = y.keys[0:order - 1]
        y.values = y.values[0:order - 1]
        if not y.leaf:
            z.children = y.children[order:(2 * order)]
            y.children = y.children[0:order]

    def search(self, key: str) -> Optional[str]:
        """Busca una clave en el B-tree y devuelve el valor."""
        return self._search(self.root, key)

    def _search(self, node: BTreeNode, key: str) -> Optional[str]:
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        if i < len(node.keys) and key == node.keys[i]:
            return node.values[i]
        if node.leaf:
            return None
        return self._search(node.children[i], key)

    def inorder(self) -> List[Any]:
        """Recorre el B-tree en orden y devuelve lista de (key, value)."""
        result = []
        self._inorder(self.root, result)
        return result

    def _inorder(self, node: BTreeNode, result: List[Any]):
        if node.leaf:
            for k, v in zip(node.keys, node.values):
                result.append((k, v))
        else:
            for i in range(len(node.keys)):
                self._inorder(node.children[i], result)
                result.append((node.keys[i], node.values[i]))
            self._inorder(node.children[-1], result)

    def show_stats(self) -> Dict:
        """Devuelve estadísticas del B-tree."""
        return {
            'order': self.order,
            'height': self._get_height(self.root),
            'nodes': self._count_nodes(self.root),
            'splits': self.stats['splits'],
            'merges': self.stats['merges']
        }

    def _get_height(self, node: BTreeNode) -> int:
        if node.leaf:
            return 1
        return 1 + self._get_height(node.children[0])

    def _count_nodes(self, node: BTreeNode) -> int:
        if node.leaf:
            return 1
        return 1 + sum(self._count_nodes(child) for child in node.children)

    def save_to_json(self, filename):
        """Guarda el índice B-tree en un archivo JSON."""
        data = self.inorder()
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    def load_from_json(self, filename):
        """Carga el índice B-tree desde un archivo JSON."""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            for k, v in data:
                self.insert(k, v)
        except FileNotFoundError:
            pass

