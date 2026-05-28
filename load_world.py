#!/usr/bin/env python3
"""Simple script to load a Webots world"""

import asyncio
import json
import websockets
import sys

async def load_world(world_url):
    async with websockets.connect("ws://localhost:2000/client", ping_interval=None) as ws:
        await ws.send(json.dumps({"start": {"url": world_url}}))

        while True:
            msg = await ws.recv()
            try:
                response = json.loads(msg)
                print(f"✅ {response.get('url')}")
                break
            except json.JSONDecodeError:
                print(f"⏳ {msg}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python load_world.py <github_url>")
        print()
        print("Example:")
        print("  python load_world.py https://github.com/haecto/webots-local-server-test/blob/main/webots/worlds/SensorFusionTrack.wbt")
        sys.exit(1)

    url = sys.argv[1]
    asyncio.run(load_world(url))
