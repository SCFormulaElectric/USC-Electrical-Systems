# Instructions for AI-assisted board test development

Read this guide and Infrastructure/README.md before editing tests or shared code.
For coding tools without AGENTS.md support, include this file explicitly in the prompt.
Read the target board's README, conftest.py and bench.example.toml. Keep changes
scoped to the requested board unless a shared change is actually necessary.

## Structure and imports

- Board work goes in Suites/<board>/; shared tools go in Infrastructure/.
- Use `python Infrastructure/new_board.py <name>` for new boards; no central registration.
  It copies Infrastructure/board_template and creates a clean local bench.toml.
- Do not put source in .venv, caches or results folders. Never move a virtual
  environment; recreate it using the requirements at its new path.
- Use test_*.py functions, ordinary Python loops and pytest assertions. Keep the
  test points, sequence and pass/fail criteria visible in the procedure file.
- Request pytest fixtures as function arguments; never import conftest.py.
- Standard fixtures: board_config, connect_instrument, visa_rm, dmm, glv_supply.
- The dmm fixture exposes EDU34450A.read_voltage_v(), identify(), and raw query().
- glv_supply exposes set_voltage_v(), output_on(), output_off(), read_voltage_v(),
  read_current_a(), wait_for_voltage_v(). It is an EDU36311A channel.
- Advanced imports use `from backend import EDU34450A, EDU36311A, instrument`.
- For board functions use its public package (e.g. `from VIL_RML_Test import
  threshold`), or board-local fixtures. Internal helpers may use relative imports.
- No sys.path edits, wildcard imports, global helper aliases, test-to-test imports,
  dynamic plugin registries or per-board pytest_plugins declarations. The runner
  owns import paths. Keep __init__.py files when copying/nesting board packages.

## Reuse shared measurements

- Use reading, ascii_waveform, pulse_timing, pulse_window, current_statistics and
  monitored_input from backend. Do not copy implementations from VIL/RML helpers.
- Pure waveform calculations live in backend/measurements.py; monitored console
  input lives in backend/operator.py. Their tests must not import a board package.
- Keep board voltages, thresholds, pin mappings, acceptance criteria and procedures
  in its suite. Do not promote a board's combined bench controller as a generic driver.
- pulse_timing defaults to 30 complete cycles and active-low input for compatibility;
  choose min_cycles and active_below explicitly for other signals when appropriate.
- monitored_input requires the board's check callback. Propagate its timeout/errors
  to fixture cleanup; do not catch them and continue energizing or prompting.

## Hardware access and cleanup

- Every test touching a device or requiring manual bench interaction must have
  @pytest.mark.hardware (or a module-level hardware mark).
- No hardware access at module import or collection time. No sockets or alternate
  VISA managers bypassing the shared fixture. Backend is always pyvisa-py (@py).
- Existing VIL/RML procedures have legacy, board-local fixtures. Preserve their
  behavior unless explicitly working on that board; do not migrate them blindly.
- Generic connect_instrument validates identity and closes sessions. It does NOT
  disable outputs. Never describe connection cleanup as power protection.
- Prefer the supplied glv_supply fixture when the instrument really is EDU36311A.
  It registers OFF before configuration. Configuration leaves output OFF; tests
  explicitly set voltage and enable. Never add implicit output enabling.
- For new source fixtures, register cleanup BEFORE the first output-changing
  command. OFF must be attempted after failed configuration, failed assertions,
  interruptions and partial connections. Teardown errors must stay visible.
- Do not auto-clear tripped protection, silently retry an output enable, or use
  *RST as generic connection setup. Do not control channels the board does not own.
- No concurrent hardware tests. A hardware fault stops further execution; investigate
  before rerunning. Coordinate exclusive bench ownership between team members.
- Use bounded waits and instrument readback, not long blind sleeps. Manual prompts
  require -s. Do not leave an energized fixture unattended while waiting for input.
- OFF/state queries do not prove discharge or protect against a broken network.
  Actual protection, wiring, probe ratings and discharge procedures are physical
  bench responsibilities. Do not claim software can guarantee them.

## Configuration, commands and acceptance

- Commit bench.example.toml; personal addresses and limits go in ignored bench.toml.
- Vehicle GLV requirement is 11-14.4 V, nominal 12 V. That does not establish every
  component's voltage rating or a safe current limit. Do not guess current/thermal
  limits, measurement uncertainties, tolerances or review flags to make a test pass.
- Supply configuration must include the model's channel and reviewed voltage/current/
  OVP limits. A reviewed flag records an actual review, not a bypass for missing data.
- Verify SCPI against the exact model's manual; cite its command source in DRIVERS.md.
  A related series is not sufficient. Raise an actionable error when information is
  missing, while continuing independent software work. Do not claim unknown commands
  are verified. Current shared drivers are only EDU34450A and EDU36311A.
- Drivers belong in Infrastructure/backend/instruments.py while small. Add only
  operations the tests need. Keep model details/SCPI out of beginner-facing procedures.
- Method/result names carry units: voltage_v, current_a, timeout_s, temperature_c.
  Add type hints/docstrings to shared APIs so editors can explain them.
- Reject NaN, infinity, overload sentinels and invalid configuration/readbacks.
- PASS must correspond to actual assertions. Label manual observations as manual,
  sampled peaks as sampled, and characterization as characterization. Do not invent
  a compliance tolerance or assert full board/vehicle compliance from one measurement.
- Use record_property with unit-bearing names for values in JUnit reports; include
  useful measured/expected values in assertion messages. Do not assert success merely
  because a command was sent or a log file was created.

## Validation before handing work back

From Test Scripts, using the local Infrastructure/.venv interpreter:

```sh
python Infrastructure/run.py -q
python Infrastructure/run.py Suites/<board> --collect-only -q
python Infrastructure/preflight.py Suites/<board> --instrument dmm
```

Preflight checks a real local config and may correctly fail when bench.toml is absent.
Do not weaken validation to make it pass. --connect is a separate read-only identity
check. Never pass --hardware just to test framework changes on unknown equipment.

- New driver branches and source changes need fake-instrument checks for commands,
  limits, bad readings and failure cleanup. Test all affected callers, not just a diff.
- Changes to fixtures/imports/config discovery need regression checks for two board
  folders, duplicate filenames, nested directories, names with spaces, overrides,
  hardware opt-in and cleanup ordering. Keep existing public APIs compatible.
- Examples live in Infrastructure/examples and are excluded from defaults. Verify
  copies run offline/skip hardware until explicitly enabled.
- Run git diff --check. Do not rewrite unrelated files or add dependencies/frameworks
  for a few lines. Update docs/template/CI when an interface or path changes.
- CI covers Windows/macOS, Python 3.11/3.13, without hardware. State exactly what was
  tested locally, which checks passed, and what still needs physical commissioning.
  Never promise code cannot break or say hardware worked based on fake tests.

## Enforced authoring path

- Install dependencies using Infrastructure/install.py (shared environment, all boards).
- Shared fixtures are function-scoped; dependent board fixtures must be too.
- The runner rejects global collection/session hooks and pytest_plugins in suites.
  Prefer fixtures; existing runtime/report hooks must remain board-specific.
- --bench is restricted to one collected board per run.
- Adapt examples/source_fixture.py for EDU36311A only; fake-backed recipe checks
  live in tests/test_authoring.py. Do not duplicate drivers or invent other model commands.
- Generated test_offline.py is synthetic teaching code. Replace with real acceptance
  logic and add failure-path checks; hardware-skipped green runs are not commissioning.
