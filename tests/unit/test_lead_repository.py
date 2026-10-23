from src.leads.models import LeadState
from src.leads.repository import (
    create_lead,
    get_lead_by_chat_id,
    update_lead,
    lead_exists,
    delete_lead,
)


class TestLeadRepository:
    async def test_create_lead(self, db):
        lead = await create_lead(channel_user_id=12345)
        assert lead.channel_user_id == 12345
        assert lead.state == LeadState.NEW
        assert lead.source == "telegram"
        assert lead.id is not None

    async def test_get_lead_by_chat_id_returns_none_for_missing(self, db):
        result = await get_lead_by_chat_id(99999)
        assert result is None

    async def test_create_and_retrieve_lead(self, db):
        created = await create_lead(channel_user_id=111)
        retrieved = await get_lead_by_chat_id(111)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.channel_user_id == 111

    async def test_update_lead(self, db):
        lead = await create_lead(channel_user_id=222)
        lead.name = "John Doe"
        lead.phone = "+1-555-0100"
        lead.service_interest = "Teeth Cleaning"
        lead.state = LeadState.COLLECT_FIELDS
        await update_lead(lead)

        retrieved = await get_lead_by_chat_id(222)
        assert retrieved is not None
        assert retrieved.name == "John Doe"
        assert retrieved.phone == "+1-555-0100"
        assert retrieved.service_interest == "Teeth Cleaning"
        assert retrieved.state == LeadState.COLLECT_FIELDS

    async def test_lead_exists(self, db):
        assert await lead_exists(333) is False
        await create_lead(channel_user_id=333)
        assert await lead_exists(333) is True

    async def test_delete_lead(self, db):
        lead = await create_lead(channel_user_id=444)
        assert await lead_exists(444) is True
        await delete_lead(lead.id)
        assert await get_lead_by_chat_id(444) is None

    async def test_multiple_leads_same_chat_returns_latest(self, db):
        first = await create_lead(channel_user_id=555)
        second = await create_lead(channel_user_id=555)
        retrieved = await get_lead_by_chat_id(555)
        assert retrieved is not None
        assert retrieved.id == second.id
        assert retrieved.id != first.id