from typing import overload

from shellarc_msk.mskob.containercoll_obj import MSK_ContainerCollection
from shellarc_msk.mskob.container_obj import MSK_Container
from shellarc_msk.mskob.property_obj import MSK_Property
from shellarc_msk.mskob.adress_obj import MSK_Address
from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex
from shellarc_msk.mskob.entity_obj import MSK_Entity
from shellarc_msk.mskdn.metanode import MSKDN_Metanode
from shellarc_msk.mskdn.hypergraph import MSKDN_Hypergraph
from shellarc_msk.mskdn.abstract_edge import MSKDN_AbstEdge

@overload 
def update_info(
    prop: MSK_Property,
    new_value: str,
    container: MSK_Container
    ) -> None:
    ...

@overload 
def update_info(
    prop: MSK_Property,
    new_value: str,
    field_name: str,
    container_index: MSK_HexIndex
    ) -> None:
    ...

def update_info(
        prop: MSK_Property,
        new_value: str,
        container: MSK_Container | None=None,
        field_name: str | None=None,
        container_index: MSK_HexIndex | None=None
        ) -> None:
    if container is None:
        coll = MSK_ContainerCollection(field_name=field_name)
        coll.write_entity(
            container_index=container_index,
            prop=prop,
            adress=MSK_Address(
                adress_type=prop.prop_type,
                adress_value=new_value
            )
        )
    else:
        container.write_entity(
            prop=prop,
            adress=MSK_Address(
                adress_type=prop.prop_type,
                adress_value=new_value
            )
        )

@overload 
def proceed_info(
    prop: MSK_Property,
    proceed_step: int,
    container: MSK_Container
    ) -> None:
    ...

@overload 
def proceed_info(
    prop: MSK_Property,
    proceed_step: int,
    field_name: str,
    container_index: MSK_HexIndex
    ) -> None:
    ...

def proceed_info(
        prop: MSK_Property,
        proceed_step: int,
        container: MSK_Container | None=None,
        field_name: str | None=None,
        container_index: MSK_HexIndex | None=None
        ) -> None:
    if container is None:
        coll = MSK_ContainerCollection(field_name=field_name)
        coll.write_entity(
            container_index=container_index,
            prop=prop,
            proceed_step=proceed_step
        )
    else:
        container.write_entity(
            prop=prop,
            proceed_step=proceed_step
        )
    