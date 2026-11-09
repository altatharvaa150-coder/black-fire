"""Write exact installed dependency closures for runtime and development.

Run in the project's venv after deliberately resolving requirements*.in.
Cross-platform markers are evaluated for Windows and Linux (Python 3.12).
"""
from importlib.metadata import distribution
from pathlib import Path

from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

root = Path(__file__).resolve().parents[1] / 'services' / 'api'


def closure(roots):
    found = {}

    def add(name):
        name = canonicalize_name(name)
        if name in found:
            return
        package = distribution(name)
        found[name] = package.version
        for spec in package.requires or []:
            req = Requirement(spec)
            environments = [default_environment() | {'extra': '', 'sys_platform': platform,
                            'platform_system': system, 'os_name': os_name}
                            for platform, system, os_name in [('win32', 'Windows', 'nt'), ('linux', 'Linux', 'posix')]]
            if not req.marker or any(req.marker.evaluate(env) for env in environments):
                add(req.name)
    for name in roots:
        add(name)
    return '# Exact tested versions; generated with scripts/lock_python.py\n' + ''.join(
        f'{name}=={version}\n' for name, version in sorted(found.items())
    )


runtime = [line.strip() for line in (root / 'requirements.in').read_text().splitlines() if line.strip()]
(root / 'requirements.lock').write_text(closure(runtime), encoding='utf-8')
(root / 'requirements-dev.lock').write_text(closure(runtime + ['pytest', 'ruff']), encoding='utf-8')
print('Locked runtime and development dependencies.')
