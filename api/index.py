from flask import Flask, request, jsonify
import sys
import os

# Add the parent directory to sys.path so we can import core and other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import core

app = Flask(__name__)

@app.route('/api/bypass', methods=['POST'])
def bypass():
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        # We don't need to suppress stdout here because Vercel logs are fine,
        # and we are returning JSON response via Flask.
        result = core.loop_thread(url)

        # Check if result is a file path (from freewall)
        if result and os.path.exists(result) and os.path.isfile(result):
             # It's a file path
             filename = os.path.basename(result)
             # Vercel functions have size limits, but for small files (images/docs) this works.
             # We return it as a download attachment if possible, or base64.
             # Since the frontend expects JSON, we'll send a signal.

             from flask import send_file
             # If we want to support direct download:
             return send_file(result, as_attachment=True, download_name=filename)

             # Alternatively, for consistency with the JSON API:
             # import base64
             # with open(result, "rb") as f:
             #    encoded = base64.b64encode(f.read()).decode('utf-8')
             # return jsonify({"file": encoded, "filename": filename})

        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Vercel requires the app object to be exposed
# If running locally
if __name__ == '__main__':
    app.run()
