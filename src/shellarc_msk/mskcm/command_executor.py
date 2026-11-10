from ast import literal_eval

from shellarc_msk.mskcm.command_enums import MSKCM_OrderEnum

def exec_mskcm(cmds):
    cmds_list = cmds.split(";")
    params = {}
    previous_rtn = None
    for i, cmd in enumerate(cmds_list):
        cmd = cmd.strip()
        if not cmd:
            continue
        elements = cmd.split(" ")
        order = elements[0].strip()
        if order == "CFG":
            params[elements[1].strip()] = literal_eval(elements[2].strip())
        elif order == "TGT":
            params["target"] = [x.strip() for x in elements[1:]]
        elif order == "PYE":
            previous_rtn = eval(elements[1].strip())
            params = {}
        else:
            order = getattr(MSKCM_OrderEnum, order, None)
            if order is None:
                raise ValueError("Invalid MSK Command")
            order_func = globals()[order]
            if previous_rtn is None:
                previous_rtn = order_func(**params)
            else:
                previous_rtn = order_func(previous_rtn, **params)
            params = {}
        print(previous_rtn)

    return previous_rtn


        