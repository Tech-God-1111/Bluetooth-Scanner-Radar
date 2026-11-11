import threading
import webbrowser

from backend.config.settings import ensure_directories
from backend.database.db import initialize_database
from frontend.web_app import create_app

HOST = "127.0.0.1"
PORT = 5000
URL = f"http://{HOST}:{PORT}"

def main():
    ensure_directories()
    initialize_database()
    app = create_app()
    print("\nSMART NETWORK GUARDIAN")
    print(f"Web dashboard: {URL}")
    print("Press CTRL+C in this terminal to stop the server.\n")
    threading.Timer(1.0, lambda: webbrowser.open_new_tab(URL)).start()
    app.run(host=HOST, port=PORT, debug=False, threaded=True)

if __name__ == "__main__":
    main()
