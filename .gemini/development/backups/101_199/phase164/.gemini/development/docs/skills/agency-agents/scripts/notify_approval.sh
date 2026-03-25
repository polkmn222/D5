#!/bin/bash
# scripts/notify_approval.sh: Trigger a macOS system notification for terminal approval.

TITLE="Gemini CLI Approval"
MESSAGE="An action requires your approval in the terminal."

if [[ "$OSTYPE" == "darwin"* ]]; then
    osascript -e "display notification \"$MESSAGE\" with title \"$TITLE\""
else
    # Fallback for Linux or other systems if needed (requires libnotify-bin)
    if command -v notify-send &> /dev/null; then
        notify-send "$TITLE" "$MESSAGE"
    else
        # Just a terminal bell as a last resort
        echo -e "\a"
    fi
fi
