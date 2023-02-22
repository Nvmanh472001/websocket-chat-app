from src.app import app, run_app

if __name__ == "__main__":
    import eventlet
    
    eventlet.monkey_patch()
    run_app()