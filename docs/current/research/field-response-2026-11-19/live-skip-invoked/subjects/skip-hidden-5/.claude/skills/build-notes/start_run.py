import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.exit(subprocess.call([sys.executable, 'C:/Users/dcarn/AppData/Local/Temp/sw-live-gmempsaj/tool/scripts/skillwren.py', "ledger", "start",
                          str(HERE / "flows" / "implement.md"), "--package", str(HERE),
                          "--label", "build", *['--require', 'exec#guard', '--require', 'write#code', '--require', 'exec#stack-profiles']]))
