# Changelog

## [1.3.2] - 2026-03-24

### Added
* set_mode() for setting the mode globally (f.e to education)
* More tests for the global mode setting

### Improved
* README examples

## [1.3.1] - 2026-03-24

### Added
* Comprehensive README overhaul with clearer structure and examples

### Dev / Tooling
* Improved release pipeline with automated versioning and GitHub releases

## [1.3.0] - 2026-03-24

### Added

* **Educational logging mode (`mode="edu"`)**

    * Human-readable, step-by-step output for learning and algorithm tracing
    * Function calls rendered as:

      ```
      Calling foo(1, b=2)
      ```
    * Automatic argument formatting (args + kwargs)
    * Omits empty kwargs

* **Nested function call tracing**

    * Logs calls inside functions (e.g. `outer.inner()`)

* **Context-aware logging**

    * `log()` inside decorated functions now inherits:

        * `mode`
        * `show_time`
        * `show_file`
        * `show_lineno`

### Improved

* **Output clarity in educational mode**

    * Removed internal noise (`<func ...>`, debug artefacts)
    * Simplified function names (no test/module prefixes)
    * More natural mutation messages:

      ```
      Added 5 to arr -> [1, 2, 5]
      ```

### Fixed

* Formatter crash (`UnboundLocalError: prefix`)
* Incorrect call argument display (`{'args': ..., 'kwargs': ...}`)
* Missing nested call events due to tracer scope issues

### Tests

* Added educational mode test coverage:

    * Call formatting
    * Argument rendering
    * Nested function tracing
    * Inherited logging behavior
    * Human-readable mutations
    * Output cleanliness

## [1.2.0] - 2026-03-23

### Added

* `@log(level=...)` for verbosity control (`call`, `state`, `full`)
* `@log(filter=[...])` to log only selected variables
* Per-function file logging via `@log(filepath=...)`
* Global file logging support
* Decorator-only logging mode toggle

### Improved

* Overall logging flexibility and usability
* Reduced noise in complex traces

---

## [1.1.5] - 2026-03-23

### Changed

* Updated README documentation

---

## [1.1.4] - 2026-03-23

### Fixed

* Class wrapping issues

---

## [1.1.3] - 2026-03-23

### Fixed

* Wrapped object representation

---

## [1.1.2] - 2026-03-23

### Fixed

* Incorrect wrapping of callables

---

## [1.1.1] - 2026-03-23

### Fixed

* Mutation tracking issues
* Nested path logging bugs
* Test failures

---

## [1.1.0] - 2026-03-23

### Added

* Mutation logging support for tracked objects

### Improved

* Core logging capabilities

---

## [1.0.0] - 2026-03-23

### Added

* Initial release
* Variable logging with name inference
* Function tracing
* Object and mapping tracking
* Message logging system
* Basic test suite