"""Optional Hugging Face ZeroGPU compatibility.

The real ``spaces.GPU`` decorator is applied when the ``spaces`` package is
available. Local development remains functional when the package is missing.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar, cast

try:
    import spaces
except Exception:
    spaces = None  # type: ignore[assignment]


F = TypeVar("F", bound=Callable[..., Any])

SPACES_IMPORT_SUCCEEDED = spaces is not None
ZERO_GPU_DECORATOR_ACTIVE = bool(
    SPACES_IMPORT_SUCCEEDED and callable(getattr(spaces, "GPU", None))
)
ZERO_GPU_RUNTIME_ACTIVE = bool(
    SPACES_IMPORT_SUCCEEDED
    and getattr(getattr(getattr(spaces, "config", None), "Config", None), "zero_gpu", False)
)


def gpu_function(*, duration: int = 180) -> Callable[[F], F]:
    """Return the real ZeroGPU decorator or a local no-op fallback."""

    if ZERO_GPU_DECORATOR_ACTIVE:
        return cast(Callable[[F], F], spaces.GPU(duration=duration))

    def identity(function: F) -> F:
        return function

    return identity
