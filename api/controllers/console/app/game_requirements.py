import json
import logging
from collections.abc import Generator

from flask import Response, stream_with_context
from flask_login import current_user
from flask_restful import Resource, reqparse

from controllers.console import api
from controllers.console.wraps import account_initialization_required
from core.errors.error import LLMBadRequestError
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
        parser = reqparse.RequestParser()
        parser.add_argument('input', type=str, required=True, location='json')
        parser.add_argument('session_id', type=str,
                            required=False, location='json')
        args = parser.parse_args()

        user_input = args['input']
        session_id = args.get('session_id')

        try:
            game_requirement_service = GameRequirementService()
            response_stream = game_requirement_service.analyze_game_requirement(
                app_model=app_model,
                user_id=current_user.id,
                input_data=user_input,
                session_id=session_id
            )
            return Response(
                stream_with_context(
                    self._generate_stream_response(response_stream)),
                content_type='text/event-stream'
            )
        except LLMBadRequestError as e:
            return {'error': str(e)}, 400
        except Exception as e:
            logger.exception("Error analyzing game requirements")
            return {'error': str(e)}, 500

    def _generate_stream_response(self, response_stream: Generator) -> Generator[str, None, None]:
        try:
            for chunk in response_stream:
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            logger.exception("Error generating stream response")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"


api.add_resource(GameRequirementAnalysisApi,
                 '/apps/<uuid:app_id>/game-requirements/analyze')
