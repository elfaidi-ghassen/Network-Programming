
class Node:
  def __init__(self, key, value):
    self._key = key
    self._value = value
    self._prev = None
    self._next = None
  def set_prev(self, prev):
    self._prev = prev
  def set_next(self, next):
    self._next = next
  def get_value(self):
    return self._value
  def get_key(self):
    return self._key
  def set_value(self, value):
    self._value = value

class LRUCache:
  def __init__(self, capacity):
    if capacity < 2:
      raise ValueError("min capacity: 2")
    self._max_size = capacity
    self._list_head = None
    self._list_tail = None
    self._current_size = 0
    self._map = {}
  def put(self, key, value):
    if key in self._map:
      node = self._map[key]
      node.set_value(value)
      self._move_to_head(node)
      return
    # add new node
    new_node = Node(key, value)
    self._map[key] = new_node
    self._add_to_head(new_node)
    self._current_size += 1
    if self._current_size > self._max_size:
      del self._map[self._list_tail.get_key()]
      before_tail = self._list_tail._prev
      self._list_tail._prev = None
      self._current_size -= 1
      before_tail._next = None
      self._list_tail = before_tail

  def contains(self, key):
    return key in self._map
  def get(self, key):
    
    if not self.contains(key):
      return None
    node = self._map[key]
    self._move_to_head(node)
    return node.get_value()

  def _add_to_head(self, node):
    if self._list_head == None or self._list_tail == None:
      self._list_head = self._list_tail = node
    else:
      node._next = self._list_head
      self._list_head._prev = node
      self._list_head = node

  def _move_to_head(self, node):
    self._remove_node(node)
    self._add_to_head(node)

  def _remove_node(self, node):
    if node == self._list_head:
        self._list_head = node._next
    if node == self._list_tail:
        self._list_tail = node._prev
    if node._next:
      node._next._prev = node._prev
    if node._prev:
      node._prev._next = node._next
    node._prev = None
    node._next = None
