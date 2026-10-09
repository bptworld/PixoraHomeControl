# 1.0.3

- Read complete local HTTP responses before decoding JSON, preserving the response size limit. Fixes fragmented device-state and service catalog reads.

# 1.0.2

- Report specific local request failures, HTTP status, and request path in logs without exposing credentials or response bodies.

# 1.0.1

- Publish the app in its own public installation repository.

# 1.0.0

- Pair with Planner and connect outbound to Pixora.
- Send local Home Assistant events to the existing Flow engine.
- Execute shared Planner, Home Control, and Flow requests locally.
- Reconnect automatically; reject expired commands and duplicate IDs.
