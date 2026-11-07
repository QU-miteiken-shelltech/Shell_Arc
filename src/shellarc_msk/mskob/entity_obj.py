from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex
from shellarc_msk.mskob.property_obj import MSK_Property
from shellarc_msk.mskob.adress_obj import MSK_Adress

class MSK_Entity:
    def __init__(self,
                 entity_chunk: bytes | None
                 ) -> None:
        if len(entity_chunk) != 48:
            raise ValueError("Requested entity exceeded binary size")
        self.container_index : MSK_HexIndex = MSK_HexIndex(value=None)
        self.prop : MSK_Property = MSK_Property(prop_index=MSK_HexIndex(value=None))
        self.address : MSK_Adress = MSK_Adress(adress_index=MSK_HexIndex(value=None))
        if entity_chunk is None:
            return

        self.container_index = MSK_HexIndex.from_bytes(entity_chunk[: 16])
        prop_index = MSK_HexIndex.from_bytes(entity_chunk[16 : 32])
        self.prop = MSK_Property(prop_index=prop_index)
        adress_index = MSK_HexIndex.from_bytes(entity_chunk[32 :])
        self.address = MSK_Adress(adress_index=adress_index)