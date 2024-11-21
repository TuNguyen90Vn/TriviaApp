import unittest
import json
from flaskr import create_app
from models import db, Question, Category
from sqlalchemy import text
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        # Load database configuration from environment variables
        self.database_name = os.getenv('DATABASE_NAME_TEST')
        self.database_user = os.getenv('DATABASE_USER')
        self.database_password = os.getenv('DATABASE_PASSWORD')
        self.database_host = os.getenv('DATABASE_HOST')
        self.database_path = f"postgresql://{self.database_user}:{self.database_password}@{self.database_host}/{self.database_name}"

        # Create app with the test configuration
        self.app = create_app({
            "SQLALCHEMY_DATABASE_URI": self.database_path,
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "TESTING": True
        })
        self.client = self.app.test_client()

        # Bind the app to the current context and create all tables
        with self.app.app_context():
            db.create_all()

        # Sample data
        self.new_question = {
            'question': 'What is the capital of France?',
            'answer': 'Paris',
            'difficulty': 1,
            'category': '1'
        }

    def tearDown(self):
        """Executed after each test"""
        with self.app.app_context():
            # Drop tables with CASCADE using SQLAlchemy's text function
            db.session.execute(text('DROP TABLE IF EXISTS questions CASCADE;'))
            db.session.execute(text('DROP TABLE IF EXISTS categories CASCADE;'))
            db.session.commit()

            # Recreate tables for subsequent tests
            db.create_all()

    def test_get_categories(self):
        """Test retrieving all categories"""
        with self.app.app_context():
            category = Category(type='Science')
            db.session.add(category)
            db.session.commit()

        response = self.client.get('/categories')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['categories'])
        self.assertTrue(data['success'])

    def test_404_get_questions_by_invalid_category(self):
        """Test 404 error for requesting questions from an invalid category"""
        response = self.client.get('/categories/999/questions')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'resource not found')

    def test_get_questions(self):
        """Test retrieving paginated questions"""
        with self.app.app_context():
            category = Category(type='Science')
            db.session.add(category)
            db.session.commit()

            question = Question(
                question='Test question',
                answer='Test answer',
                category=str(category.id),
                difficulty=1
            )
            db.session.add(question)
            db.session.commit()

        response = self.client.get('/questions?page=1')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['questions'])
        self.assertTrue(data['total_questions'])
        self.assertTrue(data['categories'])

    def test_404_get_questions_beyond_valid_page(self):
        """Test 404 error for requesting questions beyond valid page number"""
        response = self.client.get('/questions?page=1000')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'resource not found')

    def test_delete_question(self):
        """Test deleting a question"""
        with self.app.app_context():
            category = Category(type='Science')
            db.session.add(category)
            db.session.commit()

            question = Question(
                question='Test question',
                answer='Test answer',
                category=str(category.id),
                difficulty=1
            )
            db.session.add(question)
            db.session.commit()

            question_id = question.id

        response = self.client.delete(f'/questions/{question_id}')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['deleted'], question_id)

    def test_404_delete_nonexistent_question(self):
        """Test 404 error for attempting to delete a nonexistent question"""
        response = self.client.delete('/questions/1000')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'resource not found')

    def test_create_question(self):
        """Test creating a new question"""
        response = self.client.post('/questions', json=self.new_question)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(data['success'])
        self.assertTrue(data['created'])

    def test_422_create_question_with_incomplete_data(self):
        """Test 422 error for creating a question with incomplete data"""
        response = self.client.post('/questions', json={
            "question": "What is Python?",
            "answer": ""
        })
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 422)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'unprocessable entity')

    def test_search_questions(self):
        """Test searching for questions"""
        with self.app.app_context():
            category = Category(type='Science')
            db.session.add(category)
            db.session.commit()

            question = Question(
                question='What is the capital of France?',
                answer='Paris',
                category=str(category.id),
                difficulty=1
            )
            db.session.add(question)
            db.session.commit()

        response = self.client.post('/questions/search', json={'searchTerm': 'capital'})
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['questions'])
        self.assertTrue(data['total_questions'])

    def test_422_search_questions_with_empty_search_term(self):
        """Test 422 error for searching questions with an empty search term"""
        response = self.client.post('/questions/search', json={'searchTerm': ''})
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 422)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'unprocessable entity')

    def test_get_questions_by_category(self):
        """Test retrieving questions by category"""
        with self.app.app_context():
            # Insert category into the database
            category = Category(type='Science')
            db.session.add(category)
            db.session.commit()

            # Refetch the category to ensure it is bound to the session
            category = Category.query.filter_by(type='Science').one_or_none()

            # Insert a question into the database
            question = Question(
                question='Test question',
                answer='Test answer',
                category=str(category.id),
                difficulty=1
            )
            db.session.add(question)
            db.session.commit()

            # Test the endpoint
            response = self.client.get(f'/categories/{category.id}/questions')
            data = json.loads(response.data)

            self.assertEqual(response.status_code, 200)
            self.assertTrue(data['questions'])
            self.assertEqual(data['current_category'], category.id)

    def test_play_quiz(self):
        """Test playing quiz"""
        with self.app.app_context():
            # Insert category into the database
            category = Category(type='Science')
            db.session.add(category)
            db.session.commit()  # Commit to persist the category

            # Insert question into the database
            question = Question(
                question='Test question',
                answer='Test answer',
                category=str(category.id),  # Use the committed category ID
                difficulty=1
            )
            db.session.add(question)
            db.session.commit()  # Commit to persist the question

            # Ensure category ID is properly attached
            category_id = category.id

        # Test the endpoint
        response = self.client.post('/quizzes', json={
            'previous_questions': [],
            'quiz_category': {'id': str(category_id)}
        })
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['question'])

    def test_422_play_quiz_with_invalid_data(self):
        """Test 422 error for playing quiz with invalid data"""
        response = self.client.post('/quizzes', json={})
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 422)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'unprocessable entity')

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
