"""Read-only instrument discovery: python Infrastructure/discover.py [VISA_ADDRESS ...]."""
from pathlib import Path
import sys

sys.pycache_prefix = str(Path(__file__).resolve().parent / '.pycache')

if __name__ == '__main__':
    from backend.discover import main
    main()
