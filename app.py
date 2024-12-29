import bcrypt
from flask import Flask, request, render_template, redirect, url_for
import boto3

app = Flask(__name__, template_folder='webapp-frontend/templates')

# DynamoDB Client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Users')

@app.route('/')
def register():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def handle_register():
    name = request.form['name']
    email = request.form['email']
    hobby = request.form['hobby']
    password = request.form['password']
    profile_pic = request.files['profile_pic']

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    profile_pic_url = None
    if profile_pic:
        s3 = boto3.client('s3')
        s3.upload_fileobj(profile_pic, 'kaifytestapp', email)
        profile_pic_url = f"https://kaifytestapp.s3.amazonaws.com/{email}"

    # Save data in DynamoDB
    table.put_item(
        Item={
            'email': email,
            'Name': name,
            'Hobby': hobby,
            'Password': hashed_password.decode('utf-8'),
            'Profile_pic': profile_pic_url
        }
    )
    print("Registration Successfull")
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    # Authenticate user
    email = request.form['email']
    password = request.form['password']
    try:
        response = table.get_item(Key={'email': email})
        user = response.get('Item')

        if user and bcrypt.checkpw(password.encode('utf-8'), user['Password'].encode('utf-8')):
            return redirect(url_for('welcome', name=user['Name']))
        return "Invalid credentials!"
    except boto3.exceptions.S3UploadFailedError as e:
        # Handle specific errors (e.g., connection issues)
        return f"Error occurred: {str(e)}"
    except Exception as e:
        # General error handling
        return f"Error occurred: {str(e)}"

@app.route('/welcome/<name>')
def welcome(name):
    return render_template('welcome.html', name=name)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
