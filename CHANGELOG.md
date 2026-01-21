# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.15] - 2026-01-21

### Added

- Telegram slash commands for session control and TUI control:
  - `/help`, `/status`, `/web`
  - `/session list`, `/session use`, `/session new`
  - `/approve`, `/agent cycle`, `/interrupt`, `/prompt clear`, `/prompt submit`, `/page ...`
- Key moment notifications forwarded to Telegram:
  - `session.status` (idle/busy/retry)
  - `todo.updated`
  - `permission.updated`
  - `session.error`, tool errors
- Persist bindings to disk at `$OPENCODE_HOME/opencode-on-im/bindings.json`

### Fixed

- `/session use` now handles empty session lists and invalid indexes cleanly

### Changed

- Add `npm test` (runs build + node:test)
- Expanded README with commands, notifications, and permission flow

## [0.1.14] - 2026-01-19

### Fixed

- Docker test environment: wait for `/global/health` before starting bot

[Unreleased]: https://github.com/qikezhang/opencode-on-im/compare/v0.1.15...HEAD
[0.1.15]: https://github.com/qikezhang/opencode-on-im/compare/v0.1.14...v0.1.15
[0.1.14]: https://github.com/qikezhang/opencode-on-im/releases/tag/v0.1.14
