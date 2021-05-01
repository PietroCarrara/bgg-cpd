from math import floor

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
            print(f'{self.tree.get_key(d)} ', end='')
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
                lambda a, b: self.tree.get_key(a) > self.tree.get_key(b)
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
            node = self.find_node_that_may_contain_key(self.tree.get_key(value))

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
            if key < self.tree.get_key(self.data[i]):
                return self.children[i]

            # We won't even write code for the right-side path,
            # because we allocated an extra position in the data,
            # so we will actually 

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


class BTree:
    def __init__(self, order, get_key):
        # Max number of children per node
        self.order = order
        # Function to retreive a key for a specific data element
        self.get_key = get_key
        # Root node
        self.root = BTreeNode(self)

    # Print the tree
    def debug_display(self):
        self.root.debug_display()
        print()

    def insert(self, value):
        self.root.insert(value)
