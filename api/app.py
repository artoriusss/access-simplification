from flask import Flask
from routes.annotate import annotate_bp
from routes.simplify import simplify_bp

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

# Register Blueprints
app.register_blueprint(annotate_bp)
app.register_blueprint(simplify_bp)

def main():
    app.run(host='0.0.0.0', port=3003)

if __name__ == '__main__':
    main()