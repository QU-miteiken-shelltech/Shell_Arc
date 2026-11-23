import shutil

from shellarc_msk.mskut.path_solver import MSKUT_PathSolver
from shellarc_msk.mskut.on_ram_data import MSKUT_OnRamData, MSKUT_OnRamMmap, MSKUT_OnRamTmpData
from shellarc_msk.mskdf.diff_solver import MSKDF_DiffSolver
from shellarc_msk.mskob.adress_obj import MSK_Address
from shellarc_msk.mskob.entity_obj import MSK_Entity
from shellarc_msk.mskob.containercoll_obj import MSK_ContainerCollection

def merge_container_coll(field_name: str,
                         incoming_container_bin: bytearray,
                         incoming_address_bin: bytearray,
                         incoming_address_offset_bin: bytearray):
    mskfs_pathsolver = MSKUT_PathSolver()
    field_bin_file = mskfs_pathsolver.mskfs_space / f".msk_container_{field_name}"
    backup_dir = mskfs_pathsolver.mskfs_backup
    shutil.copy2(src=field_bin_file, dst=backup_dir)
    MSKUT_OnRamTmpData.adress_bin = incoming_address_bin
    MSKUT_OnRamTmpData.adress_offset_bin = incoming_address_offset_bin

    container_bin_diff_solver = MSKDF_DiffSolver(
        ours=MSKUT_OnRamMmap.container_bins[field_name],
        theirs=incoming_container_bin,
        chunk_size=48
    )
    parallel_diffs = container_bin_diff_solver.parallel_diff(
        ignore_exceeding="theirs"
    )
    parallel_diff_entities = [
        MSK_Entity(entity_chunk=b[1], on_ram_data_cls=MSKUT_OnRamTmpData) 
        for b in parallel_diffs
    ]
    excessive_diffs = container_bin_diff_solver.excessive_diff(
        exceeding="theirs"
    )
    excessive_diff_entities = [
        MSK_Entity(entity_chunk=b, on_ram_data_cls=MSKUT_OnRamTmpData) 
        for b in excessive_diffs
    ]
    diff_entities = parallel_diff_entities + excessive_diff_entities
    coll = MSK_ContainerCollection(field_name=field_name)
    for entity in diff_entities:
        entity_container_index = entity.container_index
        entity_value = entity.address.value
        entity_type = entity.address.type
        entity_prop = entity.prop
        new_address = MSK_Address(
            adress_type=entity_type,
            adress_value=entity_value
        )
        coll.write_entity(
            container_index=entity_container_index,
            prop=entity_prop,
            adress=new_address,
            do_override=True
        )
    MSKUT_OnRamTmpData.clear_all()