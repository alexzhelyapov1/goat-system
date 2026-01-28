from flask import render_template, redirect, url_for, flash, request, jsonify, Response
import json
from flask_login import login_required, current_user
from app.movies import bp
from app.services.movie_service import MovieService
from app.schemas import MovieCreate, MovieSchema
from pydantic import ValidationError
from app.extensions import db # Added db import

@bp.route('/movies')
@login_required
def movies():
    return render_template('movies/movies_list.html')

@bp.route('/movies/export')
@login_required
def export_movies():
    fields = request.args.getlist('fields')
    movies = MovieService(db_session=db.session).get_movies_by_user(current_user.id)
    
    movies_to_export = []
    for movie in movies:
        movie_dict = MovieSchema.model_validate(movie).model_dump(mode="json")
        exported_movie = {field: movie_dict.get(field) for field in fields}
        movies_to_export.append(exported_movie)
        
    response_data = json.dumps(movies_to_export, ensure_ascii=False, indent=4)
    response = Response(response_data, mimetype='application/json; charset=utf-8')
    response.headers['Content-Disposition'] = 'attachment; filename=movies.json'
    return response

@bp.route('/movies/import', methods=['POST'])
@login_required
def import_movies():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('movies.movies'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('movies.movies'))
    if file:
        try:
            movies_data = json.load(file)
            for movie_data in movies_data:
                movie_data.pop('id', None)
                movie = MovieCreate(**movie_data)
                MovieService(db_session=db.session).create_movie(movie, current_user.id)
            flash('Movies imported successfully!')
        except (json.JSONDecodeError, ValidationError) as e:
            flash(f'Error importing movies: {e}')
        return redirect(url_for('movies.movies'))
