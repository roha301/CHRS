# Implementation Details: Important Code Explanations

This document covers the intricate logic powering the core features of the **College Hall Reservation System (CHRS)**. Below are explanations of the most technical and critical functions within the platform.

---

## 1. Booking Clash Detection Engine
**Location:** `backend/routes/bookings.py` (Inside `create_booking()`)

One of the most critical back-end operations is validating that a newly requested booking does not overlap with an already approved booking (or system maintenance) for a specific hall.

### How it works:
Instead of fetching all bookings and filtering them in Python (which is slow), we rely on **MongoDB's Query Operators** (`$or`, `$lt`, `$gt`, etc.) to directly query for conflicting overlapping time blocks.

```python
# Check for time clashes with approved bookings or maintenance
clash_query = {
    'hallId': booking['hallId'],
    'date': booking['date'],
    'status': {'$in': ['approved', 'maintenance']},
    '$or': [
        # Scenario A: New booking starts during an existing booking
        {'startTime': {'$lte': booking['startTime']}, 'endTime': {'$gt': booking['startTime']}},
        
        # Scenario B: New booking ends during an existing booking
        {'startTime': {'$lt': booking['endTime']}, 'endTime': {'$gte': booking['endTime']}},
        
        # Scenario C: New booking completely encompasses an existing booking
        {'startTime': {'$gte': booking['startTime']}, 'endTime': {'$lte': booking['endTime']}}
    ]
}
```
**Explanation:** 
* Scenario A explicitly prevents someone from booking a hall at 1:00 PM if there is an existing booking from 12:00 PM to 2:00 PM.
* Scenario C catches sweeping bookings (e.g., booking 10:00 AM to 5:00 PM) that might overwrite a tiny 1:00 PM to 2:00 PM seminar inside that window.
* Only `approved` bookings or absolute `maintenance` windows trigger a clash. "Pending" reservations do not block the calendar (first to get approved wins).

---

## 2. Dynamic Event Poster & QR Generator
**Location:** `frontend/pages/events.html` (Inside `createBeautifulPoster()`)

The platform generates highly aesthetic promotional posters on the fly completely client-side in the user's browser without requiring a heavy backend image manipulation service.

### How it works:
It utilizes the **HTML5 `<canvas>` API** layering technique.

```javascript
function createBeautifulPoster(ev, qrDataUrl, fullUrl, mode) {
    const canvas = document.createElement('canvas');
    canvas.width = 1080;
    canvas.height = 1350; // Instagram Portrait Standard Size
    const ctx = canvas.getContext('2d');

    // 1. Draw Background Gradient
    const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
    gradient.addColorStop(0, '#0f172a'); // Very dark slate
    gradient.addColorStop(0.5, '#312e81'); // Indigo
    gradient.addColorStop(1, '#4c1d95'); // Deep purple
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 2. Draw Dynamic Text
    ctx.fillStyle = '#a78bfa';
    ctx.font = 'bold 72px "Poppins", sans-serif';
    ctx.fillText(ev.title, canvas.width / 2, 250);

    // ... Code safely loads the QRCode Image Object
    const qrImage = new Image();
    qrImage.onload = () => {
        // Draw the QR into the white padded box on the canvas
        ctx.drawImage(qrImage, qrX, qrY, qrSize, qrSize);
        // Turn the final canvas into a JPEG data blob which forces a download
        resolve(canvas.toDataURL('image/jpeg', 0.95));
    };
    qrImage.src = qrDataUrl;
});
```
**Explanation:**
This avoids massive overhead on the server by drawing the background colors, shapes, the `ev.title` and formatting the dates instantly inside the user's local hardware rendering engine. The `qrDataUrl` is simply `qrcode.js` making a lightweight base64 string that the canvas paints.

---

## 3. Contactless Self Check-in API
**Location:** `backend/routes/events.py` (Inside `self_checkin()`)

When a user scans a Check-in QR code, it loads a web portal. They enter their name, which hits the `/self-checkin` Python route. Validating this smoothly determines the success of automated attendance.

### How it works:
It performs an in-memory loop on the event's embedded nested participants array.

```python
target = None
for participant in participants:
    # Case insensitive exact string match for robust lookups
    if participant.get('name', '').lower() == name.lower():
        target = participant
        break

if not target:
    return jsonify({'message': 'Name not found in the registration list.'}), 404

if target.get('checkedIn'):
    return jsonify({'message': 'You are already checked in!'}), 400

# Mutate the target dictionary in memory
target['checkedIn'] = True
target['checkedInAt'] = datetime.datetime.utcnow().isoformat()

# Save the updated array back to NoSQL
events_collection.update_one(
    {'_id': event_id},
    {'$set': {'participants': participants}}
)
```
**Explanation:** 
Because MongoDB handles embedded array manipulations using positional operators weirdly when the structure isn't entirely uniform, we load the array into Python, do our highly reliable lowercase loop matching, mutate the specific dictionary reference, and dump the entire list back to NoSQL (`$set`).

---

## 4. Google OAuth API Verification
**Location:** `backend/routes/auth.py`

When the user clicks "Log in with Google", Google returns a massive signed JWT to the frontend. The frontend sends this to our `/auth/google` API.

### How it works:
Our backend explicitly contacts Google's official public servers to cryptographically verify the token wasn't tampered with.

```python
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# 1. Contact Google to decrypt and verify token signature.
idinfo = id_token.verify_oauth2_token(
    id_token_jwt_string, google_requests.Request(), GOOGLE_CLIENT_ID
)

# 2. Extract verified assertions
email = idinfo['email']
name = idinfo.get('name', '')

# 3. Seamlessly link to local database or create a new user profile on the fly
user = users_collection.find_one({'email': email})
if not user:
    user = {
        'id': user_id,
        'email': email,
        'name': name,
        'role': 'user', # System defaults via SSO.
        'authProvider': 'google'
    }
    users_collection.insert_one(user)

# 4. Generate the standard local JWT allowing subsequent API interactions
access_token = generate_jwt(user)
```
**Explanation:** 
If someone tries to send a fake JSON string with random emails, the `id_token.verify` throws a `ValueError` because the cryptographic signature will not match Google's official public signing keys (fetched under the hood automatically by `google-auth`).

---

## 5. Live Notification Polling Engine
**Location:** `frontend/js/api.js`

To achieve "Real-time" updates without the massive server scaling complexity of `WebSockets`, CHRS uses intelligent short-polling.

### How it works:
```javascript
let _notifPollTimer = null;

function startNotificationPolling() {
    if (!localStorage.getItem('token')) return; // Abort if not logged in
    
    // Immediate Initial Fetch
    fetchNotifications(); 
    
    // Background polling every 30 seconds
    _notifPollTimer = setInterval(fetchNotifications, 30000); 
}

// Ensure polling doesn't continue anonymously after logout
function logout() {
    stopNotificationPolling();
    localStorage.clear();
    window.location.href = '../index.html';
}
```
**Explanation:**
This is extremely lightweight. Every 30 seconds the system checks the very fast `/notifications` endpoint. If the user logs out, we clear the `setInterval` using `stopNotificationPolling()` removing CPU strain and stopping unauthorized requests. When fetched, the user's notification `badge` updates seamlessly causing zero disruption to the active view.
