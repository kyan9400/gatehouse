# Security policy

## Supported versions

| Version | Supported |
| --- | --- |
| `0.1.x` | Yes |

## Reporting a vulnerability

Please do not open a public issue for a security vulnerability. Use GitHub's private security advisory flow for this repository and include reproduction steps, affected endpoints, and any suggested mitigation. We will acknowledge reports within seven days.

Gatehouse is a reference implementation, not a replacement for an identity provider. Before production use, configure an external identity provider, rotate `GATEHOUSE_API_KEY`, use PostgreSQL with encrypted transport, and place the service behind a private network boundary.
