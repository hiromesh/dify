import logging
from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import Any, Optional

from core.model_manager import ModelInstance
from core.model_runtime.entities.message_entities import PromptMessage, SystemPromptMessage, UserPromptMessage
from core.rag.datasource.retrieval_service import RetrievalService
from core.rag.retrieval.retrieval_methods import RetrievalMethod
from extensions.ext_database import db
from models.dataset import Dataset
from models.model import Conversation, Message

logger = logging.getLogger(__name__)


class BaseWorkflowAgent(ABC):
    def __init__(
        self,
        *,
        tenant_id: str,
        conversation: Conversation,
        message: Message,
        user_id: str,
        model_instance: ModelInstance,
        prompt_messages: list[PromptMessage] = [],
    ) -> None:
        self.tenant_id = tenant_id
        self.conversation = conversation
        self.message = message
        self.user_id = user_id
        self.model_instance = model_instance
        self.prompt_messages = prompt_messages
        self.history_messages: list[PromptMessage] = []

    @property
    @abstractmethod
    def default_schema(self) -> dict[str, Any]:
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        pass

    @property
    @abstractmethod
    def prompt_template(self) -> str:
        pass

    @abstractmethod
    def run(self, input_data: str) -> Generator[str, None, None]:
        raise NotImplementedError

    def _relevant_info(self, query: str) -> Optional[list[str]]:
        try:
            datasets = db.session.query(Dataset).filter(
                Dataset.available_document_count > 0).all()
            if not datasets:
                return None
            dataset = datasets[0]
            retrieval_method = RetrievalMethod.SEMANTIC_SEARCH.value
            top_k = 5
            score_threshold = 0.5

            documents = RetrievalService.retrieve(
                retrieval_method=retrieval_method,
                dataset_id=dataset.id,
                query=query,
                top_k=top_k,
                score_threshold=score_threshold
            )

            if not documents:
                return None

            results = []
            for doc in documents:
                content = doc.page_content
                if doc.metadata:
                    source = doc.metadata.get('source', '')
                    title = doc.metadata.get('title', '')
                    if title or source:
                        content = f"Source: {source or 'Unknown'}, Title: {title or 'Untitled'}\n{content}"
                results.append(content)
            return results
        except Exception as e:
            logger.exception("Error in _relevant_info")
            return None

    def _construct_messages(self, prompt: str) -> list[PromptMessage]:
        system_content = self.system_prompt
        rag_results = self._relevant_info(prompt)
        if rag_results and len(rag_results) > 0:
            rag_context = "### Relevant Information:\n" + \
                "\n".join(rag_results)
            system_content = f"{system_content}\n\n{rag_context}"

        messages = [SystemPromptMessage(content=system_content)]
        messages.extend(self.history_messages)
        messages.append(UserPromptMessage(content=prompt))
        return messages
