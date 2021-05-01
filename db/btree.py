from math import floor
from utils import split
import os
from .persistence import Uint32PairPersist

# Inserts a value in the first empty space found,
# or in the first position that would keep the array
# ordered from smallest to greatest
def shift_insert(arr, insert_value, greater_than, position=0):
    if position >= len(arr):
        raise Exception('Tried inserting into full array')

    if arr[position] == None:
        arr[position] = insert_value
        return

    if greater_than(arr[position], insert_value):
        val = arr[position]
        arr[position] = insert_value

        # Shift everyone one position to the right
        shift_right(arr, position + 1, val)

        return

    shift_insert(arr, insert_value, greater_than, position + 1)

# Shifts an array one slot the right, starting at `start`
def shift_right(arr, start, insert=None):
    if start >= len(arr):
        # Make sure we are not throwing out some important value
        assert insert == None

        return

    tmp = arr[start]
    arr[start] = insert

    return shift_right(arr, start + 1, tmp)


class BTreeNode:
    def __init__(self, tree, data=[], children=[], leaf=True):
        self.tree = tree
        self.leaf = leaf

        # Allocates one more node than needed, so we can easily check for overflows
        self.children = children
        for i in range((tree.order + 1) - len(children)):
            # Insert the rest of the slots
            self.children.append(None)

        # Allocates one more than needed, to we can easily check for overflows
        # (since number of children == order - 1)
        self.data = data
        for i in range(tree.order - len(data)):
            # Insert the rest of the slots
            data.append(None)

    def debug_display(self, level=0):
        print(f'Level {level}: ', end='')
        for d in self.data:
            if d == None:
                continue
            print(f'{d[0]}:{d[1]} ', end='')
        print()

        for child in self.children:
            if child == None:
                continue
            child.debug_display(level + 1)

    # Recursively insert a node in the tree.
    # Returns true if we have modified the parent, false if we have not
    def insert(self, value, parent=None):
        if self.leaf:
            # Regular insertion
            # We're a leaf node, so we don't even bother with subtrees
            shift_insert(
                self.data,
                value,
                lambda a, b: a[0] > b[0]
            )

            if self.check_overflow():
                if parent == None:
                    # We're the root
                    self.split_into_root()
                else:
                    self.split_into_parent(parent)
                    return True

            return False
        else:
            # We're not a leaf node, so we have to insert to one of our subtrees
            node = self.find_node_that_may_contain_key(value[0])

            if node.insert(value, self):
                # Our child modified us
                # Must check for overflow
                if self.check_overflow():
                    # Overflow detected
                    if parent == None:
                        # We're the root
                        self.split_into_root()
                    else:
                        self.split_into_parent(parent)
                        return True

            return False

    # Returns a subnode where the provided key would be located
    def find_node_that_may_contain_key(self, key):
        if self.leaf:
            return None

        for i in range(len(self.data)):
            # We have seen every single data cell, stop
            # (Remember that we will always have a null slot in the end of this array,
            # for easier overflow checks. Check the constructor for more info)
            if self.data[i] == None:
                return self.children[i]

            # If we've found a key that is smaller than provided, we must
            # get down on the tree to the left of this element, so we stop.
            if key < self.data[i][0]:
                return self.children[i]

            # We won't even write code for the right-side path,
            # because we allocated an extra position in the data.
            # In a normal btree, we would look at the right only when
            # we hit the last spot. Since we have one more spot, we
            # can afford to look only at the left

        raise Exception('This should never happen')

    # Returns whether there is a overflow or not
    def check_overflow(self):
        return sum(map(lambda x: x != None, self.data)) == len(self.data)

    # Splits and returns the (left_subtree, middle_element, right_subtree)
    # Also marks this node as not being a leaf anymore
    def split(self):
        is_leaf = self.leaf
        mid = floor((self.tree.order-1) / 2)

        left = self.data[:mid]
        middle = self.data[mid]
        right = self.data[mid+1:]

        self.leaf = False

        return (
            BTreeNode(self.tree, left, self.children[:mid+1], is_leaf),
            middle,
            BTreeNode(self.tree, right, self.children[mid+1:], is_leaf)
        )

    # Splits assuming this node is the root of the tree
    def split_into_root(self):
        left, mid, right = self.split()

        self.data = [None] * self.tree.order
        self.data[0] = mid

        self.children = [None] * (self.tree.order + 1)
        self.children[0] = left
        self.children[1] = right

    # Splits and carries one element to our parent
    def split_into_parent(self, parent):
        left, mid, right = self.split()

        for i in range(len(parent.children)):
            if parent.children[i] == self:
                # Replace our link with our left child
                parent.children[i] = left

                # Move people aside, so we can put our data
                # up in our parent
                shift_right(parent.data, i)
                shift_right(parent.children, i + 1)

                parent.data[i] = mid
                parent.children[i + 1] = right

                return

        # This should never happen
        raise Exception(
            'Parent does not contain a link to us: it is not our actual parent!')

    def get_data(self):
        # [0:-1] to discard the extra slot that is allocated
        return self.data[:-1]

    # Returns all nodes of the tree, including null links
    # (except for tree nodes, we don't return any of their children)
    def bfs_with_nulls(self):
        queue = [self]
        discovered = [self]

        while len(queue) > 0:
            node = queue.pop(0)
            yield node

            if node == None:
                continue

            if not node.leaf:
                # [0:-1] to discard the extra slot that is allocated
                for child in node.children[0:-1]:
                    if child == None:
                        queue.append(child)
                    elif child not in discovered:
                        discovered.append(child)
                        queue.append(child)

    def __repr__(self):
        data = []

        for i in self.data:
            if i != None:
                data.append(f'{i[0]}:{i[1]}')

        return '[' + ', '.join(data) + ']'


class BTree:
    def __init__(self, order):
        # Max number of children per node
        self.order = order
        # Root node
        self.root = BTreeNode(self)

    # Print the tree
    def debug_display(self):
        self.root.debug_display()
        print()

    def insert(self, key, value):
        self.root.insert((key, value))

    def bfs_with_nulls(self):
        return self.root.bfs_with_nulls()


class PersistentBTree:
    # Stores a BTree in a file, representing it as an array:
    # The n-th (0-based) child of the i-th (0-based) node is the
    # order * i + n + 1 element of the array
    def __init__(self, order, filename, persist):
        self.filesize = os.path.getsize(filename)
        self.order = order
        self.persist = persist

        mode = 'ab+' if os.path.exists(filename) else 'wb+'
        self.file = open(filename, mode)

    def dump(self, tree):
        assert tree.order == self.order

        # size of data point * number of data points
        node_size = self.persist.data_size * (self.order - 1)

        # Start at the begining (duh)
        self.file.seek(0)

        for node in tree.bfs_with_nulls():
            if node == None:
                self.file.write(self.persist.to_bytes(None) * (self.order - 1))
            else:
                for data_point in node.get_data():
                    self.file.write(self.persist.to_bytes(data_point))

        # Discard any leftover
        self.file.truncate()

    def find(self, key):
        node_number = 0
        node = self.load_node(0)

        while node != None:
            i = 0

            for data in node:
                # We have walked all the array and not found a single key
                # greater than ours, dive to the rightmost child (which i points to)
                if data == None:
                    break

                # If our key is smaller than one on this node, we must
                # dive into the left child of it (which i points to)
                if key < data[0]:
                    break
                
                # Found the key
                if data[0] == key:
                    return data[1]

                i += 1

            node_number = self.child_of(node_number, i)
            node = self.load_node(node_number)

        return None
        
    def child_of(self, parent, child):
        return self.order * parent + child + 1

    # Loads the i-th (0-based) node of the tree
    def load_node(self, i):
        location = i * (self.persist.data_size * (self.order - 1))

        if location >= self.filesize:
            return None

        self.file.seek(location)

        bts = self.file.read(self.persist.data_size * (self.order - 1))

        data = [self.persist.from_bytes(b) for b in split(bts, self.persist.data_size)]

        # Check if there are no data points in this node
        if data[0] == None:
            return None

        return data

    def close(self):
        self.file.close()
