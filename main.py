from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "secret111"

@app.route('/')
def home():

    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    
    return render_template('login.html')

app.run(port = 5500)