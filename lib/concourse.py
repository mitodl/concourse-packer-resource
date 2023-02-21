# stdlib
import json
import os
import sys
from typing import Any, Dict, List, Optional

# local
from lib import packer
from lib.io import read_value_from_file
from lib.log import log, log_pretty

# =============================================================================
#
# private io functions
#
# =============================================================================


# =============================================================================
# _get_working_dir_path
# =============================================================================
def _get_working_dir_path() -> str:
    return sys.argv[1]


# =============================================================================
# _get_working_dir_file_path
# =============================================================================
def _get_working_dir_file_path(working_dir_path: str, file_name: str) -> str:
    return os.path.join(working_dir_path, file_name)


# =============================================================================
# _read_params
# =============================================================================
def _read_params(stream=sys.stdin) -> dict:
    inputs: dict = json.load(stream)
    return inputs["params"]


# =============================================================================
# _write_payload
# =============================================================================
def _write_payload(payload: Any, stream=sys.stdout) -> None:
    json.dump(payload, stream)


# =============================================================================
# _process_env_var_files
# =============================================================================
def _process_env_var_files(env_var_files: dict, working_dir: str) -> None:
    for var_name, file_path in env_var_files.items():
        os.environ[var_name] = read_value_from_file(file_path, working_dir=working_dir)


# =============================================================================
# _create_concourse_metadata_from_build_manifest_artifact
# =============================================================================
def _create_concourse_metadata_from_build_manifest_artifact(
    artifact_name: str, artifact_index: str, artifact: dict
) -> List[dict]:
    metadata = []
    for key, value in artifact.items():
        metadata.append(
            {"name": f"{artifact_name}::{artifact_index}::{key}", "value": value}
        )
    return metadata


# =============================================================================
# _create_concourse_out_payload_from_packer_build_manifest
# =============================================================================
def _create_concourse_out_payload_from_packer_build_manifest(
    build_manifest: dict,
) -> dict:
    out_payload = {"version": None, "metadata": []}
    for artifact_name, artifacts in build_manifest["artifacts"].items():
        for artifact_index, artifact in artifacts.items():
            # use first artifact as version
            if (not out_payload["version"]) and (artifact_index == "0"):
                out_payload["version"] = {"id": artifact["id"]}
            # add artifact details as metadata
            out_payload["metadata"].extend(
                _create_concourse_metadata_from_build_manifest_artifact(
                    artifact_name, artifact_index, artifact
                )
            )
    return out_payload


# =============================================================================
#
# public lifecycle functions
#
# =============================================================================
def do_check_cmd() -> None:
    # not implemented
    _write_payload([{"id": "0"}])


def do_in_cmd() -> None:
    # not implemented
    _write_payload({"version": {"id": "0"}})


def out_cmd() -> None:
    # read the concourse input payload
    params: dict = _read_params()
    # get packer objective from payload
    objective: str = params.get("objective", "validate")
    # get force setting from payload
    force_enabled: bool = params.get("force", False)
    # get debug setting from payload
    debug_enabled: bool = params.get("debug", False)
    # get the template file path from the payload
    template_file_path: str = params["template"]
    # get the working dir path from the input
    working_dir_path: str = _get_working_dir_path()
    # set env vars, if provided
    if "env_vars" in params:
        os.environ.update(params["env_vars"])
    # instantiate the var file paths and vars lists
    var_file_paths: Optional[List[str]] = None
    variables: Optional[Dict] = None
    vars_from_files: Optional[Dict] = None
    only: Optional[List[str]] = None
    excepts: Optional[List[str]] = None
    # add var file paths, if provided
    if "var_files" in params:
        var_file_paths = params["var_files"]
    # add vars, if provided
    if "vars" in params:
        variables = params["vars"]
    # add vars from files, if provided
    if "vars_from_files" in params:
        vars_from_files = params["vars_from_files"]
    # set env vars from files, if provided
    if "env_vars_from_files" in params:
        _process_env_var_files(params["env_vars_from_files"], working_dir_path)
    # set only or except, if either provided
    if "only" in params:
        only = params["only"]
    elif "excepts" in params:
        excepts = params["excepts"]
    # dump details, if debug enabled
    if debug_enabled:
        log("var_file_paths:")
        log_pretty(var_file_paths)
        log("vars:")
        log_pretty(variables)
    # dump the current packer version
    packer.version()
    # initialize templates and configs
    packer.init(working_dir_path, template_file_path)
    # initialize output payload (these values also used for validation)
    output_payload = {"version": {"id": "0"}, "metadata": []}
    # execute desired packer objective
    if objective == "validate":
        # validate the template (directory)
        packer.validate(
            working_dir_path,
            template_file_path,
            var_file_paths=var_file_paths,
            template_vars=variables,
            vars_from_files=vars_from_files,
            only=only,
            excepts=excepts,
            debug=debug_enabled,
        )
        # check formatting
        packer.format_packer_cmd(working_dir_path, template_file_path)
    elif objective == "build":
        # build the template, getting the build manifest back
        build_manifest = packer.build(
            working_dir_path,
            template_file_path,
            var_file_paths=var_file_paths,
            template_vars=variables,
            vars_from_files=vars_from_files,
            only=only,
            excepts=excepts,
            debug=debug_enabled,
            force=force_enabled,
        )
        # dump build manifest, if debug
        if debug_enabled:
            log("build manifest:")
            log_pretty(build_manifest)
        # convert the manifest into a concourse output payload
        output_payload = _create_concourse_out_payload_from_packer_build_manifest(
            build_manifest
        )
    else:
        raise RuntimeError('Invalid value for "objective" parameter')
    # dump output payload, if debug
    if debug_enabled:
        log("output payload:")
        log_pretty(output_payload)
    # write out the payload
    _write_payload(output_payload)
