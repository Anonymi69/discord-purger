# Security Policy

## Overview

This application is an open-source Discord utility designed for managing and deleting direct messages across accounts selected by the user.

The source code is fully public and intended to be audited. Users are encouraged to review the implementation, dependencies, and network activity before use.

---

## Network Activity

This application communicates exclusively with the official Discord API endpoints.

- No third-party APIs are used
- No telemetry or analytics services are included
- No external servers are contacted
- No background data collection occurs

All outbound traffic is strictly limited to Discord API requests required for functionality.

---

## Authentication Handling

This application requires Discord authentication to perform actions on behalf of the user.

To improve usability, the application may attempt to detect locally available Discord session information already present on the user's device.

Important details:

- All detection and processing occurs locally on the user's machine
- No credentials or tokens are transmitted externally
- No authentication data is logged, stored remotely, or shared
- Only account identifiers (e.g., usernames) are displayed in the interface
- Tokens (if present in memory) are used only for local API authentication


---

## File System Behavior

This application does not:

- Drop additional files outside of its installation directory
- Install services, drivers, or persistence mechanisms
- Modify system-level configuration or registry entries
- Create hidden background processes

All required assets are bundled within the application.

---

## Embedded Assets

Static assets (such as the application icon) are embedded directly within the codebase using encoded data formats (e.g., Base64).

- No external asset downloads occur at runtime
- No separate icon or resource files are required
- This is purely for packaging convenience

---

## Data Handling

This application does not:

- Exfiltrate user data
- Send personal information to external servers
- Store sensitive authentication data persistently
- Log private messages or account content externally

All processing is performed locally on the user’s device.

---

## What This Application Does NOT Do

This project explicitly does NOT:

- Steal or transmit Discord tokens
- Harvest browser credentials or passwords
- Access unrelated system data
- Run hidden background persistence tasks
- Download or execute remote code
- Perform unauthorized data collection

---

## Security Transparency

Users are encouraged to:

- Inspect the full source code
- Monitor network traffic during use
- Run the application from source when possible
- Verify all dependencies independently

Recommended tools for verification:
- Network monitors (e.g., Wireshark)
- Process inspectors
- Dependency scanners
- Online malware analysis tools

---

## False Positives

Security software may incorrectly flag this application due to:

- Discord API automation behavior
- Authentication usage patterns
- Bundled executable packaging
- Electron/Node.js runtime characteristics

These are expected in tools that interact heavily with Discord functionality.

---

## Reporting Security Issues

If you discover a potential vulnerability or unexpected behavior:

- Open an issue on the repository
- Provide reproduction steps where possible
- Do not publicly share sensitive tokens or credentials

---

## Responsible Use

Users are responsible for ensuring compliance with:

- Discord Terms of Service
- Local laws and regulations
- Platform usage policies

This project is provided for educational and utility purposes only.
