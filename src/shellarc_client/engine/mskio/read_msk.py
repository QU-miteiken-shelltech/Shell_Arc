from shellarc_msk.mskob.containercoll_obj import MSK_ContainerCollection
from shellarc_msk.mskob.container_obj import MSK_Container
from shellarc_msk.mskob.property_obj import MSK_Property
from shellarc_msk.mskob.adress_obj import MSK_Address
from shellarc_msk.mskob.entity_obj import MSK_Entity
from shellarc_msk.mskdn.metanode import MSKDN_Metanode
from shellarc_msk.mskdn.hypergraph import MSKDN_Hypergraph
from shellarc_msk.mskdn.abstract_edge import MSKDN_AbstEdge

COUNTER = 0

def get_values_by_property(
        target_field_name: str,
        requested_property: MSK_Property,
        eluminate_duplication: bool=True
        ) -> list[MSK_Entity]:
    values = []
    appeared = []
    global COUNTER
    for container in MSK_ContainerCollection(field_name=target_field_name).container_iter():
        if __debug__: 
            COUNTER += 1; print(f"loop : {COUNTER}")
        entity = container.request_entity(requesting_prop=requested_property)
        entity_value = entity.address.value
        if eluminate_duplication and entity_value in appeared:
            continue
        values.append(entity)
        appeared.append(entity_value)
    return values

def filter_container_by_entity(
        target_field_name: str,
        filter_property: MSK_Property,
        filter_entity: MSK_Entity 
        ) -> list[MSK_Container]:
    rtn = []
    for container in MSK_ContainerCollection(field_name=target_field_name).container_iter():
        entity = container.request_entity(requesting_prop=filter_property)
        if entity.general_eq(filter_entity):
            rtn.append(container)
    return rtn

def solve_abst_edge(
        field_name: str,
        upstream_metanodes: list[MSKDN_Metanode],
        target_prop: MSK_Property,
        max_count: int=10
        ) -> MSKDN_AbstEdge:
    abst_edge = MSKDN_Hypergraph(field_name=field_name).get_abstract_edge(
        upstream_metanodes=upstream_metanodes,
        target_prop=target_prop,
        max_count=max_count
    )
    return abst_edge

def filter_container(
        field_name: str,
        conditions: list[tuple[MSK_Property, MSK_Address]],
        max_count: int=1
        ) -> list[MSK_Container]:
    containers = MSK_ContainerCollection(field_name=field_name).filter_container(
        conditions=conditions,
        max_count=max_count
    )
    return containers