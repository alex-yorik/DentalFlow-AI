from datetime import datetime, timezone


from src.leads.models import Lead
from src.storage.appointment_repository import (
    find_existing_appointment,
    create_appointment,
    update_appointment_datetime,
)


def _lead(chat_id=42, name="John", phone="555-0100", service="Cleaning") -> Lead:
    now = datetime.now(timezone.utc)
    return Lead(
        id="lead-1",
        channel_user_id=chat_id,
        name=name,
        phone=phone,
        service_interest=service,
        preferred_time="2026-08-10 10:00",
        created_at=now,
        updated_at=now,
    )


class TestAppointmentRepository:
    async def test_find_by_phone(self, db):
        await create_appointment(_lead())
        found = await find_existing_appointment(name=None, phone="555-0100")
        assert found is not None
        assert found["name"] == "John"
        assert found["service"] == "Cleaning"

    async def test_no_phone_returns_none_by_default(self, db):
        await create_appointment(_lead())
        found = await find_existing_appointment(name="John", phone=None)
        assert found is None

    async def test_no_phone_cannot_leak_same_name_record(self, db):
        await create_appointment(_lead(name="John", phone="555-0100", service="Cleaning"))
        await create_appointment(_lead(name="John", phone="555-0200", service="Whitening"))
        found = await find_existing_appointment(name="John", phone=None)
        assert found is None

    async def test_name_collision_does_not_leak_other_patient(self, db):
        await create_appointment(_lead(name="John", phone="555-0100", service="Cleaning"))
        await create_appointment(_lead(name="John", phone="555-0200", service="Whitening"))
        other = await find_existing_appointment(name="John", phone="555-0200")
        assert other["phone"] == "555-0200"
        assert other["service"] == "Whitening"
        assert await find_existing_appointment(name="John", phone="555-0199") is None

    async def test_find_none_when_no_match(self, db):
        found = await find_existing_appointment(name="Nobody", phone="555-9999")
        assert found is None

    async def test_update_appointment_datetime(self, db):
        appt_id = await create_appointment(_lead())
        await update_appointment_datetime(appt_id, "2026-08-11 14:30")
        found = await find_existing_appointment(name="John", phone="555-0100")
        assert found["appointment_datetime"] == "2026-08-11 14:30"

    async def test_create_uses_preferred_time(self, db):
        await create_appointment(_lead())
        found = await find_existing_appointment(name="John", phone="555-0100")
        assert found["appointment_datetime"] == "2026-08-10 10:00"
