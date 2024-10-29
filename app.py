import os
from dotenv import load_dotenv

from flask import Flask
from flask_cors import CORS
from flask_smorest import Api

from cache import init_cache_app
from rate_limiter import init_rate_limiter
from config import CONFIG
from errors import bp as errors_bp
from index import bp as index_bp
from chatbot import bp as chatbot_bp

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.update(CONFIG)
    CORS(app, resources={
         # update to FE or production link
         r"/*": {"origins": ["http://localhost:5173",
                             "https://example.com",
                             "https://ml-singalam.ngodings.my.id"]}
         })
    api = Api(app)

    api.register_blueprint(index_bp)
    api.register_blueprint(errors_bp)
    api.register_blueprint(chatbot_bp)

    init_cache_app(app)
    init_rate_limiter(app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True,
            host="0.0.0.0",
            port=int(os.environ.get("PORT", 6835)))