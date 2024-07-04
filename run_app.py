from app import app

if __name__ == "__main__":
    from gunicorn.app.wsgiapp import run
    app.run()
