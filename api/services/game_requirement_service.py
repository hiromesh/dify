import json
import logging
from collections.abc import Generator
from datetime import datetime
from typing import Any, Optional

from core.model_manager import ModelManager
from core.model_runtime.entities.message_entities import AssistantPromptMessage, UserPromptMessage
from core.model_runtime.entities.model_entities import ModelType
from core.workflow_generator.agents.requirement_understanding_agent import RequirementUnderstandingAgent
from extensions.ext_database import db
from models import App
from models.game_requirements import GameRequirementSession

logger = logging.getLogger(__name__)


class GameRequirementService:
    """
    Service for managing game requirement analysis sessions
    """

    def get_or_create_session(self, app_model: App, user_id: str,
                              session_id: Optional[str] = None) -> GameRequirementSession:
        """
        Get an existing session or create a new one
        """
        if session_id:
            session = db.session.query(GameRequirementSession).filter(
                GameRequirementSession.id == session_id,
                GameRequirementSession.tenant_id == app_model.tenant_id,
                GameRequirementSession.app_id == app_model.id
            ).first()

            if session:
                return session

        new_session = GameRequirementSession.create(
            tenant_id=app_model.tenant_id,
            app_id=app_model.id,
            user_id=user_id
        )

        db.session.add(new_session)
        db.session.commit()
        return new_session

    def update_session(self, session_id: str, requirement_data: dict[str, Any],
                       history_messages: Optional[list] = None, status: Optional[str] = None) -> GameRequirementSession:
        """
        Update session data, history messages, and status
        """
        session = db.session.query(GameRequirementSession).filter(
            GameRequirementSession.id == session_id
        ).first()

        if not session:
            raise ValueError(f"Session with id {session_id} not found")

        session.requirement_data = json.dumps(requirement_data)

        if history_messages is not None:
            session.history_messages = json.dumps(history_messages)

        if status:
            session.status = status

        session.updated_at = datetime.utcnow()
        db.session.commit()

        return session

    def analyze_game_requirement(self, app_model: App, user_id: str, input_data: str,
                                 session_id: Optional[str] = None) -> Generator[dict[str, Any], None, None]:
        """
        Analyze game requirements using the RequirementUnderstandingAgent

        """
        requirement_session = self.get_or_create_session(
            app_model, user_id, session_id)

        model_manager = ModelManager()
        model_instance = model_manager.get_model_instance(
            tenant_id=app_model.tenant_id,
            model_config={
                "model": "deepseek",
                "model_type": ModelType.LLM,
                "parameters": {
                    "temperature": 0.3,
                    "max_tokens": 4096
                }
            }
        )

        agent = RequirementUnderstandingAgent(
            model_instance=model_instance,
            model_parameters={"temperature": 0.3, "max_tokens": 4096},
            user_id=user_id
        )

        if requirement_session.history_messages:
            saved_messages = requirement_session.history_messages_list
            history_messages = []

            for msg in saved_messages:
                if msg.get('type') == 'user':
                    history_messages.append(UserPromptMessage(
                        content=msg.get('content', '')))
                elif msg.get('type') == 'assistant':
                    history_messages.append(AssistantPromptMessage(
                        content=msg.get('content', '')))

            agent.history_messages = history_messages

        response_stream = agent.run(input_data)

        for chunk in response_stream:
            serialized_messages = []
            for msg in agent.history_messages:
                msg_type = 'user' if isinstance(
                    msg, UserPromptMessage) else 'assistant'
                serialized_messages.append({
                    'type': msg_type,
                    'content': msg.content
                })

            self.update_session(
                requirement_session.id,
                chunk,
                serialized_messages
            )

            result = {
                "session_id": requirement_session.id,
                "status": requirement_session.status,
                "data": chunk
            }
            yield result

    def get_session_by_id(self, session_id: str) -> Optional[GameRequirementSession]:
        return db.session.query(GameRequirementSession).filter(
            GameRequirementSession.id == session_id
        ).first()

    def get_sessions_by_app(self, app_id: str, user_id: Optional[str] = None) -> list[GameRequirementSession]:
        query = db.session.query(GameRequirementSession).filter(
            GameRequirementSession.app_id == app_id
        )
        if user_id:
            query = query.filter(GameRequirementSession.user_id == user_id)
        return query.order_by(GameRequirementSession.updated_at.desc()).all()

    def advance_session_status(self, session_id: str, new_status: str) -> GameRequirementSession:
        session = self.get_session_by_id(session_id)
        if not session:
            raise ValueError(f"Session with id {session_id} not found")

        session.status = new_status
        session.updated_at = datetime.utcnow()
        db.session.commit()
        return session
