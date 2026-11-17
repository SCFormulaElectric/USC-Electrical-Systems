"""Install the shared environment, including all board requirements. No hardware access."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def install(root=ROOT):
    requirements = [root / 'Infrastructure/requirements.txt']
    requirements.extend(sorted((root / 'Suites').glob('*/requirements.txt')))
    command = [sys.executable, '-m', 'pip', 'install']
    for path in requirements:
        command.extend(['-r', str(path)])
    subprocess.run(command, check=True)
    subprocess.run([sys.executable, '-m', 'pip', 'check'], check=True)


if __name__ == '__main__':
    install()
