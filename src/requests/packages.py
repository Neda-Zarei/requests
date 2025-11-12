import sys
import warnings

from .compat import chardet

# This code exists for backwards compatibility reasons.
# I don't like it either. Just look the other way. :)

_DEPRECATION_MSG = (
    "requests.packages.* is deprecated; import third-party packages directly "
    "(e.g., urllib3, idna, chardet/charset_normalizer)."
)

# Emit a deprecation warning when this module is imported.
# This warning is intentionally broad to cover any usage of requests.packages.*.
warnings.warn(_DEPRECATION_MSG, DeprecationWarning, stacklevel=2)

for package in ("urllib3", "idna"):
    locals()[package] = __import__(package)
    # This traversal is apparently necessary such that the identities are
    # preserved (requests.packages.urllib3.* is urllib3.*)
    for mod in list(sys.modules):
        if mod == package or mod.startswith(f"{package}."):
            sys.modules[f"requests.packages.{mod}"] = sys.modules[mod]

if chardet is not None:
    target = chardet.__name__
    for mod in list(sys.modules):
        if mod == target or mod.startswith(f"{target}."):
            imported_mod = sys.modules[mod]
            sys.modules[f"requests.packages.{mod}"] = imported_mod
            mod = mod.replace(target, "chardet")
            sys.modules[f"requests.packages.{mod}"] = imported_mod


def __getattr__(name):
    """Module attribute access hook to warn on attribute usage.

    Returns any existing alias for the requested attribute if available,
    otherwise raises AttributeError.
    """
    warnings.warn(_DEPRECATION_MSG, DeprecationWarning, stacklevel=2)
    # If we already created a local alias, return it
    if name in globals():
        return globals()[name]

    # Fallback to any existing sys.modules alias created above
    mod = sys.modules.get(f"requests.packages.{name}")
    if mod is not None:
        return mod

    raise AttributeError(f"module 'requests.packages' has no attribute '{name}'")
