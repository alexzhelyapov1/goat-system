from flask import render_template, redirect, url_for, flash, request, jsonify, Response
import json
from flask_login import login_required, current_user
from app.movies import bp
from app.services.movie_service import MovieService
from app.schemas import MovieCreate, MovieSchema
from pydantic import ValidationError

@bp.route('/movies')
@login_required
def movies():
    movies = MovieService.get_movies_by_user(current_user.id)
    return render_template('movies/movies_list.html', movies=movies)

@bp.route('/movie/<int:movie_id>/json')
@login_required
def movie_json(movie_id):
    movie = MovieService.get_movie(movie_id)
    if movie.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    return jsonify(MovieSchema.model_validate(movie).model_dump(mode="json"))

@bp.route('/movies/create', methods=['GET', 'POST'])
@login_required
def create_movie():
    if request.method == 'POST':
        try:
            movie_data = MovieCreate(**request.form)
            MovieService.create_movie(movie_data, current_user.id)
            flash('Movie created successfully!')
            return redirect(url_for('movies.movies'))
        except ValidationError as e:
            flash(str(e.errors()))
            return redirect(url_for('movies.create_movie'))
    return render_template('movies/movie_form.html')

@bp.route('/movies/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def edit_movie(movie_id):
    movie = MovieService.get_movie(movie_id)
    if movie.user_id != current_user.id:
        flash('You are not authorized to edit this movie.')
        return redirect(url_for('movies.movies'))
    if request.method == 'POST':
        try:
            movie_data = MovieCreate(**request.form)
            MovieService.update_movie(movie_id, movie_data)
            flash('Movie updated successfully!')
            return redirect(url_for('movies.movies'))
        except ValidationError as e:
            flash(str(e.errors()))
            return redirect(url_for('movies.edit_movie', movie_id=movie_id))
    return render_template('movies/movie_form.html', movie=movie)

@bp.route('/movie/delete/<int:movie_id>', methods=['POST'])
@login_required
def delete_movie(movie_id):
    movie = MovieService.get_movie(movie_id)
    if movie.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    MovieService.delete_movie(movie_id)
    flash('Movie deleted successfully!')
    return jsonify({'success': True})

@bp.route('/movies/export')
@login_required
def export_movies():
    fields = request.args.getlist('fields')
    movies = MovieService.get_movies_by_user(current_user.id)
    
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
                MovieService.create_movie(movie, current_user.id)
            flash('Movies imported successfully!')
        except (json.JSONDecodeError, ValidationError) as e:
            flash(f'Error importing movies: {e}')
        return redirect(url_for('movies.movies'))
