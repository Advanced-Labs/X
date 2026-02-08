from flask import Flask
from routes.users import users_bp
from routes.items import items_bp
from common_ref import get_version

app = Flask(__name__)
app.register_blueprint(users_bp, url_prefix="/api/users")
app.register_blueprint(items_bp, url_prefix="/api/items")

@app.route("/api/health")
def health():
    return {"status": "ok", "version": get_version()}

if __name__ == "__main__":
    app.run(debug=True, port=5000)
