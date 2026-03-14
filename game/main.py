"""
Compatibility wrapper for tooling that executes game/main.py directly.

This module exposes the async `main()` coroutine from `game/__main__.py`
without re-entering asyncio during import.
"""
# 'importlib.util' module, provides utility functions
# for dynamically importing modules by filename or other non-standard means (rather than
# normal 'import ...' by package/module name).
# 
# In this file, it's required because we want to load and execute the code in 'game/__main__.py'
# as a module at runtime, so we can access its definitions (e.g., the 'main' coroutine)
# without invoking its __main__ block. This enables 'game/main.py' to act as a compatibility
# wrapper for runtime or tooling environments that expect to interact via 'main.py'.
import importlib.util
import os


def _load_runtime_module():
    main_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "__main__.py")
    spec = importlib.util.spec_from_file_location("game_runtime", main_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load game runtime module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_runtime = _load_runtime_module()
main = _runtime.main


if __name__ == "__main__":
    import nest_asyncio

    async def _boot():
        await _runtime.main_menu(main)

    nest_asyncio.run_main(_boot)
