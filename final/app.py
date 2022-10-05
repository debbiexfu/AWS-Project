from crypt import methods
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import boto3
import json
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
import pymysql
import os
from botocore.exceptions import ClientError

app = Flask(__name__)


ACCESS_KEY = "AKIA4X7JWPVVPKMJWOFJ"
SECRET_KEY ="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"

ENDPOINT="testdb.cvavoczjlsdp.us-east-1.rds.amazonaws.com"
PORT="3306"
USER="admin"
PASSWORD="password1"
DB="testdb"

topic = 'arn:aws:sns:us-east-1:876126567786:dfu_final'

app = Flask(__name__)

email = '1'
password = '2'

@app.route('/')
def home():
    return render_template('intro.html')

@app.route('/notfound.html')
def notfound():
    return render_template('notfound.html')

@app.route('/login.html', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        global email
        email = request.form.get("email")
        global password
        password = request.form.get("password")
        print(email, password)
        try:
            conn=pymysql.connect(host=ENDPOINT, user=USER, password=PASSWORD, database=DB)
            cur = conn.cursor()
            cur.execute("SELECT * FROM userdetails;")
            query_results = cur.fetchall()
            print(email, password)
            print(query_results)
            for row in query_results:
                print(row[0], row[1])
                if row[0].__eq__(email) and row[1].__eq__(password):
                    return render_template('upload.html')
                else:
                    continue
            return render_template('register.html')
        except Exception as e:
            print("error login")
            return render_template('register.html')
        return redirect(url_for('upload.html'))
    else:
        return render_template('login.html')

@app.route('/register.html', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        r_email = request.form.get("r_email")
        r_password = request.form.get("r_password")
        conn=pymysql.connect(host=ENDPOINT, user=USER, password=PASSWORD, database=DB)
        cur = conn.cursor()
        print('db connected')
        print(email, password)
        try:
                cur.execute("INSERT INTO userdetails(email, password, filename) VALUES('"+r_email+"', '"+r_password+"','""');")
                print("Insert Success")
                conn.commit()
        except Exception as e:
                cur.execute("CREATE TABLE userdetails(email VARCHAR(20), password VARCHAR(20), filename VARCHAR(50))")
                cur.execute("INSERT INTO userdetails(email, password, filename) VALUES('"+r_email+"', '"+r_password+"','""');")
                print("Insert Success")
                conn.commit()
        cur.execute("SELECT * FROM userdetails;")
        query_results = cur.fetchall()
        print(query_results)
        return redirect(url_for('login'))
    else:
        return render_template('register.html')

@app.route('/upload.html', methods=['GET','POST'])
def upload():
    if request.method == 'POST':
        global email
        email = request.form.get("email")
        global password
        password = request.form.get("password")
        print(email, password)
        return render_template('upload.html')
    else:
        return render_template('upload.html')

@app.route('/add' , methods=['POST'])
def add():
        f = request.files['file']
        filename = f.filename.split("\\")[-1]
        f.save(secure_filename(filename))

        s3 = boto3.client('s3',aws_access_key_id = ACCESS_KEY,aws_secret_access_key = SECRET_KEY,region_name = 'us-east-1')
        s3.upload_file(filename, "dfu.final", filename,ExtraArgs={'GrantRead':'uri="http://acs.amazonaws.com/groups/global/AllUsers"'})


        print("db time")
        conn=pymysql.connect(host=ENDPOINT, user=USER, password=PASSWORD, database=DB)
        cur = conn.cursor()
        print('db connected')
        print(email, password, filename)
        try:
            cur.execute("INSERT INTO userdetails(email, password, filename) VALUES('"+email+"', '"+password+"','"+filename+"');")
            print("Insert Success")
            conn.commit()
        except Exception as e:
            cur.execute("CREATE TABLE userdetails(email VARCHAR(20), password VARCHAR(20), filename VARCHAR(50))")
            cur.execute("INSERT INTO userdetails(email, password, filename) VALUES('"+email+"', '"+password+"','"+filename+"');")
            print("Insert Success")
            conn.commit()
        cur.execute("SELECT * FROM userdetails;")

        #os.remove(filename)

        sns = boto3.client('sns',region_name='us-east-1',
                  aws_access_key_id=ACCESS_KEY,
                  aws_secret_access_key=SECRET_KEY)
        email1 = request.form.get("email1")
        response = sns.subscribe(TopicArn =topic,
                         Protocol='email',
                         Endpoint=email1)
        
        lambda_client = boto3.client('lambda',
        aws_access_key_id = ACCESS_KEY,
        aws_secret_access_key = SECRET_KEY,
        region_name = 'us-east-1')

        link = "https://s3.amazonaws.com/dfu.final/" + filename
        lambda_payload={"link":link}
        lambda_client.invoke(FunctionName='dfu_final',
                        InvocationType='Event',
                        Payload=json.dumps(lambda_payload))

        #s3_2 = boto3.resource('s3')
        #s3_2.Object('dfu.final', filename).delete()   
        return redirect(url_for('confirm'))


@app.route('/confirm.html')
def confirm():
    return render_template('confirm.html')

@app.route('/database.html', methods=['GET', 'POST'])
def database():
    if request.method == 'POST':
        search = request.form.get("dbuser")
        try:
            conn=pymysql.connect(host=ENDPOINT, user=USER, password=PASSWORD, database=DB)
            cur = conn.cursor()
            
            '''cur.execute("DROP TABLE userdetails;")
            print('db gone')'''

            print('db connected')
            cur.execute("SELECT * FROM userdetails;")
            query_results = cur.fetchall()
            print(query_results)
            file_list = []
            print('loop')
            for i in query_results:
                if i[0] == search:
                    if i[2] != '':
                        file_list.append(i[2])
            print(file_list)

            return render_template('database.html', files = file_list)
        except Exception as e:
            return render_template('notfound.html')
    else:
        return render_template('database.html')


if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True)
