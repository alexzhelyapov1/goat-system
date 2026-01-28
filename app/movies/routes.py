from flask import render_template, redirect, url_for, flash, request, jsonify, Response, session
import json
from flask_login import login_required, current_user
from app.movies import bp
from app.services.movie_service import MovieService
from app.schemas import MovieCreate, MovieSchema
from pydantic import ValidationError, TypeAdapter
import httpx
from typing import List
from app.extensions import SessionLocal # Import SessionLocal for direct DB session


API_BASE_URL = "http://api:5001"

async def _make_api_request(method: str, endpoint: str, movie_id: int = None, json_data: dict = None):
    headers = {}
    if 'jwt_token' in session:
        headers["Authorization"] = f"Bearer {session['jwt_token']}"

    url = f"{API_BASE_URL}{endpoint}"
    if movie_id:
        url = f"{url}{movie_id}"

    async with httpx.AsyncClient() as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, json=json_data, headers=headers)
            elif method == "PUT":
                response = await client.put(url, json=json_data, headers=headers)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError("Unsupported HTTP method")

            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                flash("Your session has expired. Please log in again.")
                # Redirect to login page, this should be handled by client-side or
                # a global Flask before_request if all API calls need auth
            elif e.response.status_code == 403:
                flash("You are not authorized to perform this action.")
            else:
                flash(f"API Error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            flash(f"Network Error: Could not connect to API - {e}")
            raise

@bp.route('/movies')
@login_required
async def movies():
    try:
        response = await _make_api_request("GET", "/movies/")
        movies_data = response.json()
        movies = TypeAdapter(List[MovieSchema]).validate_python(movies_data)
    except httpx.RequestError:
        movies = []
    return render_template('movies/movies_list.html', movies=movies)

@bp.route('/movie/<int:movie_id>/json')
@login_required
async def movie_json(movie_id):
    try:
        response = await _make_api_request("GET", f"/movies/{movie_id}")
        return jsonify(response.json())
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/movies/create', methods=['GET', 'POST'])
@login_required
async def create_movie():
    if request.method == 'POST':
        try:
            movie_data = {
                "title": request.form['title'],
                "genre": request.form.get('genre'),
                "rating": int(request.form['rating']) if request.form['rating'] else None,
                "comment": request.form.get('comment')
            }
            await _make_api_request("POST", "/movies/", json_data=movie_data)
            flash('Movie created successfully!')
            return redirect(url_for('movies.movies'))
        except (ValidationError, httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
            flash(str(e))
            return redirect(url_for('movies.create_movie'))
    return render_template('movies/movie_form.html')

@bp.route('/movies/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
async def edit_movie(movie_id):
    if request.method == 'POST':
        try:
            movie_data = {
                "title": request.form['title'],
                "genre": request.form.get('genre'),
                "rating": int(request.form['rating']) if request.form['rating'] else None,
                "comment": request.form.get('comment')
            }
            await _make_api_request("PUT", f"/movies/{movie_id}", json_data=movie_data)
            flash('Movie updated successfully!')
            return redirect(url_for('movies.movies'))
        except (ValidationError, httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
            flash(str(e))
            return redirect(url_for('movies.edit_movie', movie_id=movie_id))
    
    try:
        response = await _make_api_request("GET", f"/movies/{movie_id}")
        movie = response.json()
    except httpx.RequestError as e:
        flash(f"Error fetching movie: {e}")
        return redirect(url_for('movies.movies'))

    return render_template('movies/movie_form.html', movie=movie)

@bp.route('/movie/delete/<int:movie_id>', methods=['POST'])
@login_required
async def delete_movie(movie_id):
    try:
        await _make_api_request("DELETE", f"/movies/{movie_id}")
        flash('Movie deleted successfully!')
        return jsonify({'success': True})
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/movies/export')
@login_required
def export_movies():
    fields = request.args.getlist('fields')
    # This still uses the service directly, as it's a specific feature.
    # This can be migrated later.
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
                # This still uses the service directly.
                # This can be migrated later.
                movie = MovieCreate(**movie_data)
                MovieService.create_movie(movie, current_user.id)
            flash('Movies imported successfully!')
        except (json.JSONDecodeError, ValidationError) as e:
            flash(f'Error importing movies: {e}')
        return redirect(url_for('movies.movies'))