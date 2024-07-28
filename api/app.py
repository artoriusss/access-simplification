import logging
from flask import Flask
from routes.annotate import annotate_bp
from routes.simplify import simplify_bp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your_secret_key'  

app.register_blueprint(annotate_bp)
app.register_blueprint(simplify_bp)

def main():
    app.run(host='0.0.0.0', port=3003) # run app in debug mode on port 3003

if __name__ == '__main__':
    main()