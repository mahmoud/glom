__version__ = "24.11.1.dev"
version_info = tuple(
    int(part) if part.isdigit() else part for part in __version__.split(".")
)
