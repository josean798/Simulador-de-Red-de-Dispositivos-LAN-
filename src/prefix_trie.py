"""
Modulo 3: Árbol N-ario (Trie) para Prefijos IP y Políticas Jerárquicas
Implementa un trie binario/base-256 para prefijos IP y políticas (ttl-min, block).
Permite herencia de políticas y visualización jerárquica.
"""
import json
from typing import Optional, Dict, Any, List

class TrieNode:
    def __init__(self):
        self.children: Dict[int, 'TrieNode'] = {}
        self.policy: Optional[Dict[str, Any]] = None
        self.is_end: bool = False
        self.prefix: Optional[str] = None
        self.mask: Optional[str] = None

class PrefixTrie:
    def __init__(self, base: int = 256):
        self.root = TrieNode()
        self.base = base

    def set_policy(self, prefix: str, mask: str, policy_type: str, value: Any = None):
        """Establece una política en el nodo correspondiente al prefijo/máscara."""
        node = self._get_node(prefix, mask, create=True)
        if not node.policy:
            node.policy = {}
        if policy_type == 'block':
            node.policy['block'] = True
        elif policy_type == 'ttl-min':
            node.policy['ttl-min'] = value
        node.is_end = True
        node.prefix = prefix
        node.mask = mask

    def unset_policy(self, prefix: str, mask: str):
        """Elimina la política del nodo correspondiente al prefijo/máscara."""
        node = self._get_node(prefix, mask, create=False)
        if node and node.policy:
            node.policy = None

    def lookup_policy(self, ip: str) -> Optional[Dict[str, Any]]:
        """Busca la política más específica para la IP (herencia)."""
        node = self.root
        ip_parts = list(map(int, ip.split('.')))
        best_policy = None
        for part in ip_parts:
            if part in node.children:
                node = node.children[part]
                if node.policy:
                    best_policy = node.policy
            else:
                break
        return best_policy

    def show_tree(self) -> str:
        """Devuelve un diagrama ASCII del trie con prefijos y políticas."""
        lines = []
        self._ascii_trie(self.root, lines, "")
        return "\n".join(lines)

    def _ascii_trie(self, node: TrieNode, lines: List[str], prefix: str):
        if node.is_end:
            pol = f" {node.policy}" if node.policy else ""
            lines.append(f"{prefix}{node.prefix}/{self._mask_to_cidr(node.mask)}{pol}")
        for k, child in node.children.items():
            self._ascii_trie(child, lines, prefix + "└── ")

    def _get_node(self, prefix: str, mask: str, create: bool = False) -> Optional[TrieNode]:
        node = self.root
        prefix_parts = list(map(int, prefix.split('.')))
        mask_parts = list(map(int, mask.split('.')))
        for i in range(4):
            if mask_parts[i] == 0:
                break
            part = prefix_parts[i]
            if part not in node.children:
                if create:
                    node.children[part] = TrieNode()
                else:
                    return None
            node = node.children[part]
        return node

    def _mask_to_cidr(self, mask):
        return sum(bin(int(x)).count('1') for x in mask.split('.'))

    def save_to_json(self, filename):
        """Guarda el trie en un archivo JSON."""
        data = self._collect_trie(self.root)
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    def load_from_json(self, filename):
        """Carga el trie desde un archivo JSON."""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            self.root = self._rebuild_trie(data)
        except FileNotFoundError:
            pass

    def _collect_trie(self, node: TrieNode):
        result = {}
        if node.is_end:
            result['policy'] = node.policy
            result['prefix'] = node.prefix
            result['mask'] = node.mask
        result['children'] = {str(k): self._collect_trie(child) for k, child in node.children.items()}
        return result

    def _rebuild_trie(self, data):
        node = TrieNode()
        if 'policy' in data:
            node.policy = data['policy']
            node.is_end = True
            node.prefix = data.get('prefix')
            node.mask = data.get('mask')
        for k, child_data in data.get('children', {}).items():
            node.children[int(k)] = self._rebuild_trie(child_data)
        return node

