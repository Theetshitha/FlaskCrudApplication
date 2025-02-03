from flask import Flask, render_template, render_template_string, request, redirect, url_for, session, flash  
from flask_pymongo import PyMongo  
import bcrypt  
from oauthlib.oauth2 import WebApplicationClient  
import requests  
import os  
import random  
import string  
from bson.objectid import ObjectId  

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  

app = Flask(__name__)  
app.secret_key = 'your_secret_key'  

app.config["MONGO_URI"] = "mongodb://localhost:27017/mydatabase"  
mongo = PyMongo(app)  

GOOGLE_CLIENT_ID = "460868348129-7mt9vccdrptdtaccv9pjf0fmimp6ahgt.apps.googleusercontent.com"  
GOOGLE_CLIENT_SECRET = "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"  
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"  
REDIRECT_URI = "http://127.0.0.1:5000/home/callback"  

client = WebApplicationClient(GOOGLE_CLIENT_ID)  

HTML_TEMPLATE = """  
<!DOCTYPE html>  
<html lang="en">  
<head>  
    <meta charset="UTF-8">  
    <meta name="viewport" content="width=device-width, initial-scale=1.0">  
    <title>Login</title>  
    <link rel="stylesheet" href="/static/styles/styles.css">  
</head>  
<body>  
    <nav>  
        <h1><a href="/home">Employees Hub</a></h1>  
        <a href="/home">Home</a>  
        <a href="#">About</a>  
        <a href="#">Services</a>  
        <a href="/contact">Contact</a>  
    </nav>  
    <div class="container">  
        {% with messages = get_flashed_messages() %}  
            {% if messages %}  
                <div class="flash-message">  
                    {{ messages[0] }}  
                </div>  
            {% endif %}  
        {% endwith %}  
        <form id="loginForm" method="POST" action="/register">  
            <h2>Login</h2>  
            <input type="email" name="email" placeholder="Email" required>  
            <input type="password" name="password" placeholder="Password" required>  
            <button type="submit">Login</button>  
            <p>----------------- OR -----------------</p>  
            <a href="/login/google">  
                <img src="https://auth.openai.com/assets/google-logo-NePEveMl.svg" alt="Google Login"><span>Continue with Google</span>  
            </a>  
        </form>  
    </div>  
</body>  
</html>  
"""  

def get_google_provider_cfg():  
    return requests.get(GOOGLE_DISCOVERY_URL).json()  

def generate_random_password(length=8):  
    """Generates a random password of a given length."""  
    characters = string.ascii_letters + string.digits + string.punctuation  
    return ''.join(random.choice(characters) for i in range(length))  

@app.route('/')  
def login():  
    if 'email' in session:  
        return redirect('/home')  
    return render_template_string(HTML_TEMPLATE)  

@app.route('/register', methods=['POST'])  
def register():  
    email = request.form['email']  
    password = request.form['password']  
    user = mongo.db.normal_logins.find_one({"email": email})  

    if user:  
        if bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):  
            flash("Logged in successfully!")  
            session['email'] = email  
            return redirect('/home')  
        else:  
            flash("Invalid credentials!")  
            return redirect('/')  

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')  
    try:  
        mongo.db.normal_logins.insert_one({"email": email, "password": hashed_password})  
        session['email'] = email  
        flash("Account created successfully!")  
    except Exception as e:  
        flash(f"Error: {str(e)}")  
        return redirect('/')  
    return redirect('/home')  

@app.route('/login/google')  
def login_google():  
    google_provider_cfg = get_google_provider_cfg()  
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]  
    request_uri = client.prepare_request_uri(  
        authorization_endpoint,  
        redirect_uri=REDIRECT_URI,  
        scope=["openid", "email", "profile"]  
    )  
    return redirect(request_uri)  

@app.route('/home/callback')  
def callback():  
    code = request.args.get("code")  
    google_provider_cfg = get_google_provider_cfg()  
    token_endpoint = google_provider_cfg["token_endpoint"]  

    token_url, headers, body = client.prepare_token_request(  
        token_endpoint,  
        authorization_response=request.url,  
        redirect_url=REDIRECT_URI,  
        code=code  
    )  
    token_response = requests.post(  
        token_url,  
        headers=headers,  
        data=body,  
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),  
    )  
    client.parse_request_body_response(token_response.text)  

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]  
    uri, headers, body = client.add_token(userinfo_endpoint)  
    userinfo_response = requests.get(uri, headers=headers, data=body)  

    user_info = userinfo_response.json()  
    email = user_info.get("email")  
    name = user_info.get("name")  

    user = mongo.db.google_logins.find_one({"email": email})  
    if not user:  
        random_password = generate_random_password()  
        hashed_random_password = bcrypt.hashpw(random_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')  
        try:  
            mongo.db.google_logins.insert_one({  
                "name": name,  
                "email": email,  
                "password": hashed_random_password,   
            })  
        except Exception as e:  
            flash(f"Error: {str(e)}")  
            return redirect('/')  

    session['email'] = email  
    return redirect('/home')  

@app.route('/home')  
def home():  
    if 'email' not in session:  
        return redirect('/')  
    employee_records = mongo.db.employees.find()  
    return render_template("home.html", email=session['email'], employees=employee_records)  

@app.route('/logout')  
def logout():  
    session.clear()  
    return redirect('/')  

@app.route('/add', methods=['GET', 'POST'])  
def add_employee():  
    if 'email' not in session:  
        return redirect('/')  
    if request.method == 'POST':  
        employee = {  
            "id": request.form['id'],  
            "name": request.form['name'],  
            "age": request.form['age'],  
            "phoneNo": request.form['phoneNo'],  
            "department": request.form['department'],  
            "salary": request.form['salary'],  
            "address": request.form['address']  
        }  
        mongo.db.employees.insert_one(employee)  
        return redirect(url_for('home'))  
    return render_template('add_employee.html')  

@app.route('/edit/<id>', methods=['GET', 'POST'])  
def edit_employee(id):  
    if 'email' not in session:  
        return redirect('/')  
    employee = mongo.db.employees.find_one({"_id": ObjectId(id)})  
    if request.method == 'POST':  
        updated_employee = {  
            "id": request.form['id'],  
            "name": request.form['name'],  
            "age": request.form['age'],  
            "phoneNo": request.form['phoneNo'],  
            "department": request.form['department'],  
            "salary": request.form['salary'],  
            "address": request.form['address']  
        }  
        mongo.db.employees.update_one({"_id": ObjectId(id)}, {"$set": updated_employee})  
        return redirect(url_for('home'))  
    return render_template('edit_employee.html', employee=employee)  

@app.route('/delete/<id>', methods=['GET'])  
def delete_employee(id):  
    if 'email' not in session:  
        return redirect('/')  
    mongo.db.employees.delete_one({"_id": ObjectId(id)})  
    return redirect(url_for('home'))  

if __name__ == '__main__':  
    app.run(debug=True)  