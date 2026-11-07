from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex
from shellarc_msk.mskob.property_obj import MSK_Property
from shellarc_msk.mskob.adress_obj import MSK_Adress

class MSK_Entity:
    def __init__(self,
                 entity_chunk: bytes
                 ) -> None:
        if len(entity_chunk) != 48:
            raise ValueError("Requested entity exceeded binary size")
        self.container_index : MSK_HexIndex = MSK_HexIndex(value=entity_chunk[: 16].decode("utf-8"))
        prop_index = MSK_HexIndex(value=entity_chunk[16 : 32].decode("utf-8"))
        self.prop : MSK_Property = MSK_Property(prop_index=prop_index)
        adress_index = MSK_HexIndex(value=entity_chunk[32 :].decode("utf-8"))
        self.address : MSK_Adress = MSK_Adress(adress_index=adress_index)