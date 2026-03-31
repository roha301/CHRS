# How to Run CHRS locally on Terminal

This guide provides step-by-step instructions on how to start the KKWIEER College Hall Reservation System application directly from your terminal (CMD or PowerShell).

### 1. Open Terminal and Navigate to the Project folder
Ensure you are in the root directory of the application:
```powershell
cd C:\Users\Asus\Desktop\CHRS
```

### 2. Enter the Backend Directory
The server logic lives in the `backend` folder:
```powershell
cd backend
```

### 3. Activate the Virtual Environment
Before starting the application, you must activate the Python virtual environment (.venv) so the correct dependencies are loaded. From the `backend` folder:
```powershell
..\.venv\Scripts\activate
```
*(You should see `(.venv)` prefix appear in your terminal prompt)*

### 4. Start the Application Server
Run the Flask server:
```powershell
python app.py
```
*(If dependencies are missing, install them first using: `pip install -r requirements.txt`)*

### 5. Access the Website
Once the terminal says `* Running on http://127.0.0.1:5000`, open your web browser and go to:
**http://localhost:5000**

---

### To Stop the Server
When done, click on your terminal window and press `CTRL + C` to stop the Python server. You can exit the virtual environment by typing:
```powershell
deactivate
```
