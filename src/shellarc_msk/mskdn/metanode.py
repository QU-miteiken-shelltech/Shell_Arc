from typing import Optional
from collections import UserList
from shellarc_msk.mskdn.node import MSKDN_VNode

class MSKDN_Metanode(UserList[MSKDN_VNode]):
    def __init__(self, 
                 prim_node: Optional[int]=0,
                 iterable=None):
        super().__init__()
        self.prim_node = prim_node
        if iterable:
            for item in iterable:
                self.append(item)

    def _validate(self, object):
        if not isinstance(object, MSKDN_VNode):
            raise TypeError(f"MSKDN_VNode accepts only MSK_VNode")

    def get_prim_node(self) -> Optional[MSKDN_VNode]:
        if len(self) > self.prim_node:
            return self[self.prim_node]
        return None

    def append(self, object):
        self._validate(object)
        super().append(object)

    def extend(self, iterable):
        validated_items = []
        for item in iterable:
            self._validate(item)
            validated_items.append(item)
        super().extend(validated_items)

    def insert(self, index, object):
        self._validate(object)
        super().insert(index, object)

    def __setitem__(self, index, object):
        if isinstance(index, slice):
            for item in object:
                self._validate(item)
        else:
            self._validate(object)
        super().__setitem__(index, object)

    def __iadd__(self, iterable):
        self.extend(iterable)
        return self