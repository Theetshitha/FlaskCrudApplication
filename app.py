from flask import Flask, render_template, request, redirect, url_for  
from flask_pymongo import PyMongo  
from bson.objectid import ObjectId  

app = Flask(__name__)  

 
app.config['MONGO_URI'] = "mongodb://localhost:27017/flaskCrudApp"  
mongo = PyMongo(app)  

db = mongo.db  
employees = db.employees  

@app.route('/')  
def home():  
    employee_records = employees.find()  
    return render_template('home.html', employees=employee_records)  

@app.route('/add', methods=['GET', 'POST'])  
def add_employee():  
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
        employees.insert_one(employee)  
        return redirect(url_for('home'))  
    return render_template('add_employee.html')  

@app.route('/edit/<id>', methods=['GET', 'POST'])  
def edit_employee(id):  
    employee = employees.find_one({"_id": ObjectId(id)})  
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
        employees.update_one({"_id": ObjectId(id)}, {"$set": updated_employee})  
        return redirect(url_for('home'))  

@app.route('/delete/<id>', methods=['GET'])  
def delete_employee(id):  
    employees.delete_one({"_id": ObjectId(id)})  
    return redirect(url_for('home'))  

if __name__ == '__main__':  
    app.run(debug=True)