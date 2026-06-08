#!/usr/bin/env python3
"""
Load Webots world from GitHub repository via simulation server.

Usage:
    python load_world.py <github_url> [--mode {w3d,mjpeg}] [--server localhost:2000]
    python load_world.py https://github.com/user/repo/blob/main/app/worlds/world.wbt
    python load_world.py https://github.com/user/repo/blob/main/app/worlds/world.wbt --mode mjpeg
"""

import asyncio
import json
import sys
import argparse
import webbrowser
import websockets


async def load_world(
    github_url: str,
    server: str = "localhost:2000",
    mode: str = "w3d",
    open_browser: bool = True
) -> str:
    """
    Load a Webots world from GitHub via simulation server.

    Args:
        github_url: Full GitHub URL to world file
        server: Simulation server address (default: localhost:2000)
        mode: Webots mode - 'w3d' (default) or 'mjpeg'
        open_browser: Whether to open the Webots URL in browser

    Returns:
        The WebSocket URL of the launched Webots instance
    """

    protocol = "wss" if server.startswith("https") else "ws"
    ws_url = f"{protocol}://{server}/client"

    payload = {
        "start": {
            "url": github_url,
            "mode": mode
        }
    }

    print(f"🔗 Connecting to simulation server: {ws_url}")
    print(f"🌍 Loading world: {github_url}")
    print(f"📡 Mode: {mode}")

    try:
        async with websockets.connect(ws_url, ping_interval=None) as websocket:
            await websocket.send(json.dumps(payload))
            print("⏳ Request sent, waiting for response...\n")

            while True:
                msg = await websocket.recv()
                try:
                    response = json.loads(msg)
                    webots_url = response.get("webots")
                    if webots_url:
                        print(f"✅ World loaded successfully!")
                        print(f"🌐 Webots URL: {webots_url}\n")

                        if open_browser:
                            print("🌍 Opening in browser...")
                            webbrowser.open(webots_url)

                        return webots_url
                except json.JSONDecodeError:
                    print(f"⏳ Status: {msg}")

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Load Webots world from GitHub repository",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python load_world.py https://github.com/haecto/webots-local-server-test/blob/main/webots/worlds/SensorFusionTrack.wbt
  python load_world.py https://github.com/cyberbotics/webots/blob/master/projects/objects/walls/worlds/wall.wbt --mode mjpeg
  python load_world.py https://github.com/alice/sim/blob/main/app/worlds/my_world.wbt --server simulation.example.com:2000
        """
    )

    parser.add_argument(
        "url",
        help="GitHub URL to world file"
    )

    parser.add_argument(
        "--mode",
        choices=["w3d", "mjpeg"],
        default="w3d",
        help="Webots streaming mode (default: w3d)"
    )

    parser.add_argument(
        "--server",
        default="localhost:2000",
        help="Simulation server address (default: localhost:2000)"
    )

    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't open browser automatically"
    )

    return parser.parse_args()


async def main():
    args = parse_args()
    await load_world(
        github_url=args.url,
        server=args.server,
        mode=args.mode,
        open_browser=not args.no_browser
    )


if __name__ == "__main__":
    asyncio.run(main())
