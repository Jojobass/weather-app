from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
import sys
import requests
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)
app.config.update(SECRET_KEY=os.urandom(24))


class City(db.Model):
    __tablename__ = 'city_table'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(85), nullable=False, unique=True)


db.create_all()

all_weather_cards = []


# creates a dict with needed info and appends it to all_weather_cards
def create_card(temp_weather_card, temp_id):
    # checks time of day
    if temp_weather_card['dt'] < temp_weather_card['sys']['sunrise'] - 900 or temp_weather_card['dt'] > temp_weather_card['sys']['sunset'] + 900:
        temp_time_of_day = 'night'
    elif temp_weather_card['sys']['sunrise'] + 5400 < temp_weather_card['dt'] < temp_weather_card['sys']['sunset'] - 5400:
        temp_time_of_day = 'day'
    else:
        temp_time_of_day = 'evening-morning'

    all_weather_cards.append({
        'city': temp_weather_card['name'].upper(),
        'time_of_day': temp_time_of_day,
        'degrees': round(temp_weather_card['main']['temp']),
        'state': temp_weather_card['weather'][0]['main'],
        'id': temp_id
    })


# gets weather info for all city-names stored in db
def get_cards_info():
    all_weather_cards.clear()
    rows_to_delete = []
    # finds info about every city in list on the internet
    for name, temp_id in City.query.with_entities(City.name, City.id).all():
        temp_weather_card = requests.get(f'http://api.openweathermap.org/data/2.5/weather?q={name}&appid=7d41501380650a285bafa9c114d099bb&units=metric').json()
        # if no info was found, appends id to list 'to delete' and flashes message
        if temp_weather_card['cod'] != 200:
            rows_to_delete.append(temp_id)
            flash("The city doesn't exist!")
        else:
            create_card(temp_weather_card, temp_id)
    # deletes all rows in db with IDs in this list
    for id_to_delete in rows_to_delete:
        City.query.filter(City.id == id_to_delete).delete()
        db.session.commit()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        get_cards_info()
        return render_template('index.html', all_weather_cards=all_weather_cards)
    else:
        # saves data into the table
        temp_city = City(name=request.form["city_name"].upper())
        # commits changes
        db.session.add(temp_city)
        # if this city is in the db, doesn't append and flashes message
        try:
            db.session.commit()
        except Exception:
            flash("The city has already been added to the list!")
        return redirect('/')


# 'x' button leads here
@app.route('/delete/<city_id>', methods=['POST'])
def delete(city_id):
    city = City.query.filter_by(id=city_id).first()
    db.session.delete(city)
    db.session.commit()
    return redirect('/')


# don't change the following way to run flask:
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run(debug=True)
