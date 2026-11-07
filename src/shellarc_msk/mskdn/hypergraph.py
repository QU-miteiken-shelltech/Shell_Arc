from shellarc_msk.mskob.containercoll_obj import MSK_ContainerCollection
from shellarc_msk.mskdn.abstract_edge import MSKDN_AbstEdge
from shellarc_msk.mskdn.metanode import MSKDN_Metanode
from shellarc_msk.mskdn.node import MSKDN_VNode
from shellarc_msk.mskob.property_obj import MSK_Property

class MSKDN_Hypergraph(MSK_ContainerCollection):
    def __init__(self, field_name):
        super().__init__(field_name)

    def get_abstract_edge(self,
                          upstream_metanode: MSKDN_Metanode,
                          target_prop: MSK_Property,
                          max_count: int=1
                          ) -> MSKDN_AbstEdge:
        target_containers = self.filter_container(
            conditions=[
                (node.prop, node.address) 
                for node in upstream_metanode
            ],
            max_count=max_count
        )
        derived_metanode = MSKDN_Metanode(
            iterable=[
                MSKDN_VNode(entity=c.request_entity(requesting_prop=target_prop))
                for c in target_containers
            ]
        )
        abst_edge = MSKDN_AbstEdge(
            upstream=upstream_metanode,
            derivitive=derived_metanode
        )
        return abst_edge