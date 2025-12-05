import sys
import json
import os
import contextlib

# Suppress stdout to prevent pollution from bypasser prints
@contextlib.contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout

# We can import core, but we need to make sure we don't print anything during import if possible.
# bypasser.py seems to have prints only in functions, not at top level (except the one we might have missed, but checked earlier).

import core

def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # Read from stdin
        try:
            input_data = json.load(sys.stdin)
            url = input_data.get("url")
        except:
            url = None

    if not url:
        print(json.dumps({"error": "No URL provided"}))
        return

    try:
        with suppress_stdout():
            result = core.loop_thread(url)

        # Check if result is a file path (for freewall)
        # In core.py we modified it to return the path.
        # But for normal links it returns a string with newlines.
        if result and os.path.exists(result) and os.path.isfile(result):
            # For CLI usage, we just return the path so Node can handle it
            # (Node could read it and send it, or just print the path)
            print(json.dumps({"result": f"File downloaded to: {result}", "file_path": result}))
        else:
            print(json.dumps({"result": result}))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    main()
