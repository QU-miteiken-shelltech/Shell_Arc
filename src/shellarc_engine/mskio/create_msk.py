from typing import Optional

from shellarc_msk.mskob.field_obj import MSK_Field
from shellarc_msk.mskob.containercoll_obj import MSK_ContainerCollection
from shellarc_msk.mskob.container_obj import MSK_Container
from shellarc_msk.mskob.property_obj import MSK_Property
from shellarc_msk.mskob.adress_obj import MSK_Address
from shellarc_msk.mskob.type_obj import MSK_Type
from shellarc_msk.mskob.entity_obj import MSK_Entity
from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex
from shellarc_msk.mskdn.metanode import MSKDN_Metanode
from shellarc_msk.mskdn.hypergraph import MSKDN_Hypergraph
from shellarc_msk.mskdn.abstract_edge import MSKDN_AbstEdge

def create_field(new_field_name: str):
    field = MSK_Field(
        field_name=new_field_name,
        allow_make=True
    )

def add_field_def(field_name: str,
                  new_type: MSK_Type, 
                  new_property: MSK_Property
                  ):
    MSK_Field(
        field_name=field_name,
    ).def_field(
        prop=new_property,
        type=new_type
    )

def create_type(type_name: str,
                type_literals: Optional[list[str]]=None
                ) -> MSK_Type:
    new_type = MSK_Type(
        type_name=type_name,
        type_literals=type_literals,
        allow_make=True
    )
    return new_type

def create_property(prop_type: MSK_Type,
                    prop_name: str
                    ) -> MSK_Property:
    new_property = MSK_Property(
        prop_type=prop_type,
        prop_name=prop_name,
        allow_make=True
    )
    return new_property

def create_entity(field_name: str, 
                  container_index: MSK_HexIndex,
                  prop: MSK_Property,
                  adress: MSK_Address,
                  is_override: bool
                  ):
    coll = MSK_ContainerCollection(field_name=field_name)
    coll.write_entity(
        container_index=container_index,
        prop=prop,
        adress=adress,
        do_override=is_override
    )

def create_by_filter(field_name: str,
                     conditions: list[tuple[MSK_Property, MSK_Address]],
                     is_override: bool
                     ):
    coll = MSK_ContainerCollection(field_name=field_name)
    containers = coll.filter_container(
        conditions=conditions,
        max_count=2,
        do_make=True
    )
    if len(containers) > 1:
        raise ValueError("Container cannot be specified")
    container = containers[0]
    for condition in conditions:
        prop = condition[0]
        adress = condition[1]
        container.write_entity(
            prop=prop,
            adress=adress,
            do_override=is_override
        )