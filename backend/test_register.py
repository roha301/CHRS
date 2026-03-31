import urllib.request
import json

data = json.dumps({'name': 'Test User', 'email': 'test@kkwagh.edu.in', 'password': 'password', 'role': 'user'}).encode('utf-8')
req = urllib.request.Request('http://localhost:5000/api/auth/register', data=data, headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as f:
        print(f.read().decode('utf-8'))
except Exception as e:
    print(e)
    if hasattr(e, 'read'):
        print(e.read().decode('utf-8'))
