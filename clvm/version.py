import importlib_metadata

__version__: str
try:
    __version__ = importlib_metadata.version(__name__)
except importlib_metadata.PackageNotFoundError:
    # package is not installed
    __version__ = "unknown"
