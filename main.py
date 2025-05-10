# Copyright (c) 2025 devgagan : https://github.com/devgaganin.  
# Licensed under the GNU General Public License v3.0.  
# See LICENSE file in the repository root for full license text.

import asyncio
from shared_client import start_client
import importlib
import os
import sys

async def load_and_run_plugins():
    # Start the shared client
    client, app, userbot = await start_client()
    
    plugin_dir = "plugins"
    if not os.path.isdir(plugin_dir):
        print(f"Plugin directory '{plugin_dir}' not found.")
        return

    plugins = [f[:-3] for f in os.listdir(plugin_dir) if f.endswith(".py") and f != "__init__.py"]

    for plugin in plugins:
        try:
            module = importlib.import_module(f"plugins.{plugin}")
            func_name = f"run_{plugin}_plugin"
            if hasattr(module, func_name):
                print(f"Running {plugin} plugin...")
                await getattr(module, func_name)()
            else:
                print(f"Plugin '{plugin}' does not have '{func_name}' function.")
        except Exception as e:
            print(f"Error loading plugin '{plugin}': {e}")

async def main():
    await load_and_run_plugins()
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    print("Starting clients ...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
    except Exception as e:
        print(e)
        sys.exit(1)