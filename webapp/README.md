# Keip Integration Route App

A Python web server that implements the following endpoints:
- `/webhook`: A [lambda controller from the Metacontroller API](https://metacontroller.github.io/metacontroller/concepts.html#lambda-controller).
- `/route`: Deploys a route from an XML file.

The webhook contains two endpoints, `/webhook/sync` and `/webhook/addons/certmanager/sync`.
  - `/webhook/sync`: The core logic that creates a `Deployment` from `IntegrationRoute` resources.
  - `/webhook/addons/certmanager/sync`: An add-on that creates
    a [cert-manager.io/v1.Certificate](https://cert-manager.io/docs/reference/api-docs/#cert-manager.io/v1.Certificate)
    based on annotations in an `IntegrationRoute`.

  The format for the request and response JSON payloads can be
  seen [here](https://metacontroller.github.io/metacontroller/api/compositecontroller.html#sync-hook)

## Deployment

This web server is designed to be run as a service within a Kubernetes cluster. It is intended to be used with [Metacontroller](https://metacontroller.github.io/metacontroller/), which will call the `/webhook` endpoint to manage `IntegrationRoute` custom resources.

The `/route` endpoint is provided for convenience to deploy routes from XML files.

## Developer Guide

Requirements:

- Python v3.11

### Create the Python virtual environment

```shell
make venv
```

You should now have a [virtual environment](https://docs.python.org/3.11/library/venv.html) installed in `./venv` that
includes all the dependencies required by the project.
You can point your IDE of choice to `./venv/bin/python3` to enable its Python toolchain for this project.

### Run Tests

```shell
make test
```

### Run the Dev Server

```shell
make start-dev-server
```

### Code Formatting and Linting

To keep diffs small, we use the [Black](https://black.readthedocs.io/en/stable/index.html) formatter (included as part
of the `venv` install). [See here](https://black.readthedocs.io/en/stable/integrations/editors.html) for instructions on
integrating it with your editor.

```shell
make format
make lint
```

### Precommit Task

For convenience, there is a `precommit` task that runs unit tests, formatting, and linting. This task should be run
prior to every commit, as such you are encouraged to add it as
a [pre-commit git hook](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks).

```shell
make precommit
```

### Docker

To build the Docker image, run:

```shell
make build
```

To run the Docker container:

```shell
make run-container
```

### Windows Development

There are Windows-compatible equivalents for most of the `make` commands listed above, prefixed with `win-` (
e.g. `test` -> `win-test`). See the [Makefile](Makefile) for more details.