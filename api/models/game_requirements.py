import json
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, String, Text

from extensions.ext_database import db
from models.base import Base


class GameRequirementSession(Base):

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
    updated_at = Column(DateTime, nullable=False,
                        default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def requirement_data_dict(self):
        if not self.requirement_data:
            return {}
        return json.loads(self.requirement_data)

    @property
    def history_messages_list(self):
        if not self.history_messages:
            return []
        return json.loads(self.history_messages)

    @classmethod
    def create(cls, tenant_id, app_id, user_id):
        session = cls()
        session.id = str(uuid4())
        session.tenant_id = tenant_id
        session.app_id = app_id
        session.user_id = user_id
        session.status = 'requirements'
        session.requirement_data = '{}'
        session.history_messages = '[]'
        session.created_at = datetime.utcnow()
        session.updated_at = session.created_at
        return session
