# In-memory data store for testing without a database

users = []

halls = [
    {
        "_id": "h1",
        "name": "JVN Hall",
        "location": "4th Floor, CSD Department",
        "capacity": 150,
        "resources": ["Smart Board", "Projector", "Sound System"],
        "maintenanceWindows": []
    },
    {
        "_id": "h2",
        "name": "Faraday Hall",
        "location": "2nd Floor, Electrical Department",
        "capacity": 100,
        "resources": ["Smart Board", "Sound System"],
        "maintenanceWindows": []
    },
    {
        "_id": "h3",
        "name": "Vishveshwaraya Hall",
        "location": "2nd Floor, Civil Department",
        "capacity": 80,
        "resources": ["Screen", "Projector", "Speakers"],
        "maintenanceWindows": []
    },
    {
        "_id": "h4",
        "name": "P.C Ray Hall",
        "location": "2nd Floor, Chemical Department",
        "capacity": 150,
        "resources": ["Smart Board", "Projector", "Speaker", "Sound System"],
        "maintenanceWindows": []
    },
    {
        "_id": "h5",
        "name": "MCA Hall",
        "location": "4th Floor, MCA Department",
        "capacity": 100,
        "resources": ["Smart Board", "Projector", "AC"],
        "maintenanceWindows": []
    },
    {
        "_id": "h6",
        "name": "Meeting Hall 1",
        "location": "MBA Department",
        "capacity": 100,
        "resources": ["Smart Board", "Projector", "AC"],
        "maintenanceWindows": []
    }
]

bookings = []
