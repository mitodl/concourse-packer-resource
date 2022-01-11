# stdlib
import subprocess
from typing import List

# local
from lib.io import read_value_from_file
from lib.log import log, log_pretty


# =============================================================================
#
# constants
#
# =============================================================================

PACKER_BIN_FILE_PATH = 'packer'


# =============================================================================
#
# private utility functions
#
# =============================================================================

# =============================================================================
# _parse_packer_machine_readable_output_line
# =============================================================================
def _parse_packer_machine_readable_output_line(output_line: str) -> dict:
    # machine readable format
    # from https://www.packer.io/docs/commands/index.html
    parsed_line = None
    if output_line:
        message_item: dict = {
            'timestamp': None,
            'target': None,
            'type': None,
            'data': []
        }
        # split each line on commas
        line_tokens: list = output_line.split(',')
        for i, line_token in enumerate(line_tokens):
            # assign payload fields based on token number
            if i == 0:
                message_item['timestamp'] = line_token
            elif i == 1:
                message_item['target'] = line_token
            elif i == 2:
                message_item['type'] = line_token
            elif i > 2:
                # strip trailing newline from data
                message_item['data'].append(line_token.rstrip('\n'))
        parsed_line = message_item
    return parsed_line


# =============================================================================
# _format_packer_machine_readable_output_line
# =============================================================================
def _format_packer_machine_readable_output_line(
    timestamp: str,
    target: str,
    type: str,
    data: str,
    subtype=None
) -> str:
    # most messages won't have a target which means it's global
    if not target:
        target = 'global'
    # consistent padding for the 'version' types
    if type.startswith('version'):
        type = f"{type:16}"
    # replace the packer comma
    data = data.replace('%!(PACKER_COMMA)', ',')
    if subtype:
        return f"{timestamp} | {target} | {type} | {subtype:8} | {data}"
    else:
        return f"{timestamp} | {target} | {type} | {data}"


# =============================================================================
# _print_parsed_packer_machine_readable_output_line
# =============================================================================
def _print_parsed_packer_machine_readable_output_line(
        parsed_line: dict) -> None:
    if parsed_line:
        if len(parsed_line['data']) > 0:
            subtype = None
            # check for subtype
            if parsed_line['data'][0] in ['say', 'error', 'message']:
                # pop found subtype from the parsed line
                subtype = parsed_line['data'].pop(0)
            for item in parsed_line['data']:
                # split on \\n
                item_lines = item.split('\\n')
                for item_line in item_lines:
                    log(_format_packer_machine_readable_output_line(
                        parsed_line['timestamp'],
                        parsed_line['target'],
                        parsed_line['type'],
                        item_line,
                        subtype=subtype))


# =============================================================================
# _parse_packer_parsed_output_for_build_manifest
# =============================================================================
def _parse_packer_parsed_output_for_build_manifest(
        parsed_output: List[dict]) -> dict:
    manifest = {'artifacts': {}}
    # create collection of targets
    targets = {}
    for parsed_item in parsed_output:
        if parsed_item['target']:
            target_name = parsed_item['target']
            if target_name not in targets:
                targets[target_name] = []
            del parsed_item['target']
            targets[target_name].append(parsed_item)
    # iterate on targets
    for target in targets.keys():
        # log('target:')
        # log_pretty(target)
        # split into artifacts
        target_artifacts = {}
        for target_item in targets[target]:
            if target_item['type'] == 'artifact':
                # first index of data will be the artifact number
                artifact_number = target_item['data'][0]
                # second index of data will be the artifact key
                artifact_key = target_item['data'][1]
                # skip adding the 'end' key
                if artifact_key == 'end':
                    continue
                # third index of data will be the artifact value, if present
                if len(target_item['data']) > 2:
                    artifact_value = target_item['data'][2]
                else:
                    artifact_value = None
                # create the target artifact dict, if missing
                if artifact_number not in target_artifacts:
                    target_artifacts[artifact_number] = {}
                # assign the artifact key and value
                target_artifacts[artifact_number][artifact_key] = \
                    artifact_value
        manifest['artifacts'][target] = target_artifacts
    return manifest


# =============================================================================
#
# private exe functions
#
# =============================================================================

# =============================================================================
# _packer
# =============================================================================
def _packer(*args: str, input=None, working_dir=None) -> List[dict]:
    # runs packer bin with forced machine readable output
    process_args = [
        PACKER_BIN_FILE_PATH,
        '-machine-readable',
        *args
    ]
    parsed_lines = []
    # use Popen so we can read lines as they come
    with subprocess.Popen(
            process_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # redirect stderr to stdout
            bufsize=1,
            universal_newlines=True,
            stdin=input,
            cwd=working_dir) as pipe:
        for line in pipe.stdout:
            if 'fmt' in args:
                # determine log level
                log_level = 'warning' if 'fmt' in args else 'info'
                # directly log the output
                log(f"global | ui | {log_level} | {line.rstrip()}")
            else:
                # parse the machine readable output as it arrives
                parsed_line = _parse_packer_machine_readable_output_line(line)
                parsed_lines.append(parsed_line)
                _print_parsed_packer_machine_readable_output_line(parsed_line)
    if pipe.returncode != 0:
        # args are masked to prevent credentials leaking
        raise subprocess.CalledProcessError(
            pipe.returncode, [PACKER_BIN_FILE_PATH])
    return parsed_lines


# =============================================================================
#
# public packer functions
#
# =============================================================================

# =============================================================================
# version
# =============================================================================
def version() -> None:
    # execute version command
    _packer('version')


# =============================================================================
# init
# =============================================================================
def init(
        working_dir_path: str,
        template_file_path: str) -> None:
    # execute init command
    _packer(
        'init',
        template_file_path,
        working_dir=working_dir_path)


# =============================================================================
# format
# =============================================================================
def format(
        working_dir_path: str,
        template_file_path: str) -> None:
    # execute format command
    _packer(
        'fmt',
        '-check',
        '-diff',
        template_file_path,
        working_dir=working_dir_path)


# =============================================================================
# validate
# =============================================================================
def validate(
        working_dir_path: str,
        template_file_path: str,
        var_file_paths: List[str] = None,
        vars: dict = None,
        vars_from_files: dict = None,
        only: List[str] = None,
        excepts: List[str] = None,
        syntax_only: bool = False,
        debug: bool = False) -> None:
    packer_command_args = []
    # add any specified var file paths
    if var_file_paths:
        for var_file_path in var_file_paths:
            packer_command_args.append(f"-var-file={var_file_path}")
    # add any specified vars
    if vars:
        for var_name, var_value in vars.items():
            packer_command_args.append(f"-var={var_name}={var_value}")
    # add any vars from files
    if vars_from_files:
        for var_name, file_path in vars_from_files.items():
            var_value = \
                read_value_from_file(
                    file_path,
                    working_dir=working_dir_path)
            packer_command_args.append(f"-var={var_name}={var_value}")
    # only build specified sources
    if only:
        packer_command_args.append(f"-only={','.join(only)}")
    # build all sources except those specified
    elif excepts:
        packer_command_args.append(f"-except={','.join(excepts)}")
    # optionally check only syntax
    if syntax_only:
        packer_command_args.append('-syntax-only')
    # dump args on debug
    if debug:
        log('validate args:')
        log_pretty(packer_command_args)
    # execute validate command
    _packer(
        'validate',
        *packer_command_args,
        template_file_path,
        working_dir=working_dir_path)


# =============================================================================
# build
# =============================================================================
def build(
        working_dir_path: str,
        template_file_path: str,
        var_file_paths: List[str] = None,
        vars: dict = None,
        vars_from_files: dict = None,
        only: List[str] = None,
        excepts: List[str] = None,
        debug: bool = False,
        force: bool = False) -> dict:
    packer_command_args = []
    # add any specified var file paths
    if var_file_paths:
        for var_file_path in var_file_paths:
            packer_command_args.append(f"-var-file={var_file_path}")
    # add any specified vars
    if vars:
        for var_name, var_value in vars.items():
            packer_command_args.append(f"-var={var_name}={var_value}")
    # add any vars from files
    if vars_from_files:
        for var_name, file_path in vars_from_files.items():
            var_value = \
                read_value_from_file(
                    file_path,
                    working_dir=working_dir_path)
            packer_command_args.append(f"-var={var_name}={var_value}")
    # only build specified sources
    if only:
        packer_command_args.append(f"-only={','.join(only)}")
    # build all sources except those specified
    elif excepts:
        packer_command_args.append(f"-except={','.join(excepts)}")
    # add force if requested
    if force:
        packer_command_args.append("-force")
    # dump args on debug
    if debug:
        log('build args:')
        log_pretty(packer_command_args)
    # execute build command
    packer_command_result = _packer(
        'build',
        *packer_command_args,
        template_file_path,
        working_dir=working_dir_path)
    # get build manifest from output
    packer_build_manifest = \
        _parse_packer_parsed_output_for_build_manifest(packer_command_result)
    # return the manifest
    return packer_build_manifest
