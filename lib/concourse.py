# stdlib
import json
import os
import sys
from typing import Any, Dict, List, Optional

# local
import lib.packer
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
def _get_working_dir_file_path(
        working_dir_path: str, file_name: str) -> str:
    return os.path.join(working_dir_path, file_name)


# =============================================================================
# _read_payload
# =============================================================================
def _read_payload(stream=sys.stdin) -> Any:
    return json.load(stream)


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
        os.environ[var_name] = (
            read_value_from_file(file_path, working_dir=working_dir))


# =============================================================================
# _create_concourse_metadata_from_build_manifest_artifact
# =============================================================================
def _create_concourse_metadata_from_build_manifest_artifact(
        artifact_name: str,
        artifact_index: str,
        artifact: dict) -> List[dict]:
    metadata = []
    for key, value in artifact.items():
        metadata.append({
            'name': f"{artifact_name}::{artifact_index}::{key}",
            'value': value
        })
    return metadata


# =============================================================================
# _create_concourse_out_payload_from_packer_build_manifest
# =============================================================================
def _create_concourse_out_payload_from_packer_build_manifest(
        build_manifest: dict) -> dict:
    out_payload = {
        'version': None,
        'metadata': []
    }
    for artifact_name, artifacts in build_manifest['artifacts'].items():
        for artifact_index, artifact in artifacts.items():
            # use first artifact as version
            if (not out_payload['version']) and (artifact_index == '0'):
                out_payload['version'] = {
                    'id': artifact['id']
                }
            # add artifact details as metadata
            out_payload['metadata'].extend(
                _create_concourse_metadata_from_build_manifest_artifact(
                    artifact_name, artifact_index, artifact))
    return out_payload


# =============================================================================
#
# public lifecycle functions
#
# =============================================================================

def do_check() -> None:
    # not implemented
    _write_payload([{'id': '0'}])


def do_in() -> None:
    # not implemented
    _write_payload({
        "version": {
            'id': '0'
        }
    })


def do_out() -> None:
    # read the concourse input payload
    input_payload = _read_payload()
    # get force setting from payload
    force_enabled: bool = input_payload['params'].get('force', False)
    # get debug setting from payload
    debug_enabled: bool = input_payload['params'].get('debug', False)
    # get the template file path from the payload
    template_file_path: str = input_payload['params']['template']
    # get the working dir path from the input
    working_dir_path = _get_working_dir_path()
    # set env vars, if provided
    if 'env_vars' in input_payload['params']:
        os.environ.update(input_payload['params']['env_vars'])
    # instantiate the var file paths and vars lists
    var_file_paths: Optional[List[str]] = None
    vars: Optional[Dict] = None
    vars_from_files: Optional[Dict] = None
    # add var file paths, if provided
    if 'var_files' in input_payload['params']:
        var_file_paths = input_payload['params']['var_files']
    # add vars, if provided
    if 'vars' in input_payload['params']:
        vars = input_payload['params']['vars']
    # add vars from files, if provided
    if 'vars_from_files' in input_payload['params']:
        vars_from_files = input_payload['params']['vars_from_files']
    # set env vars from files, if provided
    if 'env_vars_from_files' in input_payload['params']:
        _process_env_var_files(
            input_payload['params']['env_vars_from_files'],
            working_dir_path)
    # dump details, if debug enabled
    if debug_enabled:
        log('var_file_paths:')
        log_pretty(var_file_paths)
        log('vars:')
        log_pretty(vars)
    # dump the current packer version
    lib.packer.version()
    # validate the template
    lib.packer.validate(
        working_dir_path,
        template_file_path,
        var_file_paths=var_file_paths,
        vars=vars,
        vars_from_files=vars_from_files,
        debug=debug_enabled)
    # build the template, getting the build manifest back
    build_manifest = lib.packer.build(
        working_dir_path,
        template_file_path,
        var_file_paths=var_file_paths,
        vars=vars,
        vars_from_files=vars_from_files,
        debug=debug_enabled,
        force=force_enabled)
    # dump build manifest, if debug
    if debug_enabled:
        log('build manifest:')
        log_pretty(build_manifest)
    # convert the manifest into a concourse output payload
    output_payload = _create_concourse_out_payload_from_packer_build_manifest(
        build_manifest)
    # dump output payload, if debug
    if debug_enabled:
        log('output payload:')
        log_pretty(output_payload)
    # write out the payload
    _write_payload(output_payload)
