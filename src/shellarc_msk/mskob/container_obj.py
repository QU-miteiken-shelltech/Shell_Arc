from collections import UserList
from typing import Optional

from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex
from shellarc_msk.mskob.entity_obj import MSK_Entity
from shellarc_msk.mskob.property_obj import MSK_Property
from shellarc_msk.mskob.adress_obj import MSK_Address
from shellarc_msk.mskob.containercoll_obj import MSK_ContainerCollection

class MSK_Container(UserList[MSK_Entity], MSK_ContainerCollection):
    def __init__(self,
                 field_name: str,
                 container_index: Optional[MSK_HexIndex]=None,
                 container_offset_counts: Optional[list[int]]=None
                 ) -> None:
        MSK_ContainerCollection.__init__(self, field_name=field_name)
        if container_offset_counts is not None:
            member_entities = self._find_from_offset_count(
                offset_counts=container_offset_counts
            )
        elif container_index is not None:
            member_entities = self._find_from_mskindex(
                container_index=container_index
            )
        else:
            raise ValueError("Container cannot be built from None")
        super().__init__(member_entities)
        self.container_index = container_index

    def _find_from_offset_count(self,
                                offset_counts: list[int]
                                ) -> list[MSK_Entity]:
        entities = []
        for c in offset_counts:
            entities.append(
                MSK_Entity(
                    entity_chunk=self.container_bin[c * 48 : (c + 1) * 48]
                )
            )
        return entities

    def _find_from_mskindex(self,
                            container_index: MSK_HexIndex
                            ) -> list[MSK_Entity]:
        # cached in MSKFS_OnRamData.container_index_table; scanned (and cached) only on a miss
        return self._find_from_offset_count(
            offset_counts=self._rows_of_container(container_index)
        )

    def append(self, object):
        if not isinstance(object, MSK_Entity):
            return
        return super().append(object)

    def request_adress(self,
                       requesting_prop: MSK_Property
                       ) -> MSK_Address:
        for entity in self:
            if entity.prop == requesting_prop:
                return entity.address

        return MSK_Address(adress_index=MSK_HexIndex(value=None))

    def request_entity(self,
                       requesting_prop: MSK_Property
                       ) -> MSK_Entity:
        for entity in self:
            if entity.prop == requesting_prop:
                return entity

        # absent property reads as null: return an Entity holding the null address
        null = MSK_HexIndex(value=None)
        container_index = self.container_index if self.container_index is not None else null
        return MSK_Entity(
            entity_chunk=(container_index.to_bytes() +
                          requesting_prop.prop_index.to_bytes() +
                          null.to_bytes())
        )