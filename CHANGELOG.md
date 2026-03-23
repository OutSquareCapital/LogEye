# Changelog

## [1.2.0] - 2026-03-23

### Added
- `@log(level=...)` for verbosity control (`call`, `state`, `full`)
- `@log(filter=[...])` to log only selected variables
- Per-function file logging via `@log(filepath=...)`
- Global file logging support
- Decorator-only logging mode toggle

### Improved
- Overall logging flexibility and usability
- Reduced noise in complex traces

---

## [1.1.5] - 2026-03-23

### Changed
- Updated README documentation

---

## [1.1.4] - 2026-03-23

### Fixed
- Class wrapping issues

---

## [1.1.3] - 2026-03-23

### Fixed
- Wrapped object representation

---

## [1.1.2] - 2026-03-23

### Fixed
- Incorrect wrapping of callables

---

## [1.1.1] - 2026-03-23

### Fixed
- Mutation tracking issues
- Nested path logging bugs
- Test failures

---

## [1.1.0] - 2026-03-23

### Added
- Mutation logging support for tracked objects

### Improved
- Core logging capabilities

---

## [1.0.0] - 2026-03-23

### Added
- Initial release
- Variable logging with name inference
- Function tracing
- Object and mapping tracking
- Message logging system
- Basic test suite