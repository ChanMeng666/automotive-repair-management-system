"""
Application Entry Point
Automotive Repair Management System
For local development use
"""
import os
import logging
from app import create_app

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    """Main function"""
    # Create application
    app = create_app()

    # Get runtime configuration
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    debug = app.config.get('DEBUG', False)

    print("\n" + "=" * 60)
    print("Selwyn Panel Beaters Online Service")
    print("Automotive Repair Management System")
    print("=" * 60)
    print(f"Application URL: http://{host}:{port}")
    print(f"Debug Mode: {'Enabled' if debug else 'Disabled'}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print("=" * 60 + "\n")

    # Start application
    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\nApplication closed")
    except Exception as e:
        print(f"\nApplication startup failed: {e}")


if __name__ == "__main__":
    main()
