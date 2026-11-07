from shellarc_msk.mskob.entity_obj import MSK_Entity

class MSKDN_VNode:
    """Minimal placeholder (node.py was empty and failed to import).

    Wraps one MSK_Entity and exposes the .prop / .address that
    MSKDN_Hypergraph.get_abstract_edge reads from metanode members.
    """
    def __init__(self, entity: MSK_Entity) -> None:
        self.entity = entity

    @property
    def prop(self):
        return self.entity.prop

    @property
    def address(self):
        return self.entity.address
