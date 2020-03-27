# import random
import re

from flask import abort, Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from sqlalchemy.sql.expression import func

from backend.database.models import Category, Question, setup_db

QUESTIONS_PER_PAGE = 10


def create_app():
    """
    Creates and sets up a Flask application
    :return: Flask application
    """
    app = Flask(__name__)
    setup_db(app)

    CORS(app, resources={r'/*': {'origins': '*'}})

    @app.after_request
    def set_headers(response):
        """
        Intercept response to add 'Access-Control-Allow' headers
        :param response: HTTP Response
        :return: Modified HTTP Response
        """
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization, true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET, PATCH, POST, DELETE, OPTIONS')
        return response

    @app.route('/categories', methods=['GET'])
    def get_all_categories():
        """
        Creates a dictionary of all categories
        :return: All categories
        """
        categories = {}
        for category in Category.query.all():
            categories[category.id] = category.type
        return jsonify({
            'categories': categories
        })

    @app.route('/questions', methods=['GET'])
    def get_questions():
        """
        Get all questions, categories and total questions from database
        :return: Questions, categories and total questions
        """
        categories = {}
        for category in Category.query.all():
            categories[category.id] = category.type
        questions = [question.format() for question in Question.query.all()]
        page = int(request.args.get('page', '0'))
        upper_limit = page * 10
        lower_limit = upper_limit - 10
        return jsonify({
            'questions': questions[
                         lower_limit:upper_limit] if page else questions,
            'total_questions': len(questions),
            'categories': categories
        })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        """
        Delete a question using question id
        :param question_id: Id of the question to be deleted
        :return: Id of the question that has been deleted
        """
        question = Question.query.get(question_id)
        if not question:
            return abort(404, f'No question found with id: {question_id}')
        question.delete()
        return jsonify({
            'deleted': question_id
        })

    @app.route('/questions', methods=['POST'])
    def post_question():
        """
        Adds a question to database
        :return: The question that is added
        """
        question = request.json.get('question')
        answer = request.json.get('answer')
        category = request.json.get('category')
        difficulty = request.json.get('difficulty')
        if not (question and answer and category and difficulty):
            return abort(400,
                         'Required question object keys missing from request '
                         'body')
        question_entry = Question(question, answer, category, difficulty)
        question_entry.insert()
        return jsonify({
            'question': question_entry.format()
        })

    @app.route('/search', methods=['POST'])
    def search():
        """
        Search for questions using the search term
        :return: Searched questions and total questions
        """
        search_term = request.json.get('searchTerm', '')
        questions = [question.format() for question in Question.query.all() if
                     re.search(search_term, question.question, re.IGNORECASE)]
        return jsonify({
            'questions': questions,
            'total_questions': len(questions)
        })

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_by_category(category_id):
        """
        Gets questions from database and filters them based on category
        :param category_id: The category for which questions are to be filtered
        :return: Filtered questions, total questions and current category
        """
        if not category_id:
            return abort(400, 'Invalid category id')
        questions = [question.format() for question in
                     Question.query.filter(Question.category == category_id)]
        return jsonify({
            'questions': questions,
            'total_questions': len(questions),
            'current_category': category_id
        })

    @app.route('/quizzes', methods=['POST'])
    def get_quiz_questions():
        """
        Gets question for quiz
        :return: Uniques quiz question or None
        """
        previous_questions = request.json.get('previous_questions')
        quiz_category = request.json.get('quiz_category')
        if not quiz_category:
            return abort(400, 'Required keys missing from request body')
        category_id = int(quiz_category.get('id'))
        questions = Question.query.filter(
            Question.category == category_id,
            ~Question.id.in_(previous_questions)) if category_id else \
            Question.query.filter(~Question.id.in_(previous_questions))
        question = questions.order_by(func.random()).first()
        if not question:
            return jsonify({})
        return jsonify({
            'question': question.format()
        })

    # Error Handler
    @app.errorhandler(HTTPException)
    def http_exception_handler(error):
        """
        HTTP error handler for all endpoints
        :param error: HTTPException containing code and description
        :return: error: HTTP status code, message: Error description
        """
        return jsonify({
            'success': False,
            'error': error.code,
            'message': error.description
        }), error.code

    @app.errorhandler(Exception)
    def exception_handler(error):
        """
        Generic error handler for all endpoints
        :param error: Any exception
        :return: error: HTTP status code, message: Error description
        """
        return jsonify({
            'success': False,
            'error': 500,
            'message': f'Something went wrong: {error}'
        }), 500

    return app
