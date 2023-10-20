from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash, generate_password_hash
import numpy as np
import pandas as pd
import pickle
import joblib

app = Flask(__name__)

app.secret_key = 'kuncisecret'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'db_prediction'
mysql = MySQL(app)

@app.route('/')
def index():
    if 'loggedin' in session:
        return render_template('index.html')
    flash('Harap Login Terlebih dahulu', 'danger')
    return redirect(url_for('login'))

@app.route('/registrasi', methods=('GET', 'POST'))
def registrasi():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        level = request.form['level']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM tb_login WHERE username=%s OR email=%s', (username, email, ))
        akun = cursor.fetchone()
        if akun is None:
            cursor.execute('INSERT INTO tb_login (username, email, password, level) VALUES (%s, %s, %s, %s)', (username, email, generate_password_hash(password), level))
            mysql.connection.commit()
            flash('Registration Successful... Please Click Login', 'success')
        else :
            flash('Username or Email already exists.. Please Try Again', 'danger')
    return render_template('registrasi.html')

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM tb_login WHERE email=%s', (email, ))
        akun = cursor.fetchone()
        if akun is None:
            flash('Login Failed!!! Check Your Username', 'danger')
        elif not check_password_hash(akun[3], password):
            flash('Login Failed!!! Check Your Password', 'danger')
        else:
            session['loggedin'] =  True
            session['username'] = akun[1]
            session['level'] = akun[4]
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/prediksi')
def prediksi():
    return render_template('prediksi.html')

@app.route('/prediksi_lama_rawat_inap')
def prediksi_lama_rawat_inap():
    return render_template('prediksi_lama_rawat_inap.html')

def ValuePredictorMortalitas(to_predict_list):
    to_predict = np.array(to_predict_list).reshape(1, 17)
    loaded_model = joblib.load('model_xgb_best_mortalitas.joblib')
    result = loaded_model.predict(to_predict)
    return result[0]

def ValuePredictorRawatInap(to_predict_list):
    to_predict = np.array(to_predict_list).reshape(1, 17)
    loaded_model = joblib.load('model_xgb_best_rawat.joblib')
    result = loaded_model.predict(to_predict)
    return result[0]
 
@app.route('/result', methods = ['POST'])
def result():
    if request.method == 'POST':
        to_predict_list = request.form.to_dict()
        to_predict_list = list(to_predict_list.values())
        to_predict_list = list(map(float, to_predict_list))
        resultMortalitas = ValuePredictorMortalitas(to_predict_list)
    
        if int(resultMortalitas) == 1:
            prediction_label_mortalitas ='Pasien Berpotensi Meninggal / Potential patients are dead'
        else:
            prediction_label_mortalitas ='Pasien Berpotensi Sembuh / Patients with potential recovery'  

        return render_template("result.html", predictionMortalitas = prediction_label_mortalitas )

@app.route('/result_lama_rawat_inap', methods = ['POST'])
def result_lama_rawat_inap():
    if request.method == 'POST':
        to_predict_list = request.form.to_dict()
        to_predict_list = list(to_predict_list.values())
        to_predict_list = list(map(float, to_predict_list))
        resultRawatInap = ValuePredictorRawatInap(to_predict_list)
        
        if int(resultRawatInap) == 1:
            prediction_label_rawat_inap ='Lebih Dari 7 Hari (Tidak Standar) / More than 7 days (Non-standard)'
        else:
            prediction_label_rawat_inap ='Kurang dari sama dengan 7 Hari (Standar) / Less than equal to 7 Days (Standard)' 

        return render_template("result_lama_rawat_inap.html", predictionRawatInap = prediction_label_rawat_inap )

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    session.pop('level', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
