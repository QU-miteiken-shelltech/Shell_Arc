from functools import cached_property

from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex
from shellarc_msk.mskob.property_obj import MSK_Property
from shellarc_msk.mskob.adress_obj import MSK_Address

class MSK_Entity:
    container_index : MSK_HexIndex

    def __init__(self,
                 entity_chunk: bytes | None
                 ) -> None:
        self.entity_chunk = entity_chunk

        if entity_chunk is None:
            self.container_index = MSK_HexIndex(value=None)
            return
        if len(entity_chunk) != 48:
            raise ValueError("Requested entity exceeded binary size")

        self.container_index = MSK_HexIndex.from_bytes(entity_chunk[: 16])

    @cached_property
    def prop(self) -> MSK_Property:
        if self.entity_chunk is None:
            return MSK_Property(prop_index=MSK_HexIndex(value=None))
        else:
            prop_index = MSK_HexIndex.from_bytes(self.entity_chunk[16 : 32])
            return MSK_Property(prop_index=prop_index)

    @cached_property
    def address(self) -> MSK_Address:
        if self.entity_chunk is None:
            return MSK_Address(adress_index=MSK_HexIndex(value=None))
        else:
            adress_index = MSK_HexIndex.from_bytes(self.entity_chunk[32 :])
            return MSK_Address(adress_index=adress_index)


    def __eq__(self, other):
        if not isinstance(other, MSK_Entity):
            return NotImplemented
        return (
            self.container_index == other.container_index and
            self.prop == other.prop and
            self.address == other.address
        )

    def __str__(self):
        rtn_str = f" \
            container_index : {self.container_index} \n \
            property_name : {self.prop.prop_name} \n \
            address_value : {self.address.value} \
        " 
        return rtn_str

    def general_eq(self, other):
        if not isinstance(other, MSK_Entity):
            return NotImplemented
        return (self.prop, self.address) == (other.prop, other.address)