import logging

from src.integrations.crm.provider import CRMProvider
from src.leads.models import Lead

logger = logging.getLogger(__name__)


class MockCRMProvider(CRMProvider):
    def __init__(self):
        self._contacts: dict[str, dict] = {}
        self._leads: dict[str, dict] = {}

    async def create_contact(self, lead: Lead) -> str:
        contact_id = f"mock_contact_{lead.channel_user_id}"
        self._contacts[contact_id] = {
            "name": lead.name,
            "phone": lead.phone,
            "email": lead.email,
        }
        logger.info("Mock CRM: created contact %s for chat %s", contact_id, lead.channel_user_id)
        return contact_id

    async def update_contact(self, contact_id: str, lead: Lead) -> None:
        if contact_id in self._contacts:
            self._contacts[contact_id].update({
                "name": lead.name,
                "phone": lead.phone,
                "email": lead.email,
            })
        logger.info("Mock CRM: updated contact %s", contact_id)

    async def create_lead(self, contact_id: str, lead: Lead) -> str:
        lead_id = f"mock_lead_{lead.channel_user_id}_{lead.id[:8]}"
        self._leads[lead_id] = {
            "contact_id": contact_id,
            "service_interest": lead.service_interest,
            "urgency": lead.urgency,
        }
        logger.info("Mock CRM: created lead %s for contact %s", lead_id, contact_id)
        return lead_id

    async def add_note(self, lead_id: str, note: str) -> None:
        logger.info("Mock CRM: added note to %s: %s", lead_id, note)

    async def update_stage(self, lead_id: str, stage: str) -> None:
        logger.info("Mock CRM: updated stage for %s to %s", lead_id, stage)
