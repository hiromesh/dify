import json
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, String, Text

from extensions.ext_database import db
from models.base import Base


class GameRequirementSession(Base):
    """
    Game Requirement Session

    Attributes:
        id (str): Primary key
        tenant_id (str): Workspace ID
        app_id (str): App ID
        user_id (str): User ID
        status (str): Status of the session (e.g., 'requirements', 'design', 'features', 'workflow')
        requirement_data (str): JSON string containing the requirement data
        history_messages (str): JSON string containing the history messages for prompt context
        created_at (datetime): Creation time
        updated_at (datetime): Last update time
    """
    __tablename__ = 'game_requirement_sessions'
    __table_args__ = (
        db.PrimaryKeyConstraint('id', name='game_requirement_session_pkey'),
        {},
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), nullable=False)
    app_id = Column(String(36), nullable=False)
    user_id = Column(String(36), nullable=False)
    status = Column(String(36), nullable=False, default='requirements')
    requirement_data = Column(Text, nullable=True)
    history_messages = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def requirement_data_dict(self):
        """Parse the requirement_data JSON string to a dict"""
        if not self.requirement_data:
            return {}
        return json.loads(self.requirement_data)
        
    @property
    def history_messages_list(self):
        """Parse the history_messages JSON string to a list"""
        if not self.history_messages:
            return []
        return json.loads(self.history_messages)

    @classmethod
    def create(cls, tenant_id, app_id, user_id):
        """Create a new session"""
        session = cls()
        session.id = str(uuid4())
        session.tenant_id = tenant_id
        session.app_id = app_id
        session.user_id = user_id
        session.status = 'requirements'
        session.requirement_data = '{}'
        session.history_messages = '[]'  # 初始化为空列表
        session.created_at = datetime.utcnow()
        session.updated_at = session.created_at
        return session
