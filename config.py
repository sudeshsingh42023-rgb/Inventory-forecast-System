import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def get_database_uri():
    return os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'inventory.db')}")


class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOW_STOCK_THRESHOLD_DEFAULT = 20

    @staticmethod
    def init_app(app):
        app.config["SQLALCHEMY_DATABASE_URI"] = get_database_uri()
