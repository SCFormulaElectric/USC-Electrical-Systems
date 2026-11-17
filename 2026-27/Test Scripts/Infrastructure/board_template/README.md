# Board tests

Rename this heading and document:

- Board name/revision, test purpose, owner and relevant requirements.
- Instruments, channel assignments, wiring and probe/shunt ratings.
- Approved voltage/current limits, calibration and pass/fail criteria.
- Setup and shutdown order, output-off cleanup and discharge checks.
- Each script's purpose and any required manual observations.

Copy bench.example.toml to bench.toml; set local IP addresses. Infrastructure/README.md
has installation and execution instructions. test_identity.py only queries the DMM;
it does not validate any board behavior or turn on a supply.

Most tests only need `import pytest`. Instruments are provided as function arguments:

```python
import pytest

@pytest.mark.hardware
def test_identity(dmm):
    assert 'EDU34450A' in dmm.identify()
```

Or use the shared factory directly, with no board fixture required:

```python
import pytest

@pytest.mark.hardware
def test_identity(connect_instrument):
    meter = connect_instrument('dmm')  # instruments.dmm in this board's bench.toml
    assert 'EDU34450A' in meter.query('*IDN?')
```

Connections are identified and closed automatically; sources are not powered off by
generic connection cleanup. The shared glv_supply fixture provides reviewed
EDU36311A setup and OFF cleanup; other source fixtures must implement their own.
Put reusable instrument fixtures in conftest.py; tests do not import fixtures.
For advanced custom fixtures, `from backend import instrument` is the public helper.

Board helper functions can live in helper/. For a Python-compatible board folder
name, expose selected functions from its __init__.py; test authors can then use
`from My_Board_Test import calculate` at any depth. Keep internal relative imports
inside the helper package. Boards with spaces in their names can use pytest fixtures
to expose helpers without spelling the board name in a Python import.

Do not import another board's helper package or modify central configuration just
to register your folder. See Infrastructure/README.md for details.

Read Infrastructure/AI_GUIDE.md when using a coding agent. Copy worked procedures
from Infrastructure/examples and consult Infrastructure/DRIVERS.md for typed APIs.
Use Infrastructure/preflight.py for offline config checks or --connect identity checks.

## Before calling this board tested

- Run the infrastructure offline suite and collect this board's tests.
- Replace test_offline.py's synthetic example with actual acceptance logic and test
  both acceptable and unacceptable readings. It does not certify hardware behavior.
- Add fake-backed tests for any new setup/measurement path and its failure cleanup.
- Run preflight, then review wiring/limits before explicitly selecting hardware tests.
- Record physical commissioning and remaining manual checks separately.

Use default function-scoped fixtures when depending on board_config,
connect_instrument, dmm or glv_supply. Broader scopes are unsupported. Do not add
collection/session hooks or pytest_plugins to this suite.

For a tested source fixture pattern, see ../../Infrastructure/examples/source_fixture.py
and ../../Infrastructure/tests/test_authoring.py. Prefer shared glv_supply for EDU36311A;
other models require their own verified commands. Register OFF before configuration.

Install/update the shared environment with `python Infrastructure/install.py` from
Test Scripts after adding board requirements. A model-only identity accepts any unit
of that model; use the actual identity substring including serial when unit identity matters.
