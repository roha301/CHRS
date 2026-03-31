import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from db import init_db
from routes.auth import auth_bp
from routes.halls import halls_bp
from routes.bookings import bookings_bp
from routes.analytics import analytics_bp
from routes.poster import poster_bp
from routes.events import events_bp
from routes.notifications import notifications_bp

load_dotenv()
init_db()

app = Flask(__name__, static_folder='../frontend')
CORS(app)

# API Routes
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(halls_bp, url_prefix='/api/halls')
app.register_blueprint(bookings_bp, url_prefix='/api/bookings')
app.register_blueprint(analytics_bp, url_prefix='/api/bookings')
app.register_blueprint(poster_bp, url_prefix='/api/bookings')
app.register_blueprint(events_bp, url_prefix='/api/events')
app.register_blueprint(notifications_bp, url_prefix='/api/notifications')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
