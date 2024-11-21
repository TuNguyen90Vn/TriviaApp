import random

from flask import Flask, request, abort, jsonify
from flask_cors import CORS
from models import setup_db, Question, Category, db

QUESTIONS_PER_PAGE = 10

def paginate_items(request, items):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    return [item.format() for item in items[start:end]]


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    if test_config is None:
        setup_db(app)
    else:
        database_path = test_config.get('SQLALCHEMY_DATABASE_URI')
        setup_db(app, database_path=database_path)

    with app.app_context():
        db.create_all()

    # Set up CORS. Allow '*' for origins.
    CORS(app)

    # Set Access-Control-Allow headers
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,DELETE,OPTIONS')
        return response


    @app.route('/categories', methods=['GET'])
    def get_categories():
        try:
            categories = Category.query.all()
            formatted_categories = {category.id: category.type for category in categories}
            return jsonify({
                'success': True,
                'categories': formatted_categories
            })
        except:
            abort(404)


    @app.route('/questions', methods=['GET'])
    def get_questions():
        questions = Question.query.all()
        categories = Category.query.all()

        paginated_questions = paginate_items(request, questions)
        if not paginated_questions:
            abort(404)

        formatted_categories = {category.id: category.type for category in categories}
        return jsonify({
            'success': True,
            'questions': paginated_questions,
            'total_questions': len(questions),
            'categories': formatted_categories,
            'current_category': None
        })


    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        question = Question.query.get(question_id)
        if not question:
            abort(404)
        try:
            question.delete()
            return jsonify({'success': True, 'deleted': question_id})
        except:
            abort(422)


    @app.route('/questions', methods=['POST'])
    def create_question():
        data = request.get_json()
        question_text = data.get('question')
        answer = data.get('answer')
        category = data.get('category')
        difficulty = data.get('difficulty')

        if not (question_text and answer and category and difficulty):
            abort(422)

        try:
            question = Question(
                question=question_text, answer=answer,
                category=category, difficulty=difficulty
            )
            question.insert()
            return jsonify({'success': True, 'created': question.id}), 201
        except Exception as e:
            print(e)
            abort(422)


    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        data = request.get_json()
        search_term = data.get('searchTerm', '')
        if not search_term:
            abort(422)

        questions = Question.query.filter(Question.question.ilike(f'%{search_term}%')).all()
        paginated_questions = paginate_items(request, questions)
        return jsonify({
            'success': True,
            'questions': paginated_questions,
            'total_questions': len(questions),
            'current_category': None
        })


    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_by_category(category_id):
        category = Category.query.get(category_id)
        if not category:
            abort(404)

        questions = Question.query.filter(Question.category == str(category_id)).all()
        paginated_questions = paginate_items(request, questions)
        return jsonify({
            'success': True,
            'questions': paginated_questions,
            'total_questions': len(questions),
            'current_category': category_id
        })


    @app.route('/quizzes', methods=['POST'])
    def play_quiz():
        data = request.get_json()

        # Validate input data
        if not data or 'quiz_category' not in data or 'previous_questions' not in data:
            abort(422)

        quiz_category = data.get('quiz_category', {})
        previous_questions = data.get('previous_questions', [])

        category_id = int(quiz_category.get('id', 0))  # Default to 0 if id is not provided
        if category_id:
            questions = Question.query.filter(
                Question.category == str(category_id),
                Question.id.notin_(previous_questions)
            ).all()
        else:
            questions = Question.query.filter(
                Question.id.notin_(previous_questions)
            ).all()

        # Pick a random question from the filtered list
        if questions:
            question = random.choice(questions).format()
        else:
            question = None

        return jsonify({'success': True, 'question': question})


    # Error Handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'success': False, 'error': 404, 'message': 'resource not found'}), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({'success': False, 'error': 422, 'message': 'unprocessable entity'}), 422

    return app

