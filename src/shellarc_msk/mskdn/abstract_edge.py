from shellarc_msk.mskdn.metanode import MSKDN_Metanode
from shellarc_msk.mskob.property_obj import MSK_Property

class MSKDN_AbstEdge:
    def __init__(self,
                 upstream: list[MSKDN_Metanode],
                 derivitive: MSKDN_Metanode,
                 deriving_property: MSK_Property
                 ) -> None:
        self.upstream : list[MSKDN_Metanode] = upstream
        self.derivitive : MSKDN_Metanode = derivitive
        self.deriving_property : MSK_Property = deriving_property