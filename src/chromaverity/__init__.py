"""chromaverity: check whether a video's color labels match its pixels.

Mezzframe open lab, Encode topic. Apache-2.0.

The package is split so that each module does one job you can explain in a
sentence. See docs/02-how-it-works.md for the map.
"""

__version__ = "0.1.0.dev0"

# The report format has its own version, separate from the package version.
# Agents and scripts parse reports; bump this only when a field changes meaning
# or disappears (see docs/05-report-format.md).
REPORT_SCHEMA_VERSION = "0.1"
