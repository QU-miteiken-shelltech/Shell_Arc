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
                         incoming_address_offset_bin: bytearray
                         ) -> int:
    # return 0: have diff / 1: no diff
    print(f"[msk_merge] start: field_name={field_name}")
    mskfs_pathsolver = MSKUT_PathSolver()
    backup_dir = mskfs_pathsolver.mskfs_backup
    print("[msk_merge] creating backups")
    for src_file in [mskfs_pathsolver.mskfs_space / f".msk_container_{field_name}",
                     mskfs_pathsolver.mskfs_space / f".msk_adress",
                     mskfs_pathsolver.mskfs_space / f".msk_adress_offset"]:
           shutil.copy2(src=src_file, dst=backup_dir)
    print("[msk_merge] backups created")

    container_bin_diff_solver = MSKDF_DiffSolver(
        ours=MSKUT_OnRamMmap.container_bins[field_name],
        theirs=incoming_container_bin,
        chunk_size=48
    )
    print("[msk_merge] checking for differences")
    if container_bin_diff_solver.identity_diff():
        print("[msk_merge] no differences found")
        return 1
    
    MSKUT_OnRamTmpData.adress_bin = incoming_address_bin
    MSKUT_OnRamTmpData.adress_offset_bin = incoming_address_offset_bin
    print("[msk_merge] calculating parallel differences")
    parallel_diffs = container_bin_diff_solver.parallel_diff(
        ignore_exceeding="theirs"
    )
    print(f"[msk_merge] parallel differences found: {len(parallel_diffs)}")
    parallel_diff_entities = [
        MSK_Entity(entity_chunk=b[1], on_ram_data_cls=MSKUT_OnRamTmpData) 
        for b in parallel_diffs
    ]
    print("[msk_merge] calculating excessive differences")
    excessive_diffs = container_bin_diff_solver.excessive_diff(
        exceeding="theirs"
    )
    print(f"[msk_merge] excessive differences found: {len(excessive_diffs)}")
    excessive_diff_entities = [
        MSK_Entity(entity_chunk=b, on_ram_data_cls=MSKUT_OnRamTmpData) 
        for b in excessive_diffs
    ]
    diff_entities = parallel_diff_entities + excessive_diff_entities
    print(f"[msk_merge] applying entity differences: {len(diff_entities)}")
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
    print("[msk_merge] clearing temporary data")
    MSKUT_OnRamTmpData.clear_all()
    print("[msk_merge] merge complete")
    return 0
