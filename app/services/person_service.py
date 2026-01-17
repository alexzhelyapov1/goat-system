from app import db
from app.models import Person
from app.schemas import PersonCreate
from flask_login import current_user

class PersonService:
    @staticmethod
    def get_people_by_user(user_id):
        return Person.query.filter_by(user_id=user_id).all()

    @staticmethod
    def get_person(person_id):
        return Person.query.get(person_id)

    @staticmethod
    def create_person(person_data: PersonCreate):
        person = Person(**person_data.model_dump(), user_id=current_user.id)
        db.session.add(person)
        db.session.commit()
        return person

    @staticmethod
    def update_person(person_id, person_data: PersonCreate):
        person = Person.query.get(person_id)
        for key, value in person_data.model_dump(exclude_unset=True).items():
            setattr(person, key, value)
        db.session.commit()
        return person

    @staticmethod
    def delete_person(person_id):
        person = Person.query.get(person_id)
        db.session.delete(person)
        db.session.commit()
