# CHRS: KKWIEER College Hall Reservation System

CHRS (College Hall Reservation System) is a comprehensive web application designed to streamline the process of reserving halls and managing events at KKWIEER. It provides a user-friendly interface for students and administrators to handle bookings, event registrations, and ticketing efficiently.

## Features

- **Role-Based Access Control:** Distinct interfaces and permissions for Students and Administrators.
  - *Students:* Browse available halls, request bookings, register for events, and view personal booking history. Must register using the official `@kkwagh.edu.in` domain.
  - *Administrators:* Manage hall inventory, approve/reject booking requests, oversee event registrations, and access analytics dashboards.
- **Hall Management:** View detailed information about available halls, their capacity, and current booking status.
- **Event Registration:** Seamless registration for upcoming college events.
- **Automated Poster & Ticket Generation:** Generates event posters and unique QR codes for tickets (using `qrcode` and `pillow`).
- **Real-time Availability:** Conflict-free booking through real-time availability checking.

## Tech Stack

**Frontend:**
- HTML5, CSS3, Vanilla JavaScript
- Modern, responsive design using custom glassmorphism components
- Fetch API for backend communication

**Backend:**
- Python + Flask (RESTful API)
- PyMongo (MongoDB Database)
- PyJWT & bcrypt (Secure Authentication)
- Pillow & qrcode (Image and QR payload generation)

## Prerequisites

- [Python 3.8+](https://www.python.org/downloads/)
- [MongoDB](https://www.mongodb.com/) (Local or Atlas URL)
- [Git](https://git-scm.com/)

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/roha301/CHRS.git
   cd CHRS
   ```

2. **Set up the virtual environment & install dependencies:**
   ```bash
   cd backend
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/Mac:
   source .venv/bin/activate
   
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the `backend` directory with the following configuration:
   ```env
   PORT=5000
   MONGO_URI=your_mongodb_connection_string
   JWT_SECRET=your_super_secret_jwt_key
   ```

4. **Initialize the Database:**
   Wait for the backend server to run. The database schemas are automatically initialized using `db.py`.

5. **Run the Application:**
   ```bash
   # From the backend directory with your virtual environment activated:
   python app.py
   ```
   The backend server will run on `http://localhost:5000`. The frontend templates are served automatically by Flask as static files from the root URL. Just visit `http://localhost:5000` in your web browser.

## Default Credentials

If initialized with default data, an administrator account is available:
- **Email/Username:** `CHRS21`
- **Password:** `KKWIEER`

*(Make sure to change these credentials in a production environment!)*

## License

This project is intended for educational and internal college use at KKWIEER.
