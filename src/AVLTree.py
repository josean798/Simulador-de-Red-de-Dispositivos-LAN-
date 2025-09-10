class Route:
    def __init__(self, prefix, mask, next_hop, metric=1):
        self.prefix = prefix
        self.mask = mask
        self.next_hop = next_hop
        self.metric = metric
        self.prefix_int = self.ip_to_int(prefix)
        self.mask_int = self.ip_to_int(mask)
        self.mask_len = self.mask_to_len(mask)
        self.network = self.prefix_int & self.mask_int

    @staticmethod
    def ip_to_int(ip):
        parts = ip.split('.')
        return (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])

    def mask_to_len(self, mask):
        m = self.ip_to_int(mask)
        return bin(m).count('1')

    def __str__(self):
        return f"{self.prefix}/{self.mask_len} via {self.next_hop} metric {self.metric}"

    def tree_str(self):
        return f"[{self.prefix}/{self.mask_len}]"

class AVLNode:
    def __init__(self, route):
        self.route = route
        self.left = None
        self.right = None
        self.height = 1

class AVLTree:
    def __init__(self):
        self.root = None
        self.rotations = {'LL': 0, 'LR': 0, 'RL': 0, 'RR': 0}
        self.nodes = 0

    def height(self, node):
        return node.height if node else 0

    def balance(self, node):
        return self.height(node.left) - self.height(node.right) if node else 0

    def update_height(self, node):
        node.height = 1 + max(self.height(node.left), self.height(node.right))

    def rotate_right(self, y):
        x = y.left
        T2 = x.right
        x.right = y
        y.left = T2
        self.update_height(y)
        self.update_height(x)
        return x

    def rotate_left(self, x):
        y = x.right
        T2 = y.left
        y.left = x
        x.right = T2
        self.update_height(x)
        self.update_height(y)
        return y

    def insert(self, root, route):
        if not root:
            self.nodes += 1
            return AVLNode(route)
        if self.compare_routes(route, root.route) < 0:
            root.left = self.insert(root.left, route)
        else:
            root.right = self.insert(root.right, route)

        self.update_height(root)
        balance = self.balance(root)

        # LL
        if balance > 1 and self.compare_routes(route, root.left.route) < 0:
            self.rotations['LL'] += 1
            return self.rotate_right(root)

        # RR
        if balance < -1 and self.compare_routes(route, root.right.route) > 0:
            self.rotations['RR'] += 1
            return self.rotate_left(root)

        # LR
        if balance > 1 and self.compare_routes(route, root.left.route) > 0:
            self.rotations['LR'] += 1
            root.left = self.rotate_left(root.left)
            return self.rotate_right(root)

        # RL
        if balance < -1 and self.compare_routes(route, root.right.route) < 0:
            self.rotations['RL'] += 1
            root.right = self.rotate_right(root.right)
            return self.rotate_left(root)

        return root

    def compare_routes(self, r1, r2):
        # Comparar por network, luego mask_len desc, luego metric asc
        if r1.network != r2.network:
            return r1.network - r2.network
        if r1.mask_len != r2.mask_len:
            return r2.mask_len - r1.mask_len  # más largo primero
        return r1.metric - r2.metric

    def add_route(self, route):
        self.root = self.insert(self.root, route)

    def delete(self, root, route):
        if not root:
            return root
        cmp = self.compare_routes(route, root.route)
        if cmp < 0:
            root.left = self.delete(root.left, route)
        elif cmp > 0:
            root.right = self.delete(root.right, route)
        else:
            self.nodes -= 1
            if not root.left:
                return root.right
            elif not root.right:
                return root.left
            temp = self.min_value_node(root.right)
            root.route = temp.route
            root.right = self.delete(root.right, temp.route)

        if not root:
            return root

        self.update_height(root)
        balance = self.balance(root)

        # LL
        if balance > 1 and self.balance(root.left) >= 0:
            self.rotations['LL'] += 1
            return self.rotate_right(root)

        # LR
        if balance > 1 and self.balance(root.left) < 0:
            self.rotations['LR'] += 1
            root.left = self.rotate_left(root.left)
            return self.rotate_right(root)

        # RR
        if balance < -1 and self.balance(root.right) <= 0:
            self.rotations['RR'] += 1
            return self.rotate_left(root)

        # RL
        if balance < -1 and self.balance(root.right) > 0:
            self.rotations['RL'] += 1
            root.right = self.rotate_right(root.right)
            return self.rotate_left(root)

        return root

    def min_value_node(self, node):
        current = node
        while current.left:
            current = current.left
        return current

    def del_route(self, route):
        original_nodes = self.nodes
        self.root = self.delete(self.root, route)
        if self.nodes < original_nodes:
            self.nodes -= 1

    def lookup(self, dest_ip):
        dest_int = Route.ip_to_int(dest_ip)
        return self._lookup(self.root, dest_int)

    def _lookup(self, node, dest_int):
        if not node:
            return None
        route = node.route
        if (dest_int & route.mask_int) == route.network:
            # Check left for longer prefix
            left_match = self._lookup(node.left, dest_int)
            if left_match and left_match.mask_len > route.mask_len:
                return left_match
            # Check right
            right_match = self._lookup(node.right, dest_int)
            if right_match and right_match.mask_len > route.mask_len:
                return right_match
            return route
        elif dest_int < route.network:
            return self._lookup(node.left, dest_int)
        else:
            return self._lookup(node.right, dest_int)

    def inorder(self, node, result):
        if node:
            self.inorder(node.left, result)
            result.append(node.route)
            self.inorder(node.right, result)

    def get_routes(self):
        result = []
        self.inorder(self.root, result)
        return result

    def print_tree(self, node):
        if not node:
            return
        print(node.route.tree_str())
        if node.left or node.right:
            print(" / \\")
            left = node.left.route.tree_str() if node.left else ""
            right = node.right.route.tree_str() if node.right else ""
            print(left + " " * (20 - len(left)) + right)
            # For left subtree
            if node.left and (node.left.left or node.left.right):
                print(" / \\")
                left_left = node.left.left.route.tree_str() if node.left.left else ""
                left_right = node.left.right.route.tree_str() if node.left.right else ""
                print(" " + left_left + " " * (20 - len(left_left) - 1) + left_right)
            # For right subtree
            if node.right and (node.right.left or node.right.right):
                print(" / \\")
                right_left = node.right.left.route.tree_str() if node.right.left else ""
                right_right = node.right.right.route.tree_str() if node.right.right else ""
                print(" " + right_left + " " * (20 - len(right_left) - 1) + right_right)

    def get_height(self):
        return self.height(self.root)

    def get_stats(self):
        return {
            'nodes': self.nodes,
            'height': self.get_height(),
            'rotations': self.rotations
        }
