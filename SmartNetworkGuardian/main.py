from backend.config.settings import ensure_directories
from backend.database.db import initialize_database
from frontend.web_app import create_app

def main():
    ensure_directories()
    initialize_database()
    app = create_app()
    print("\nSMART NETWORK GUARDIAN")
    print("Web dashboard: http://127.0.0.1:5000")
    print("Press CTRL+C to stop.\n")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)

if __name__ == "__main__":
    main()
