class TrieNode:
    def __init__(self):
        self.children = [None, None]  # 0 y 1
        self.policy = {}  # {'block': True} o {'ttl-min': 3}
        self.prefix = None  # Para mostrar, el prefijo completo

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def _ip_to_binary(self, ip):
        """Convierte IP a lista de bits"""
        parts = ip.split('.')
        binary = []
        for part in parts:
            bin_part = format(int(part), '08b')
            binary.extend([int(b) for b in bin_part])
        return binary

    def _mask_to_length(self, mask):
        """Convierte máscara a longitud de prefijo"""
        try:
            if mask.isdigit():
                return int(mask)
            if '/' in mask:
                return int(mask.split('/')[1])
            parts = mask.split('.')
            if len(parts) != 4:
                return None
            binary = []
            for part in parts:
                binary.extend(format(int(part), '08b'))
            return sum(1 for b in binary if b == '1')
        except ValueError:
            return None

    def insert(self, prefix, mask, policy_type, policy_value=None):
        """Inserta un prefijo con política"""
        binary = self._ip_to_binary(prefix)
        mask_len = self._mask_to_length(mask)
        if mask_len is None:
            raise ValueError("Máscara inválida")
        node = self.root
        for i in range(mask_len):
            bit = binary[i]
            if node.children[bit] is None:
                node.children[bit] = TrieNode()
            node = node.children[bit]
        # Al final del prefijo, setear política
        if policy_type == 'block':
            node.policy = {'block': True}
        elif policy_type == 'ttl-min':
            node.policy = {'ttl-min': policy_value}
        node.prefix = f"{prefix}/{mask_len}"

    def delete(self, prefix, mask):
        """Elimina la política de un prefijo"""
        binary = self._ip_to_binary(prefix)
        mask_len = self._mask_to_length(mask)
        if mask_len is None:
            raise ValueError("Máscara inválida")
        node = self.root
        path = []
        for i in range(mask_len):
            bit = binary[i]
            if node.children[bit] is None:
                return  # No existe
            path.append((node, bit))
            node = node.children[bit]
        # Limpiar política
        node.policy = {}
        node.prefix = None
        # Opcional: limpiar nodos vacíos, pero por simplicidad, no lo hago

    def search(self, ip):
        """Busca la política para la IP (longest prefix match)"""
        binary = self._ip_to_binary(ip)
        node = self.root
        best_policy = {}
        for bit in binary:
            if node.children[bit] is None:
                break
            node = node.children[bit]
            if node.policy:
                best_policy = node.policy
        return best_policy

    def _print_tree_recursive(self, node, depth=0, prefix_bits=[], is_last=True):
        """Imprime el árbol recursivamente"""
        indent = ""
        for i in range(depth):
            if i == depth - 1:
                indent += "└── " if is_last else "├── "
            else:
                indent += "  "  # Reducido de 4 a 2 espacios
        if node.prefix:
            policy_str = ""
            if 'block' in node.policy:
                policy_str = "{block}"
            elif 'ttl-min' in node.policy:
                policy_str = f"{{ttl-min={node.policy['ttl-min']}}}"
            print(f"{indent}{node.prefix} {policy_str}")
        elif node.policy:
            ip = self._binary_to_ip(prefix_bits)
            if ip:
                policy_str = ""
                if 'block' in node.policy:
                    policy_str = "{block}"
                elif 'ttl-min' in node.policy:
                    policy_str = f"{{ttl-min={node.policy['ttl-min']}}}"
                print(f"{indent}{ip} {policy_str}")
        children = [bit for bit in [0, 1] if node.children[bit]]
        for i, bit in enumerate(children):
            last = (i == len(children) - 1)
            self._print_tree_recursive(node.children[bit], depth + 1, prefix_bits + [bit], last)

    def print_tree(self):
        """Imprime el trie de prefijos"""
        if not self.root.children[0] and not self.root.children[1]:
            print("No policies configured")
            return
        for bit in [0, 1]:
            if self.root.children[bit]:
                self._print_tree_recursive(self.root.children[bit], 0, [bit], True)

    def get_policies(self):
        """Devuelve una lista de políticas: [(prefix, mask, policy_type, policy_value)]"""
        policies = []
        self._collect_policies(self.root, policies)
        return policies

    def _collect_policies(self, node, policies):
        """Recoge políticas recursivamente"""
        if node.prefix and node.policy:
            prefix, mask = node.prefix.split('/')
            if 'block' in node.policy:
                policies.append((prefix, mask, 'block', None))
            elif 'ttl-min' in node.policy:
                policies.append((prefix, mask, 'ttl-min', node.policy['ttl-min']))
        for bit in [0, 1]:
            if node.children[bit]:
                self._collect_policies(node.children[bit], policies)
