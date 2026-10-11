"""Rehome the already bootstrapped Hermes runtime for isolated CLI testing.

Run this file with runpy.run_path after importing hermes_bootstrap, passing HOME
and Hermes arguments in sys.argv. See the verification record for actual commands.
Bootstrapping before rehoming reuses the installed dependency graph rather than
provisioning a second full Hermes environment for every disposable test home.
"""
import os
import sys

os.environ['HERMES_HOME'] = sys.argv.pop(1)
from hermes_cli.main import main

raise SystemExit(main())
