import sys

__all__ = []

# ensure BlueSky is available
try:
    import bluesky
except ImportError:
    raise ImportError(
        (
            "No module named 'bluesky'\n"
            f"This python is from directory: {sys.prefix}"
            "\n\n"
            "You should type 'exit' now and"
            " find the ipython with Bluesky."
        )
    )


req_version = (1, 1)
cur_version = tuple(map(int, bluesky.__version__.split(".")[:2]))
if cur_version < req_version:
    ver_str = ".".join((map(str, req_version)))
    raise ValueError(
        (
            f"Need at least Bluesky version {ver_str}"
            f" but you have version {bluesky.__version__}"
        )
    )
