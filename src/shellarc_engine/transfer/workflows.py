import importlib
import sys
from pathlib import Path

from shellarc_engine.config.read_config import ReadClientConfig
from shellarc_msk.mskut.path_solver import MSKUT_PathSolver

def available_actions() -> list[str]:
    call_actions = ReadClientConfig.get_config_item("call_actions")
    return [x for x in call_actions]

def _run_workflow_func(
        file_path: str, 
        func_name: str,
        *args, **kwargs):
    path = Path(file_path).resolve()
    module_name = path.stem
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Read file failed : {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    func = getattr(module, func_name)
    if not func:
        raise ValueError(f"Designated workflow function ({func_name}) not found")
    return func(*args, **kwargs)

def run_workflow(action: str, *args, **kwargs):
    call_actions = ReadClientConfig.get_config_item("call_actions")
    call_action = call_actions.get(action, None)
    if call_action is None:
        raise ValueError("Unregistered action is not callable")
    workflow_file_path = call_action.get("filepath", None)
    workflow_func_name = call_action.get("function", None)
    if workflow_file_path is None or workflow_func_name is None:
        raise ValueError(f"'filepath' and/or 'function' of workflow action {action} is not defined properly")
    workflow_file_path = MSKUT_PathSolver().mskfs_client / "workflows" / str(workflow_file_path)
    if not workflow_file_path.exists():
        raise ValueError(f"Designated workflow file ({workflow_file_path}) not found")
    _run_workflow_func(
        workflow_file_path,
        workflow_func_name,
        *args, **kwargs
    )
    