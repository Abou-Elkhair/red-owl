#!/bin/sh
cd "$(dirname "$0")" || exit 1
open http://127.0.0.1:8765/ar/ &
exec python3 -B server.py
