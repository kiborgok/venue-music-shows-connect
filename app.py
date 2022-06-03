#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from crypt import methods
from email.policy import default
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120), nullable=True)
    image_link = db.Column(db.String(500), nullable=True)
    facebook_link = db.Column(db.String(120), nullable=True)
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(600), nullable=True)
    website = db.Column(db.String(120), nullable=True)
    genres = db.Column(db.ARRAY(db.String(120)))
    shows = db.relationship('Show', backref='venues', lazy=True, cascade="all, delete")

    def __repr__(self):
        return f'<Venue {self.name} {self.city} {self.state}>'
    
    @property 
    def upcoming_shows(self):
      upcoming_shows = []
      for show in self.shows:
        artist = Artist.query.get(show.artist_id)
        if show.start_time > datetime.now():
          upcoming_shows.append({
          "artist_id": show.artist_id,
          "artist_name": artist.name,
          "artist_image_link": artist.image_link,
          "start_time": show.start_time
          })
      return upcoming_shows
    
    @property
    def num_upcoming_shows(self):
      return len(self.upcoming_shows)

    @property
    def past_shows(self):
      past_shows = []
      for show in self.shows:
        artist = Artist.query.get(show.artist_id)
        if show.start_time < datetime.now():
          past_shows.append({
          "artist_id": show.artist_id,
          "artist_name": artist.name,
          "artist_image_link": artist.image_link,
          "start_time": show.start_time
          })
      return past_shows

    @property
    def num_past_shows(self):
      return len(self.past_shows)
    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500), nullable=True)
    facebook_link = db.Column(db.String(120), nullable=True)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website = db.Column(db.String(500), nullable=True)
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120), nullable=True)
    shows = db.relationship('Show', backref='artists', lazy=True)

    def __repr__(self):
        return f'<Artist {self.name} >'

    @property 
    def upcoming_shows(self):
      upcoming_shows = []
      for show in self.shows:
        venue = Venue.query.get(show.venue_id)
        if show.start_time > datetime.now():
          upcoming_shows.append({
          "venue_id": show.venue_id,
          "venue_name": venue.name,
          "venue_image_link": venue.image_link,
          "start_time": show.start_time
          })
      return upcoming_shows
    
    @property
    def num_upcoming_shows(self):
      return len(self.upcoming_shows)

    @property
    def past_shows(self):
      past_shows = []
      for show in self.shows:
        venue = Venue.query.get(show.venue_id)
        if show.start_time < datetime.now():
          past_shows.append({
          "venue_id": show.venue_id,
          "venue_name": venue.name,
          "venue_image_link": venue.image_link,
          "start_time": show.start_time
          })
      return past_shows

    @property
    def num_past_shows(self):
      return len(self.past_shows)

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
    __tablename__ = 'shows'
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.now)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  if isinstance(value, str):
    date = dateutil.parser.parse(value)
  else:
    date = value
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  venues = Venue.query.all()
  unique_city_states = set()
  for venue in venues:
      unique_city_states.add((venue.city, venue.state))
  for city_state in unique_city_states:
    city = city_state[0]
    state = city_state[1]
    venues_in_city = Venue.query.filter_by(city=city, state=state).all()
    data.append({
      "city": city,
      "state": state,
      "venues": venues_in_city
      })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term', '')
  venues = Venue.query.filter(Venue.name.ilike('%' + search_term + '%')).all()
  data = []
  for venue in venues:
    data.append({
      "id": venue.id,
      "name": venue.name
    })
  response = {
    "count": len(data),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>', methods=['GET'])
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  data = Venue.query.get(venue_id)
  data.upcoming_shows_count = data.num_upcoming_shows
  data.past_shows_count = data.num_past_shows
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try:
    # TODO: insert form data as a new Venue record in the db, instead
    form = VenueForm(request.form)
    name = form.name.data
    city = form.city.data
    state = form.state.data
    address = form.address.data
    phone = form.phone.data
    genres = form.genres.data
    seeking_talent = form.seeking_talent.data
    facebook_link = form.facebook_link.data
    website = form.website_link.data
    image_link = form.image_link.data
    seeking_description = form.seeking_description.data

    venue = Venue(name=name, city=city, state=state, address=address,
                    phone=phone, genres=genres, facebook_link=facebook_link,
                    website=website, image_link=image_link,
                    seeking_talent=seeking_talent,
                    seeking_description=seeking_description)
    db.session.add(venue)
    db.session.commit()
    # TODO: modify data to be the data object returned from db insertion
    if venue:
      data = {
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_description,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
      }
    # on successful db insert, flash success
    flash('Venue ' + data.name + ' was successfully listed!')
  except:
    db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    print(sys.exc_info())
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  try:
      venue = Venue.query.get(venue_id)
      db.session.delete(venue)
      db.session.commit()
  except:
      db.session.rollback()
      error = True
  finally:
      db.session.close()
  if error:
      server_error(500)
  
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return redirect(url_for('home'))
#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term', '')
  artists = Artist.query.filter(Artist.name.ilike('%' + search_term + '%')).all()
  data = []
  for artist in artists:
    data.append({
      "id": artist.id,
      "name": artist.name
    })
  response = {
    "count": len(data),
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
   # TODO: replace with real artist data from the artist table, using artist_id
  data = Artist.query.get(artist_id)
  data.genres = data.genres.strip('}{').split(',')
  data.upcoming_shows_count = data.num_upcoming_shows
  data.past_shows_count = data.num_past_shows

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist_data = Artist.query.get(artist_id)
  artist_data.website_link = artist_data.website
  artist={
    "id": artist_data.id,
    "name": artist_data.name,
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  form = ArtistForm(obj=artist_data)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
      artist = Artist.query.filter_by(id=artist_id).first()
      form = ArtistForm(request.form)
      artist.name = form.name.data
      artist.city = form.city.data
      artist.state = form.state.data
      artist.phone = form.phone.data
      artist.genres = form.genres.data
      artist.seeking_venue = form.seeking_venue.data
      artist.facebook_link = form.facebook_link.data
      artist.website = form.website_link.data
      artist.image_link = form.image_link.data
      artist.seeking_description = form.seeking_description.data

      db.session.commit()
      flash('Artist ' + form.name.data + ' was successfully Updated!')
  except:
    db.session.rollback()
    # TODO: on unsuccessful db update, flash an error instead.
    flash('An error occurred. Artist ' + form.name.data + ' could not be updated.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    print(sys.exc_info())
  finally:
    db.session.close()


  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue_data = Venue.query.get(venue_id)
  venue_data.website_link = venue_data.website
  venue={
    "id": venue_data.id,
    "name": venue_data.name,
  }
  # TODO: populate form with values from venue with ID <venue_id>
  form = VenueForm(obj=venue_data)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  try:
      venue = Venue.query.filter_by(id=venue_id).first()
      form = VenueForm(request.form)
      venue.name = form.name.data
      venue.city = form.city.data
      venue.state = form.state.data
      venue.phone = form.phone.data
      venue.genres = form.genres.data
      venue.seeking_talent = form.seeking_talent.data
      venue.facebook_link = form.facebook_link.data
      venue.website = form.website_link.data
      venue.image_link = form.image_link.data
      venue.seeking_description = form.seeking_description.data

      db.session.commit()
      flash('Venue ' + form.name.data + ' was successfully Updated!')
  except:
    db.session.rollback()
    # TODO: on unsuccessful db update, flash an error instead.
    flash('An error occurred. Venue ' + form.name.data + ' could not be updated.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    print(sys.exc_info())
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    try:
      # TODO: insert form data as a new Artist record in the db, instead
      form = ArtistForm(request.form)
      name = form.name.data
      city = form.city.data
      state = form.state.data
      phone = form.phone.data
      genres = form.genres.data
      seeking_venue = form.seeking_venue.data
      facebook_link = form.facebook_link.data
      website = form.website_link.data
      image_link = form.image_link.data
      seeking_description = form.seeking_description.data

      artist = Artist(name=name, city=city, state=state,
                      phone=phone, genres=genres, facebook_link=facebook_link,
                      website=website, image_link=image_link,
                      seeking_venue=seeking_venue,
                      seeking_description=seeking_description)
      db.session.add(artist)
      db.session.commit()
      # TODO: modify data to be the data object returned from db insertion
      print(artist)
      if artist:
        data = {
        "name": artist.name
        }
      # on successful db insert, flash success
      flash('Artist ' + data["name"] + ' was successfully listed!')
    except:
      db.session.rollback()
      # TODO: on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
      # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
      print(sys.exc_info())
    finally:
      db.session.close()
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
    # TODO: replace with real venues data.
  data = []
  shows = Show.query.all()
  for show in shows:
    artist = Artist.query.get(show.artist_id)
    venue = Venue.query.get(show.venue_id)
    data.append({
      "venue_id": show.venue_id,
      "venue_name": venue.name,
      "artist_id": show.artist_id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": show.start_time
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  try:
    form = ShowForm(request.form)
    artist_id = form.artist_id.data
    venue_id = form.venue_id.data
    start_time = form.start_time.data

    show = Show(artist_id=artist_id,venue_id=venue_id,start_time=start_time)
    db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
