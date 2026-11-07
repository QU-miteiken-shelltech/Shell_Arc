from shellarc_msk.mskdn.metanode import MSKDN_Metanode

class MSKDN_AbstEdge:
    def __init__(self,
                 upstream: MSKDN_Metanode,
                 derivitive: MSKDN_Metanode
                 ) -> None:
        self.upstream : MSKDN_Metanode = upstream
        self.derivitive : MSKDN_Metanode = derivitive

