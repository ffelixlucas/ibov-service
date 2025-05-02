from flask import Flask
from app.routes import market_bp
from dotenv import load_dotenv
from app.config import Config  
import os

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)  
app.register_blueprint(market_bp)

if __name__ == "__main__":
    port = app.config["PORT"]
    app.run(host="0.0.0.0", port=port)
