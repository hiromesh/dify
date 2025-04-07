import json
import logging
from collections.abc import Generator

from flask import Response, stream_with_context
from flask_login import current_user
from flask_restful import Resource, reqparse

from controllers.console import api
from controllers.console.app.error import NotFoundError
from controllers.console.decorators import account_initialization_required, app_initialization_required
from core.errors.error import LLMBadRequestError
from extensions.ext_database import db
from models.model import App
from services.game_requirement_service import GameRequirementService

logger = logging.getLogger(__name__)


class GameRequirementAnalysisApi(Resource):
    """
    Game requirement analysis API for processing and understanding game requirements
    """
    
    @account_initialization_required
    @app_initialization_required
    def post(self, app_model: App):
        """
        Analyze game requirements from user input
        
        Request body:
        - input: String, the user input for requirements analysis
        - session_id: Optional String, the session ID for continuing a conversation
        
        Returns:
        - A streaming response with processed game requirements
        """
        parser = reqparse.RequestParser()
        parser.add_argument('input', type=str, required=True, location='json')
        parser.add_argument('session_id', type=str, required=False, location='json')
        args = parser.parse_args()
        
        user_input = args['input']
        session_id = args.get('session_id')
        
        try:
            # Initialize the service
            game_requirement_service = GameRequirementService()
            
            # Run the analysis
            response_stream = game_requirement_service.analyze_game_requirement(
                app_model=app_model,
                user_id=current_user.id,
                input_data=user_input,
                session_id=session_id
            )
            
            # Return the streaming response
            return Response(
                stream_with_context(self._generate_stream_response(response_stream)),
                content_type='text/event-stream'
            )
            
        except LLMBadRequestError as e:
            return {'error': str(e)}, 400
        except Exception as e:
            logger.exception("Error analyzing game requirements")
            return {'error': str(e)}, 500
            
    def _generate_stream_response(self, response_stream: Generator) -> Generator[str, None, None]:
        """Generate a stream response from the response stream"""
        try:
            for chunk in response_stream:
                # Convert the chunk to JSON string and add data: prefix for SSE
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            logger.exception("Error generating stream response")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"


class GameRequirementSessionApi(Resource):
    """
    API for managing game requirement sessions
    """
    
    @account_initialization_required
    @app_initialization_required
    def get(self, app_model: App, session_id: str):
        """Get a specific game requirement session by ID"""
        try:
            game_requirement_service = GameRequirementService()
            session = game_requirement_service.get_session_by_id(session_id)
            
            if not session or session.app_id != app_model.id:
                raise NotFoundError("Session not found")
                
            return {
                'session_id': session.id,
                'status': session.status,
                'data': session.requirement_data_dict,
                'created_at': session.created_at.isoformat(),
                'updated_at': session.updated_at.isoformat()
            }
        except NotFoundError as e:
            return {'error': str(e)}, 404
        except Exception as e:
            logger.exception("Error retrieving game requirement session")
            return {'error': str(e)}, 500
            
    @account_initialization_required
    @app_initialization_required
    def put(self, app_model: App, session_id: str):
        """Update the status of a game requirement session"""
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('status', type=str, required=True, location='json')
            args = parser.parse_args()
            
            new_status = args['status']
            
            game_requirement_service = GameRequirementService()
            session = game_requirement_service.advance_session_status(session_id, new_status)
            
            return {
                'session_id': session.id,
                'status': session.status,
                'updated_at': session.updated_at.isoformat()
            }
        except Exception as e:
            logger.exception("Error updating game requirement session")
            return {'error': str(e)}, 500
            
    @account_initialization_required
    @app_initialization_required
    def delete(self, app_model: App, session_id: str):
        """Delete a game requirement session"""
        try:
            # Get the session first to verify it exists and belongs to this app
            game_requirement_service = GameRequirementService()
            session = game_requirement_service.get_session_by_id(session_id)
            
            if not session or session.app_id != app_model.id:
                raise NotFoundError("Session not found")
            
            # Delete from database
            db.session.delete(session)
            db.session.commit()
            
            return {'result': 'success'}
        except NotFoundError as e:
            return {'error': str(e)}, 404
        except Exception as e:
            logger.exception("Error deleting game requirement session")
            return {'error': str(e)}, 500


# Register API resources
api.add_resource(GameRequirementAnalysisApi, '/apps/<uuid:app_id>/game-requirements/analyze')
api.add_resource(GameRequirementSessionApi, '/apps/<uuid:app_id>/game-requirements/sessions/<string:session_id>')
