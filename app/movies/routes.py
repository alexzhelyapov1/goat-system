from flask import render_template, redirect, url_for, flash, request, jsonify
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
            MovieService.create_movie(movie_data)
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
