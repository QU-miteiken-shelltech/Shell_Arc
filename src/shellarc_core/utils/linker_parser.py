
class LinkerParser:
    def __init__(self):
        from shellarc_core.utils.common_initialisation import (
            CommonInitialisation as Common,
        )
        common = Common(
            uninit=["project_db", "setting_db", "r2", "spreadsheet"], 
            exclude_init_confirm=True
            )
        ref_linker = common.ref_linker
        if ref_linker:
            linker_doc = ref_linker.get().to_dict()
            if linker_doc and linker_doc.get("linker", "0") == "1":
                self.linker_doc = linker_doc
                return
        self.linker_doc = None
    
    def trace_to_parent(self, child):
        child = str(child)
        parent = self.linker_doc["backward_ref"].get(child, None)
        return int(parent) if parent is not None else None
    
    def trace_to_child(self, parent):
        parent = str(parent)
        child_str = self.linker_doc["foward_ref"].get(parent, None)
        child = child_str.split("|") if child_str is not None else None
        child = [int(i) for i in child] if child is not None else None
        return child
    
    def find_children(self):
        children_set = set()
        for child in self.linker_doc["backward_ref"].keys():
            children_set.add(int(child))
        return children_set
    
class MakeLinker:
    def __init__(self):
        pass
        
    @staticmethod
    def restructure_linker(linker_dict):
        linker_dict_restructure = {
            "linker": "1",
            "foward_ref": {},
            "backward_ref": {}
        }
        for k, v in linker_dict.items():
            linker_dict_restructure["foward_ref"][str(k)] = "|".join([str(i) for i in v])
        for k, v in linker_dict.items():
            for sub_v in v:
                linker_dict_restructure["backward_ref"][str(sub_v)] = str(k)
        return linker_dict_restructure
