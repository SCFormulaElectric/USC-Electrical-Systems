# Copyable examples

Copy the example you need into Suites/<board>/, then adapt its wiring, limits and
assertions. Examples are excluded from default discovery until copied. They are
procedures to adapt, not commissioned tests or a substitute for a board test plan.

- test_voltage.py: DMM measurement with the source supplied manually.
- test_voltage_sweep.py: explicit test points and assertions using glv_supply.
- test_manual_observation.py: unpowered visual inspection, labeled manual.
- test_offline_calculation.py: parameterized calculation checks without instruments.

The supply sweep requires the reviewed instruments.glv_supply table described in
Infrastructure/DRIVERS.md and settle_tolerance_v / settle_timeout_s under limits.
Choose those tolerances from the actual requirements and measurement uncertainty.
Use --junitxml=<board>/results/run.xml to include record_property values in a report.
Keep board-specific sequences visible in test files; put repeated instrument
operations in fixtures/drivers. Do not enable a source at import/collection time.

source_fixture.py is a copyable conftest recipe for an EDU36311A source. Prefer
shared glv_supply; adapt other models only with verified drivers and cleanup checks.
