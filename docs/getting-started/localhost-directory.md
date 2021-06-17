# The localhost directory

[`localhost/`][localhost] contains the code and artifacts that make possible running Benefits locally.

## [`data/`][localhost/data]

* `client.json`: sample configuration for the Benefits client
* `server.json`: sample configuration for a local Eligibility Verification server, including users and eligibility

## [`keys/`][localhost/keys]

* `client.key` and `client.pub`: sample encryption keypair for the Benefits client
* `server.key` and `server.pub`: sample encryption keypair for the local Eligibility Verification server

## [`server/`][localhost/server]

* Simple Flask app implementing Eligiblity Verification server

## [`Dockerfile.dev`][localhost/Dockerfile.dev]

* Docker image built on the [Benefits Docker image](../Dockerfile) used with
[VS Code devcontainers](https://code.visualstudio.com/docs/remote/containers).

[localhost]: https://github.com/cal-itp/benefits/tree/dev/localhost
[localhost/data]: https://github.com/cal-itp/benefits/tree/dev/localhost/data
[localhost/keys]: https://github.com/cal-itp/benefits/tree/dev/localhost/keys
[localhost/server]: https://github.com/cal-itp/benefits/tree/dev/localhost/server
[localhost/Dockerfile.dev]: https://github.com/cal-itp/benefits/tree/dev/localhost/Dockerfile.dev