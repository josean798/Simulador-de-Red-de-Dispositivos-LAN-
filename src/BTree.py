import json
import os
from datetime import datetime

class BTreeNode:
    def __init__(self, leaf=False):
        self.leaf = leaf
        self.keys = []
        self.children = []
        self.next = None  # For leaf nodes

class BTree:
    def __init__(self, order=4, index_file="btree_index.json"):
        self.order = order
        self.root = BTreeNode(leaf=True)
        self.index_file = index_file
        self.splits = 0
        self.merges = 0
        self.load_index()

    def load_index(self):
        if os.path.exists(self.index_file):
            with open(self.index_file, 'r') as f:
                data = json.load(f)
                self.order = data.get('order', 4)
                self.splits = data.get('splits', 0)
                self.merges = data.get('merges', 0)
                self.root = self.deserialize_node(data['root'])

    def save_index(self):
        data = {
            'order': self.order,
            'splits': self.splits,
            'merges': self.merges,
            'root': self.serialize_node(self.root)
        }
        with open(self.index_file, 'w') as f:
            json.dump(data, f, indent=2)

    def serialize_node(self, node):
        if not node:
            return None
        return {
            'leaf': node.leaf,
            'keys': node.keys,
            'children': [self.serialize_node(child) for child in node.children],
            'next': node.next
        }

    def deserialize_node(self, data):
        if not data:
            return None
        node = BTreeNode(leaf=data['leaf'])
        node.keys = data['keys']
        node.children = [self.deserialize_node(child) for child in data['children']]
        node.next = data.get('next')
        return node

    def insert(self, key, value):
        root = self.root
        if len(root.keys) == (2 * self.order) - 1:
            new_root = BTreeNode()
            self.root = new_root
            new_root.children.append(root)
            self.split_child(new_root, 0)
            self._insert_non_full(new_root, key, value)
        else:
            self._insert_non_full(root, key, value)
        self.save_index()

    def _insert_non_full(self, node, key, value):
        i = len(node.keys) - 1
        if node.leaf:
            node.keys.append(None)
            while i >= 0 and key < node.keys[i][0]:
                node.keys[i + 1] = node.keys[i]
                i -= 1
            node.keys[i + 1] = (key, value)
        else:
            while i >= 0 and key < node.keys[i][0]:
                i -= 1
            i += 1
            if len(node.children[i].keys) == (2 * self.order) - 1:
                self.split_child(node, i)
                if key > node.keys[i][0]:
                    i += 1
            self._insert_non_full(node.children[i], key, value)

    def split_child(self, parent, i):
        order = self.order
        y = parent.children[i]
        z = BTreeNode(leaf=y.leaf)
        parent.children.insert(i + 1, z)
        parent.keys.insert(i, y.keys[order - 1])
        z.keys = y.keys[order:(2 * order - 1)]
        y.keys = y.keys[0:(order - 1)]
        if not y.leaf:
            z.children = y.children[order:(2 * order)]
            y.children = y.children[0:order]
        self.splits += 1

    def search(self, key):
        return self._search(self.root, key)

    def _search(self, node, key):
        i = 0
        while i < len(node.keys) and key > node.keys[i][0]:
            i += 1
        if i < len(node.keys) and key == node.keys[i][0]:
            return node.keys[i][1]
        if node.leaf:
            return None
        return self._search(node.children[i], key)

    def inorder_traversal(self, node, result):
        if node:
            i = 0
            if not node.leaf:
                self.inorder_traversal(node.children[i], result)
            while i < len(node.keys):
                result.append(node.keys[i])
                if not node.leaf:
                    i += 1
                    self.inorder_traversal(node.children[i], result)
                else:
                    i += 1

    def get_snapshots(self):
        result = []
        self.inorder_traversal(self.root, result)
        return result

    def get_height(self, node):
        if not node:
            return 0
        if node.leaf:
            return 1
        return 1 + self.get_height(node.children[0])

    def get_stats(self):
        height = self.get_height(self.root)
        nodes = self.count_nodes(self.root)
        return {
            'order': self.order,
            'height': height,
            'nodes': nodes,
            'splits': self.splits,
            'merges': self.merges
        }

    def count_nodes(self, node):
        if not node:
            return 0
        count = 1
        for child in node.children:
            count += self.count_nodes(child)
        return count