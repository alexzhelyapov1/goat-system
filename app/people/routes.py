from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.people import bp
from app.services.person_service import PersonService
from app.schemas import PersonCreate, PersonSchema
from pydantic import ValidationError

@bp.route('/people')
@login_required
def people():
    people = PersonService.get_people_by_user(current_user.id)
    return render_template('people/people_list.html', people=people)

@bp.route('/person/<int:person_id>/json')
@login_required
def person_json(person_id):
    person = PersonService.get_person(person_id)
    if person.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    return jsonify(PersonSchema.model_validate(person).model_dump(mode="json"))

@bp.route('/people/create', methods=['GET', 'POST'])
@login_required
def create_person():
    if request.method == 'POST':
        try:
            person_data = PersonCreate(**request.form)
            PersonService.create_person(person_data)
            flash('Person created successfully!')
            return redirect(url_for('people.people'))
        except ValidationError as e:
            flash(str(e.errors()))
            return redirect(url_for('people.create_person'))
    return render_template('people/person_form.html')

@bp.route('/people/edit/<int:person_id>', methods=['GET', 'POST'])
@login_required
def edit_person(person_id):
    person = PersonService.get_person(person_id)
    if person.user_id != current_user.id:
        flash('You are not authorized to edit this person.')
        return redirect(url_for('people.people'))
    if request.method == 'POST':
        try:
            person_data = PersonCreate(**request.form)
            PersonService.update_person(person_id, person_data)
            flash('Person updated successfully!')
            return redirect(url_for('people.people'))
        except ValidationError as e:
            flash(str(e.errors()))
            return redirect(url_for('people.edit_person', person_id=person_id))
    return render_template('people/person_form.html', person=person)

@bp.route('/person/delete/<int:person_id>', methods=['POST'])
@login_required
def delete_person(person_id):
    person = PersonService.get_person(person_id)
    if person.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    PersonService.delete_person(person_id)
    flash('Person deleted successfully!')
    return jsonify({'success': True})
