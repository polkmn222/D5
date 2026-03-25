import os
import subprocess
import sys

def notify(title="Gemini CLI Approval", message="An action requires your approval in the terminal."):
    """Send a local notification to the user."""
    try:
        if sys.platform == "darwin":
            # macOS: Use osascript to show notification
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", script])
        elif sys.platform.startswith("linux"):
            # Linux: Use notify-send if available
            try:
                subprocess.run(["notify-send", title, message])
            except FileNotFoundError:
                # Fallback to terminal bell
                print("\a", end="")
        else:
            # Fallback for Windows or others: terminal bell
            print("\a", end="")
    except Exception as e:
        print(f"Notification Error: {e}")

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "An action requires your approval in the terminal."
    notify(message=msg)
