from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
from datetime import timedelta, datetime
from requests import Session, RequestException
from bs4 import BeautifulSoup as bs
from urllib.parse import urlparse, parse_qs
from datetime import datetime, date, timedelta
import re

class KretaUtils:

    def __init__(self, user_name: str, password: str, klik_id: str):
        kreta_login = self.login(user_name, password, klik_id)
        self.access_token = kreta_login.get('access_token')
        self.klik_id = klik_id
        self.request_headers = {
            'Authorization': f'Bearer {self.access_token}'
        }

    def login(self, user_name: str, password: str, klik_id: str) -> dict:

        # Load the refresh_token from a file, but handle the case if the file does not exist
        try:
            with open('refresh_token.txt', 'r') as f:
                refresh_token = f.read()
        except FileNotFoundError:
            refresh_token = None
        
        # Try to use the refresh_token to get a new access_token
        if refresh_token:
            try:
                with Session() as session:
                    data = {
                        "refresh_token": refresh_token,
                        "institute_code": klik_id,
                        "client_id": "kreta-ellenorzo-student-mobile-ios",
                        "grant_type": "refresh_token"
                    }
                    response = session.post("https://idp.e-kreta.hu/connect/token", data=data) 
                    response.raise_for_status()

                    # Save refresh_token to a file
                    refresh_token = response.json().get('refresh_token')
                    with open('refresh_token.txt', 'w') as f:
                        f.write(refresh_token)
                    return response.json()
            except Exception as e:
                # If the refresh_token is invalid, try to login with the username and password
                pass
         
        try:
            with Session() as session:
                url = "https://idp.e-kreta.hu/Account/Login?ReturnUrl=%2Fconnect%2Fauthorize%2Fcallback%3Fprompt%3Dlogin%26nonce%3DwylCrqT4oN6PPgQn2yQB0euKei9nJeZ6_ffJ-VpSKZU%26response_type%3Dcode%26code_challenge_method%3DS256%26scope%3Dopenid%2520email%2520offline_access%2520kreta-ellenorzo-webapi.public%2520kreta-eugyintezes-webapi.public%2520kreta-fileservice-webapi.public%2520kreta-mobile-global-webapi.public%2520kreta-dkt-webapi.public%2520kreta-ier-webapi.public%26code_challenge%3DHByZRRnPGb-Ko_wTI7ibIba1HQ6lor0ws4bcgReuYSQ%26redirect_uri%3Dhttps%253A%252F%252Fmobil.e-kreta.hu%252Fellenorzo-student%252Fprod%252Foauthredirect%26client_id%3Dkreta-ellenorzo-student-mobile-ios%26state%3Dkreten_student_mobile%26suppressed_prompt%3Dlogin"
                response = session.get(url)
                response.raise_for_status()

                soup = bs(response.text, 'html.parser')
                rvt = soup.find('input', {'name': '__RequestVerificationToken'})['value']

                payload = {
                    "ReturnUrl": "/connect/authorize/callback?prompt=login&nonce=wylCrqT4oN6PPgQn2yQB0euKei9nJeZ6_ffJ-VpSKZU&response_type=code&code_challenge_method=S256&scope=openid%20email%20offline_access%20kreta-ellenorzo-webapi.public%20kreta-eugyintezes-webapi.public%20kreta-fileservice-webapi.public%20kreta-mobile-global-webapi.public%20kreta-dkt-webapi.public%20kreta-ier-webapi.public&code_challenge=HByZRRnPGb-Ko_wTI7ibIba1HQ6lor0ws4bcgReuYSQ&redirect_uri=https%3A%2F%2Fmobil.e-kreta.hu%2Fellenorzo-student%2Fprod%2Foauthredirect&client_id=kreta-ellenorzo-student-mobile-ios&state=kreten_student_mobile&suppressed_prompt=login",
                    "IsTemporaryLogin": False,
                    "UserName": user_name,
                    "Password": password,
                    "InstituteCode": klik_id,
                    "loginType": "InstituteLogin",
                    "__RequestVerificationToken": rvt
                }

                url = "https://idp.e-kreta.hu/account/login"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                    'Content-Type': 'application/x-www-form-urlencoded',
                }

                response = session.post(url, headers=headers, data=payload, allow_redirects=False)
                response.raise_for_status()

                response = session.get("https://idp.e-kreta.hu/connect/authorize/callback?prompt=login&nonce=wylCrqT4oN6PPgQn2yQB0euKei9nJeZ6_ffJ-VpSKZU&response_type=code&code_challenge_method=S256&scope=openid%20email%20offline_access%20kreta-ellenorzo-webapi.public%20kreta-eugyintezes-webapi.public%20kreta-fileservice-webapi.public%20kreta-mobile-global-webapi.public%20kreta-dkt-webapi.public%20kreta-ier-webapi.public&code_challenge=HByZRRnPGb-Ko_wTI7ibIba1HQ6lor0ws4bcgReuYSQ&redirect_uri=https%3A%2F%2Fmobil.e-kreta.hu%2Fellenorzo-student%2Fprod%2Foauthredirect&client_id=kreta-ellenorzo-student-mobile-ios&state=kreten_student_mobile&suppressed_prompt=login", allow_redirects=False)
                response.raise_for_status()

                url = urlparse(response.headers['location'])
                code = parse_qs(url.query)['code'][0]

                data = {
                    "code": code,
                    "code_verifier": "DSpuqj_HhDX4wzQIbtn8lr8NLE5wEi1iVLMtMK0jY6c",
                    "redirect_uri": "https://mobil.e-kreta.hu/ellenorzo-student/prod/oauthredirect",
                    "client_id": "kreta-ellenorzo-student-mobile-ios",
                    "grant_type": "authorization_code"
                }
                response = session.post("https://idp.e-kreta.hu/connect/token", data=data)
                response.raise_for_status()

                # Save refresh_token to a file
                refresh_token = response.json().get('refresh_token')
                with open('refresh_token.txt', 'w') as f:
                    f.write(refresh_token)

            
            return response.json()
        except Exception as e:
            raise Exception(f"Login failed: {e}")    

    def get_school_year_dates(self):
        try:
            api_session = Session()
            response = api_session.get(f'https://{self.klik_id}.e-kreta.hu/ellenorzo/v3/sajat/Intezmenyek/TanevRendjeElemek', headers=self.request_headers)
            response.raise_for_status()
            return self.convert_school_year_dates(response.json())
        except RequestException as e:
            raise Exception(f"Failed to get school year dates: {e}")

    def get_student_data(self):
        try:
            api_session = Session()
            response = api_session.get(f'https://{self.klik_id}.e-kreta.hu/ellenorzo/v3/Sajat/TanuloAdatlap', headers=self.request_headers)
            response.raise_for_status()
            return self.convert_student_data(response.json())
        except RequestException as e:
            raise Exception(f"Failed to get student data: {e}")

    def get_homework(self, start_date: str, end_date: str):
        try:
            api_session = Session()
            response = api_session.get(f'https://{self.klik_id}.e-kreta.hu/ellenorzo/v3/Sajat/HaziFeladatok?datumTol={start_date}&datumIg={end_date}', headers=self.request_headers)
            response.raise_for_status()
            return self.convert_homework(response.json())
        except RequestException as e:
            raise Exception(f"Failed to get homework: {e}")

    def get_lessons(self, start_date: str, end_date: str):
        try:
            api_session = Session()
            response = api_session.get(f'https://{self.klik_id}.e-kreta.hu/ellenorzo/v3/Sajat/OrarendElemek?datumTol={start_date}&datumIg={end_date}', headers=self.request_headers)
            response.raise_for_status()
            #print(response.json())
            return self.convert_lessons(response.json())
        except RequestException as e:
            raise Exception(f"Failed to get lessons: {e}")

    def get_grades(self, start_date: str, end_date: str):
        try:
            api_session = Session()
            response = api_session.get(f'https://{self.klik_id}.e-kreta.hu/ellenorzo/v3/Sajat/Ertekelesek?datumTol={start_date}&datumIg={end_date}', headers=self.request_headers)
            response.raise_for_status()
            return self.convert_grades(response.json())
        except RequestException as e:
            raise Exception(f"Failed to get grades: {e}")
        
    def convert_school_year_dates(self, json_data):
        try:
            school_year_dates = []
            important_dates = [
                "Utolsó tanítási nap",
                "Első tanítási nap",
                "Első félév vége"
            ]
            for item in json_data:
                description = item['Naptipus']['Leiras']
                if any(re.search(f"{date}.*", description) for date in important_dates):
                    date = datetime.fromisoformat(item['Datum'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
                    school_year_dates.append({
                        'date': date,
                        'description': description
                    })
            return school_year_dates
        except (KeyError, ValueError) as e:
            raise Exception(f"Failed to convert school year dates: {e}")

    def convert_student_data(self, json_data):
        try:
            student_data = {
                "student_name": json_data.get("Nev"),
                "birth_name": json_data.get("SzuletesiNev"),
                "birth_place": json_data.get("SzuletesiHely"),
                "mother_name": json_data.get("AnyjaNeve"),
                "phone_number": json_data.get("Telefonszam"),
                "email": json_data.get("EmailCim"),
                "addresses": json_data.get("Cimek"),
                "birth_date": datetime.fromisoformat(json_data.get("SzuletesiDatum").replace('Z', '+00:00')).strftime('%Y-%m-%d') if json_data.get("SzuletesiDatum") else None,
                "school_name": json_data.get("Intezmeny", {}).get("TeljesNev")
            }
            return student_data
        except (KeyError, ValueError) as e:
            raise Exception(f"Failed to convert student data: {e}")

    def convert_lessons(self, json_data):
        try:
            lessons = []
            for item in json_data:
                if item.get("Tipus", {}).get("Nev") != "TanitasiOra" and item.get("Tipus", {}).get("Nev") != "OrarendiOra":
                    continue
                start_date = datetime.fromisoformat(item['KezdetIdopont'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
                end_date = datetime.fromisoformat(item['VegIdopont'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')

                lesson = {
                    'lesson_name': item['Nev'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'lesson_index': item['Oraszam'],
                    'classroom_name': item['TeremNeve']
                }
                lessons.append(lesson)

            lessons.sort(key=lambda x: (datetime.fromisoformat(x['start_date'].replace(" ", "T") + ":00").date(), x['lesson_index']))
            return lessons
        except (KeyError, ValueError) as e:
            raise Exception(f"Failed to convert lessons: {e}")

    def convert_grades(self, json_data):
        try:
            grades = []
            for item in json_data:
                grade_date = datetime.fromisoformat(item['RogzitesDatuma'].replace('Z', '+00:00')).strftime('%Y-%m-%d')

                grade = {
                    'grade_date': grade_date,
                    'topic': item['Tema'],
                    'grade_type': item['Tipus']['Leiras'],
                    'grade_value': item['SzovegesErtek'],
                    'lesson_name': item['Tantargy']['Nev']
                }
                grades.append(grade)
            return grades
        except (KeyError, ValueError) as e:
            raise Exception(f"Failed to convert grades: {e}")

    def convert_homework(self, json_data):
        try:
            homework_list = []
            today = date.today()
            for item in json_data:
                deadline_date = datetime.fromisoformat(item['HataridoDatuma'].replace('Z', '+00:00')).date()
                date_added = datetime.fromisoformat(item['RogzitesIdopontja'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
                deadline = deadline_date.strftime('%Y-%m-%d')

                homework = {
                    'lesson_name': item['TantargyNeve'],
                    'home_work_description': item['Szoveg'],
                    'deadline': deadline,
                    'date_added': date_added
                }
                homework_list.append(homework)
            return homework_list
        except (KeyError, ValueError) as e:
            raise Exception(f"Failed to convert homework: {e}")
        
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.permanent_session_lifetime = timedelta(days=7)

@app.route('/')
def home():
    if 'user_name' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('schedule'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_name = request.form.get('username')
        password = request.form.get('password')
        klik_id = request.form.get('klik_id')
        
        if not all([user_name, password, klik_id]):
            return render_template('login.html', error="Minden mező kitöltése kötelező")
        
        try:
            kreta_utils = KretaUtils(user_name, password, klik_id)
            session['user_name'] = user_name
            session['password'] = password  
            session['klik_id'] = klik_id
            
            student_data = kreta_utils.get_student_data()
            session['student_name'] = student_data['student_name']
            session['birth_name'] = student_data['birth_name']
            session['birth_place'] = student_data['birth_place']
            session['mother_name'] = student_data['mother_name']
            session['phone_number'] = student_data['phone_number']
            session['email'] = student_data['email']
            session['addresses'] = student_data['addresses']
            session['birth_date'] = student_data['birth_date']
            session['school_name'] = student_data['school_name']
            
            return redirect(url_for('schedule'))
        except Exception as e:
            return render_template('login.html', error=str(e))
            
    return render_template('login.html')

@app.route('/schedule')
def schedule():
    if 'user_name' not in session:
        return redirect(url_for('login'))
    try:
        kreta_utils = KretaUtils(session['user_name'], session['password'], session['klik_id'])
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=5)
        lessons = kreta_utils.get_lessons(week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d'))
        student_name = session['student_name']
        # Create separate lists for each day
        monday_lessons = []
        tuesday_lessons = []
        wednesday_lessons = []
        thursday_lessons = []
        friday_lessons = []

        # Sort lessons into appropriate days
        for lesson in lessons:
            lesson_date = datetime.strptime(lesson['start_date'], '%Y-%m-%d %H:%M')
            lesson_info = {
                'name': lesson['lesson_name'],
                'start': lesson_date.strftime('%H:%M'),
                'end': datetime.strptime(lesson['end_date'], '%Y-%m-%d %H:%M').strftime('%H:%M'),
                'room': lesson['classroom_name'],
                'index': lesson['lesson_index']
            }
            
            weekday = lesson_date.weekday()
            if weekday == 0:
                monday_lessons.append(lesson_info)
            elif weekday == 1:
                tuesday_lessons.append(lesson_info)
            elif weekday == 2:
                wednesday_lessons.append(lesson_info)
            elif weekday == 3:
                thursday_lessons.append(lesson_info)
            elif weekday == 4:
                friday_lessons.append(lesson_info)

        # Sort lessons by index for each day
        for day_lessons in [monday_lessons, tuesday_lessons, wednesday_lessons, thursday_lessons, friday_lessons]:
            day_lessons.sort(key=lambda x: x['index'])

        return render_template('schedule.html', 
                             monday=monday_lessons,
                             tuesday=tuesday_lessons,
                             wednesday=wednesday_lessons,
                             thursday=thursday_lessons,
                             friday=friday_lessons,  student_name = student_name)
    except Exception as e:
        return str(e)
    
@app.route('/grades')
def grades():
    if 'user_name' not in session:
        return redirect(url_for('login'))
    try:
        student_name = session['student_name']
        kreta_utils = KretaUtils(session['user_name'], session['password'], session['klik_id'])
        start_date = date.today().replace(day=1).strftime('%Y-%m-%d')
        end_date = date.today().strftime('%Y-%m-%d')
        grades = kreta_utils.get_grades(start_date, end_date)
        return render_template('grades.html', grades=grades, student_name=student_name)
    except Exception as e:
        return str(e)

@app.route('/assessments')
def assessments():
    if 'user_name' not in session:
        return redirect(url_for('login'))
    try:
        kreta_utils = KretaUtils(session['user_name'], session['password'], session['klik_id'])
        start_date = date.today().strftime('%Y-%m-%d')
        end_date = (date.today() + timedelta(days=12)).strftime('%Y-%m-%d')
        homework = kreta_utils.get_homework(start_date, end_date)
        return render_template('assessments.html', homework=homework)
    except Exception as e:
        return str(e)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)