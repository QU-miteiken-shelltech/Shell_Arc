from typing import Optional

from shellarc_msk.mskdn.metanode import MSKDN_Metanode

class MSKDN_DirectionalEdge:
    def __init__(self,
                 upstream: MSKDN_Metanode,
                 downstream: Optional[MSKDN_Metanode]=None
                 ) -> None:
        self.upstream : MSKDN_Metanode = upstream
        self.downstream : MSKDN_Metanode = downstream