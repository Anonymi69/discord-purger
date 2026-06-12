# Security Policy

## Overview

This application is an open-source Discord utility for deleting your own direct messages. The source code is fully public and intended to be audited. Users are encouraged to review the implementation, dependencies, and network activity before use.

---

## Token Handling

This version of the application **does not perform any form of token extraction**.

Previous versions attempted to detect Discord session tokens from local browser storage or process memory. That approach has been completely removed. The current design:

- Presents a manual login screen on startup where the user pastes their own token
- Validates the token against `GET /users/@me` before proceeding
- Never stores, logs, or writes the token to disk
- Keeps the token masked on screen at all times — it cannot be revealed, copied, or cut through the UI
- Uses the token in memory solely to make Discord API requests during the session
- Discards the token when the application is closed

---

## Network Activity

This application communicates exclusively with official Discord API endpoints (`discord.com/api/v9` and `cdn.discordapp.com`).

- No third-party APIs are used
- No telemetry or analytics of any kind
- No external servers are contacted beyond Discord's own CDN and API
- No background data collection occurs

All outbound traffic is strictly limited to:
- Token validation on login
- Loading your DM channel list
- Fetching user avatars from Discord's CDN
- Deleting your own messages via the Discord API

---

## File System Behavior

This application does not:

- Write tokens, credentials, or session data to disk
- Drop additional files outside its working directory
- Install services, drivers, or persistence mechanisms
- Modify system-level configuration or registry entries
- Create hidden background processes

---

## Data Handling

This application does not:

- Exfiltrate user data of any kind
- Send personal information to external servers
- Store authentication data persistently between sessions
- Log private message content externally

All processing is performed locally on the user's device. Message content appears only in the in-app activity log during a purge session and is not saved anywhere.

---

## What This Application Does NOT Do

- Extract, scan, or auto-detect Discord tokens from any source
- Access browser storage, process memory, or the file system for credentials
- Steal or transmit Discord tokens or any other credentials
- Harvest passwords or session cookies
- Access unrelated system data
- Download or execute remote code
- Perform unauthorized data collection

---

## False Positives

Security software may flag this application because it:

- Automates Discord API requests
- Uses authentication headers in HTTP requests
- Sends DELETE requests to Discord's API

These are expected behaviours for a tool that interacts with Discord's API on your behalf. The application does nothing beyond what is described in this document.

---

## Security Transparency

Users are encouraged to:

- Inspect the full source code before running it
- Monitor outbound network traffic during use (e.g. with Wireshark)
- Run the application from source rather than any unofficial builds
- Verify all dependencies independently via [PyPI](https://pypi.org)

---

## Reporting Issues

If you discover unexpected behavior or a potential security issue:

- Open an issue on the repository
- Provide reproduction steps where possible
- Do not publicly share your token or any credentials

---

## Responsible Use

Users are responsible for ensuring compliance with:

- Discord's Terms of Service
- Local laws and regulations
- Platform usage policies

This project is provided for personal utility and educational purposes only.
