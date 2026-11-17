# Security and private configuration

Do not publish credentials, SEC contact details, local databases or raw local logs in an issue or pull request. Keep configuration in ignored `.env` files. Use synthetic examples when reporting a problem.

For a suspected vulnerability, use GitHub's private vulnerability reporting feature if enabled. Public issue reports should omit sensitive details and reproduction data until a private reporting route has been agreed.

The current app is a local, single-user research workspace. A publicly hosted interactive service requires its own deployment validation, request/resource limits and server configuration. The API deliberately exposes no ingestion or administration endpoint. Public project pages and static reports do not execute the Python service.
