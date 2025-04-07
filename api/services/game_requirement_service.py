import json
import logging
from collections.abc import Generator
from datetime import datetime
from typing import Any, Optional

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
            # Try to find existing session
            session = db.session.query(GameRequirementSession).filter(
                GameRequirementSession.id == session_id,
                GameRequirementSession.tenant_id == app_model.tenant_id,
                GameRequirementSession.app_id == app_model.id
            ).first()
            
            if session:
                return session
        
        # Create new session
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
        
        # Update data
        session.requirement_data = json.dumps(requirement_data)
        
        # Update history messages if provided
        if history_messages is not None:
            session.history_messages = json.dumps(history_messages)
        
        # Update status if provided
        if status:
            session.status = status
            
        session.updated_at = datetime.utcnow()
        db.session.commit()
        
        return session
    
    def analyze_game_requirement(self, app_model: App, user_id: str, input_data: str, 
                                session_id: Optional[str] = None) -> Generator[dict[str, Any], None, None]:
        """
        Analyze game requirements using the RequirementUnderstandingAgent
        
        Args:
            app_model: App model
            user_id: User ID
            input_data: User input text
            session_id: Optional session ID to continue existing session
            
        Returns:
            Generator yielding analysis results
        """
        # Get or create session
        requirement_session = self.get_or_create_session(app_model, user_id, session_id)
        
        # Initialize the agent
        # In a real implementation, you'd get this from a model manager or factory
        from core.model_runtime.entities.message_entities import AssistantPromptMessage, UserPromptMessage
        from services.model_service import ModelService
        
        model_service = ModelService()
        model_instance = model_service.get_default_model_instance(app_model.tenant_id)
        
        agent = RequirementUnderstandingAgent(
            model_instance=model_instance,
            model_parameters={"temperature": 0.3, "max_tokens": 4096},
            user_id=user_id
        )
        
        # 恢复历史消息到Agent
        if requirement_session.history_messages:
            # 这里需要将JSON字符串形式的history_messages反序列化
            # 然后将对象类型转换为UserPromptMessage或AssistantPromptMessage
            saved_messages = requirement_session.history_messages_list
            history_messages = []
            
            for msg in saved_messages:
                if msg.get('type') == 'user':
                    history_messages.append(UserPromptMessage(content=msg.get('content', '')))
                elif msg.get('type') == 'assistant':
                    history_messages.append(AssistantPromptMessage(content=msg.get('content', '')))
            
            # 将历史消息设置到Agent中
            agent.history_messages = history_messages
        
        # Get the stream from the agent
        response_stream = agent.run(input_data)
        
        # Process stream and update session
        for chunk in response_stream:
            # 将Agent的历史消息转换为可JSON序列化的格式
            serialized_messages = []
            for msg in agent.history_messages:
                msg_type = 'user' if isinstance(msg, UserPromptMessage) else 'assistant'
                serialized_messages.append({
                    'type': msg_type,
                    'content': msg.content
                })
            
            # Update the session with the latest data and history messages
            self.update_session(
                requirement_session.id, 
                chunk, 
                serialized_messages
            )
            
            # Yield the chunk with session_id added
            result = {
                "session_id": requirement_session.id,
                "status": requirement_session.status,
                "data": chunk
            }
            yield result
            
    def get_session_by_id(self, session_id: str) -> Optional[GameRequirementSession]:
        """
        Get session by ID
        """
        return db.session.query(GameRequirementSession).filter(
            GameRequirementSession.id == session_id
        ).first()
        
    def get_sessions_by_app(self, app_id: str, user_id: Optional[str] = None) -> list[GameRequirementSession]:
        """
        Get all sessions for an app
        """
        query = db.session.query(GameRequirementSession).filter(
            GameRequirementSession.app_id == app_id
        )
        
        if user_id:
            query = query.filter(GameRequirementSession.user_id == user_id)
            
        return query.order_by(GameRequirementSession.updated_at.desc()).all()
        
    def advance_session_status(self, session_id: str, new_status: str) -> GameRequirementSession:
        """
        Advance the session to a new status
        """
        session = self.get_session_by_id(session_id)
        
        if not session:
            raise ValueError(f"Session with id {session_id} not found")
            
        session.status = new_status
        session.updated_at = datetime.utcnow()
        db.session.commit()
        
        return session
