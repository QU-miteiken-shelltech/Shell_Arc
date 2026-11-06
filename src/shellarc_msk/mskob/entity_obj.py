from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex
from shellarc_msk.mskob.property_obj import MSK_Property
from shellarc_msk.mskob.adress_obj import MSK_Adress

class MSK_Entity:
    def __init__(self,
                 container_bin: bytes,
                 entity_count: int
                 ) -> None:
        entity_start = 48 * entity_count
        entity_end = 48 * (entity_count + 1) - 1
        if len(container_bin) < entity_end + 1:
            raise ValueError("Requested entity exceeded binary size")
        self.container_index : MSK_HexIndex = MSK_HexIndex(value=container_bin[entity_start : entity_start + 16].decode("utf-8"))
        prop_index = MSK_HexIndex(value=container_bin[entity_start + 16 : entity_start + 32].decode("utf-8"))
        self.prop : MSK_Property = MSK_Property(prop_index=prop_index)
        adress_index = MSK_HexIndex(value=container_bin[entity_start + 32 : entity_end + 1].decode("utf-8"))
        self.address : MSK_Adress = MSK_Adress(adress_index=adress_index)