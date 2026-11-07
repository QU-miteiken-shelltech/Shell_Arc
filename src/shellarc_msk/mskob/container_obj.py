from collections import UserList

from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex
from shellarc_msk.mskob.entity_obj import MSK_Entity
from shellarc_msk.mskob.containercoll_obj import MSK_ContainerCollection

class MSK_Container(UserList, MSK_ContainerCollection):
    def __init__(self,
                 field_name: str,
                 container_index: MSK_HexIndex
                 ) -> None:
        MSK_ContainerCollection.__init__(self, field_name=field_name)
        member_entities = [
            entity for entity in self.entities_iter() 
            if entity.container_index == container_index
        ]
        super().__init__(member_entities)
        self.container_index = container_index

    def append(self, object):
        if not isinstance(object, MSK_Entity):
            return
        return super().append(object)