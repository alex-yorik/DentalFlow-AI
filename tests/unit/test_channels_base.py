from src.channels.base import IncomingMessage, OutgoingAdapter


class TestIncomingMessage:
    def test_default_channel_type_is_telegram(self):
        msg = IncomingMessage(channel_user_id="user-1", text="hello")
        assert msg.channel_type == "telegram"

    def test_custom_channel_type(self):
        msg = IncomingMessage(channel_user_id="+79161112233", text="hi", channel_type="whatsapp")
        assert msg.channel_type == "whatsapp"

    def test_fields_are_preserved(self):
        msg = IncomingMessage(channel_user_id="u42", text="hi")
        assert msg.channel_user_id == "u42"
        assert msg.text == "hi"


class TestOutgoingAdapterProtocol:
    def test_implements_send_message(self):
        class Adapter:
            async def send_message(self, channel_user_id: str, text: str) -> None:
                pass

        assert isinstance(Adapter(), OutgoingAdapter)

    def test_missing_send_message_not_compatible(self):
        class Adapter:
            pass

        assert not isinstance(Adapter(), OutgoingAdapter)
