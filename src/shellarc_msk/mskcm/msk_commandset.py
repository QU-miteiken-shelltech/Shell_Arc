from operator import attrgetter
from typing import get_type_hints

from shellarc_msk.mskdn import *
from shellarc_msk.mskob.field_obj import MSK_Field
from shellarc_msk.mskob.adress_obj import MSK_Address
from shellarc_msk.mskob.container_obj import MSK_Container
from shellarc_msk.mskob.containercoll_obj import MSK_ContainerCollection
from shellarc_msk.mskob.entity_obj import MSK_Entity
from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex
from shellarc_msk.mskob.property_obj import MSK_Property
from shellarc_msk.mskob.type_obj import MSK_Type


class MSKCM_CommandSet:
    @classmethod
    def link_field(cls, 
                   field_name: str
                   ) -> MSK_ContainerCollection:
        return MSK_ContainerCollection(
            field_name=field_name
        )

    @classmethod
    def iter_container(cls,
                       cointainer_coll: MSK_ContainerCollection,
                       target: list[str]
                       ) -> list:
        container_iter = cointainer_coll.container_iter()
        rtn = []
        for container in container_iter:
            obj = container
            for a in target:
                obj = getattr(obj, a, None)
            rtn.append(obj)
        return rtn

    @classmethod
    def sort_iterable(cls,
                      iterable: list,
                      target: list[str],
                      is_reverse: bool=False
                      ) -> list:
        return sorted(
            iterable, 
            key=attrgetter(".".join(target)), 
            reverse=is_reverse
        )
