#!/bin/bash
set -euo pipefail

# Create runtime directory for temporary files
# Try /run/secrets first, then fallback to /tmp if not writable
RUNTIME_DIR="/run/secrets"
if ! mkdir -p "$RUNTIME_DIR" 2>/dev/null; then
    echo "Warning: Cannot create /run/secrets, falling back to /tmp"
    RUNTIME_DIR="/tmp"
    mkdir -p "$RUNTIME_DIR"
fi

# Handle base64-encoded cookies
if [ -n "${COOKIES_B64:-}" ]; then
    echo "Decoding base64 cookies..."

    # Create temporary cookie file
    COOKIE_FILE="$RUNTIME_DIR/cookies.txt"

    # Decode base64 cookies and write to temp file
    echo "$COOKIES_B64" | base64 -d > "$COOKIE_FILE"

    # Set proper permissions (readable only by owner)
    chmod 600 "$COOKIE_FILE"

    # Export the cookie file path for the application
    export YT_DLP_DEFAULTS__COOKIEFILE="$COOKIE_FILE"

    echo "Cookies decoded and saved to $COOKIE_FILE"
else
    echo "No COOKIES_B64 environment variable found, skipping cookie setup"
fi

# Execute the original command
exec "$@"
