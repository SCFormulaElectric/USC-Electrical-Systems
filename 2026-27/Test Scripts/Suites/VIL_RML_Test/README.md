# VIL / RML procedures

Recovered existing procedures; hardware execution remains uncommissioned.
RML/ and VIL/ contain individual procedures; helper/ contains board-specific
measurement code and offline checks. General installation is in Infrastructure/README.md.

From Test Scripts:

```sh
python Infrastructure/run.py Suites/VIL_RML_Test -q
python Infrastructure/run.py Suites/VIL_RML_Test/VIL/test_vil_threshold.py -s --hardware
```

Copy bench.example.toml to bench.toml and complete the reviewed instrument addresses,
commands, protection limits and wiring before hardware use. GLV range is 11-14.4 V.
Current, timer-injection and ordinary voltage tests require different fixture wiring.
The supplied legacy schema is used only by this board's fixture, not the shared backend.
No instrument is opened during the default offline run.

Existing local configurations must add `output_delay_off = "OUTP:DEL:FALL {value}, (@2)"`
inside `[glv]`, matching the reviewed channel used by the other GLV commands.
Setup and shutdown clear the stored OFF delay before requesting OFF. An error
clearing the delay still attempts OFF and remains a reported failure; OFF does not
prove discharge. Required instrument identities cannot be blank.

The isolated timer test validates only its required instrument connections and
command profiles; it does not need an HV source address, command profile or current
limit. Its physical HV-disconnection and DMM checks still apply.

Light observations use measured HV. Measurements whose uncertainty spans 50 V or
60 V are marked NEEDS_REVIEW rather than accepted as conclusive illumination checks.
The 50–60 V transition region remains characterization. Review uncertainty and use
a measured interval wholly inside the required ON/OFF region for a conclusive check.

General waveform parsing, pulse timing, current statistics and monitored console
input are shared under Infrastructure/backend. Existing helper import names remain
compatible; the suite no longer owns duplicate implementations. Lamp-check startup
semantics, voltage requirements, thermal procedure and legacy HV/GLV configuration
remain board-specific.
