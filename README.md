# Concourse Packer Resource

Based off the cycloidio/concourse-packer-resource fork of Snapkitchen/concourse-packer-resource.

A [concourse-ci](https://concourse-ci.org) resource for building images via [Packer](https://www.packer.io).

## behaviour

### `check`: not implemented

### `in`: not implemented

### `out`: validate a template, or template and config directory, or build a new instance artifact

**parameters**

- `template`: _required_. the path to the packer template file or directory.

- `objective`: _optional_. the packer objective for the template; either `validate` or `build` triggers corresponding additional actions. default: `validate`

- `env_vars`: _optional_. dict of variables to set in the environment.

- `env_vars_from_files`: _optional_. dict of vars and file paths to set in the environment.

- `var_files`: _optional_. the list of paths to [external JSON variable file(s)](https://www.packer.io/docs/templates/user-variables.html).

- `vars`: _optional_. dict of explicit packer variable key/value pairs.

- `vars_from_files`: _optional_. dict of vars and file paths to use as their value.

- `only`: _optional_. list of sources on which to perform the action (mutually exclusive with `excepts`)

- `excepts`: _optional_. list of sources on which to not perform the action (mutually exclusive with `only`)

- `force`: _optional_. set to `true` to enable the [force](https://packer.io/docs/commands/build.html#force) option during a packer build. default: `false`

- `debug`: _optional_. set to `true` to dump argument values and parsed output. **may result in leaked credentials**. default: `false`

the id of the first artifact produced will be used as the version, with the full artifact details in the output metadata

**note**: in an effort to prevent credentials leaking to logs, the full packer command line will not be printed on failure -- however, you should still mark any relevant variables as _sensitive variables_ in the packer template to prevent packer from printing them in log output

the packer executable will have a working directory of the concourse input directory, so file paths can be relative to resources, or absolute paths

## Example

```yaml
resource_types:
- name: packer
  type: docker-image
  source:
    repository: snapkitchen/concourse-packer-resource
    tag: 1.4.3

resources:
- name: build-ami
  type: packer

jobs:
- name: my-ami
  plan:
  - get: my-ami-template
  - get: role-credentials
  - put: build-ami
    params:
      template: my-ami-template/template.json
      objective: build
      var_files:
      - my-ami-template/my-vars.json
      env_vars:
        AWS_DEFAULT_REGION: ((aws_region))
      env_vars_from_files:
        AWS_ACCESS_KEY_ID: role-credentials/access-key-id
        AWS_SECRET_ACCESS_KEY: role-credentials/secret-access-key
        AWS_SESSION_TOKEN: role-credentials/session-token
      vars:
        environment: dev
        package_version: 1.2.3
      vars_from_files:
        commit_ref: my-ami-template/.git/short_ref
```
