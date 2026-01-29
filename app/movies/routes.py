from flask import render_template, redirect, url_for, flash, request, jsonify, Response, session
import json
from flask_login import login_required
from app.movies import bp
from app.schemas import MovieSchema
from pydantic import ValidationError, TypeAdapter
import httpx
from typing import List
from app.api_client import make_api_request


@bp.route('/movies')
@login_required
def movies():
    try:
        response = make_api_request("GET", "/movies/")
        movies_data = response.json()
        movies = TypeAdapter(List[MovieSchema]).validate_python(movies_data)
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        flash(f"Could not load movies: {e}", "danger")
        movies = []
    return render_template('movies/movies_list.html', movies=movies)

@bp.route('/movie/<int:movie_id>/json')
@login_required
def movie_json(movie_id):
    try:
        response = make_api_request("GET", f"/movies/{movie_id}")
        return jsonify(response.json())
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/movies/create', methods=['GET', 'POST'])
@login_required
def create_movie():
    if request.method == 'POST':
        try:
            movie_data = {
                "title": request.form['title'],
                "genre": request.form.get('genre'),
                "rating": int(request.form['rating']) if request.form['rating'] else None,
                "comment": request.form.get('comment')
            }
            make_api_request("POST", "/movies/", json_data=movie_data)
            flash('Movie created successfully!', 'success')
            return redirect(url_for('movies.movies'))
        except (ValidationError, httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
            flash(str(e), 'danger')
            return redirect(url_for('movies.create_movie'))
    return render_template('movies/movie_form.html')

@bp.route('/movies/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def edit_movie(movie_id):
    if request.method == 'POST':
        try:
            movie_data = {
                "title": request.form['title'],
                "genre": request.form.get('genre'),
                "rating": int(request.form['rating']) if request.form['rating'] else None,
                "comment": request.form.get('comment')
            }
            make_api_request("PUT", f"/movies/{movie_id}", json_data=movie_data)
            flash('Movie updated successfully!', 'success')
            return redirect(url_for('movies.movies'))
        except (ValidationError, httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
            flash(str(e), 'danger')
            return redirect(url_for('movies.edit_movie', movie_id=movie_id))
    
    try:
        response = make_api_request("GET", f"/movies/{movie_id}")
        movie = response.json()
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        flash(f"Error fetching movie: {e}", 'danger')
        return redirect(url_for('movies.movies'))

    return render_template('movies/movie_form.html', movie=movie)

@bp.route('/movie/delete/<int:movie_id>', methods=['POST'])
@login_required
def delete_movie(movie_id):
    try:
        make_api_request("DELETE", f"/movies/{movie_id}")
        flash('Movie deleted successfully!', 'success')
        return jsonify({'success': True})
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        flash(f"Error deleting movie: {e}", 'danger')
        return jsonify({'error': str(e)}), 500

@bp.route('/movies/export')
@login_required
def export_movies():
    fields = request.args.getlist('fields')
    try:
        response = make_api_request("GET", "/movies/export", params={'fields': fields})
        movies_to_export = response.json()
        
        response_data = json.dumps(movies_to_export, ensure_ascii=False, indent=4)
        response = Response(response_data, mimetype='application/json; charset=utf-8')
        response.headers['Content-Disposition'] = 'attachment; filename=movies.json'
        return response
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        flash(f"Error exporting movies: {e}", 'danger')
        return redirect(url_for('movies.movies'))

@bp.route('/movies/import', methods=['POST'])
@login_required
def import_movies():
    if 'file' not in request.files:
        flash('No file part', 'warning')
        return redirect(url_for('movies.movies'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'warning')
        return redirect(url_for('movies.movies'))
    if file:
        try:
            movies_data = json.load(file)
            make_api_request("POST", "/movies/import", json_data=movies_data)
            flash('Movies imported successfully!', 'success')
        except (json.JSONDecodeError, httpx.RequestError, httpx.HTTPStatusError) as e:
            flash(f'Error importing movies: {e}', 'danger')
        return redirect(url_for('movies.movies'))