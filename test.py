from pathlib import Path

from shellarc_msk.mskob.containercoll_obj import MSK_ContainerCollection

def test():
    txt_dict = {}
    for entity in MSK_ContainerCollection(field_name="Cut").entities_iter():
        if entity.container_index in txt_dict:
            txt_dict[entity.container_index].append(f"{entity.prop.prop_name} = {entity.address.value}")
        else:
            txt_dict[entity.container_index] = [f"{entity.prop.prop_name} = {entity.address.value}"]

    write_txt = ""
    for k,v in txt_dict.items():
        write_txt += "\n".join(v)
        write_txt += "\n\n"

    with open(Path(__file__).resolve().parent / "test_ascii.txt", "w", encoding="utf-8") as f:
        f.write(write_txt)

    print("END")

test()