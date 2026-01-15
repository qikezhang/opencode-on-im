"""Tests for base adapter."""


from opencode_on_im.adapters.base import IncomingMessage


class TestIncomingMessage:
    def test_basic_message(self):
        msg = IncomingMessage(
            platform="telegram",
            user_id="123",
            chat_id="456",
            text="Hello",
        )
        assert msg.platform == "telegram"
        assert msg.user_id == "123"
        assert msg.chat_id == "456"
        assert msg.text == "Hello"
        assert msg.voice_data is None
        assert msg.reply_to_message_id is None

    def test_message_with_voice(self):
        msg = IncomingMessage(
            platform="dingtalk",
            user_id="user1",
            chat_id="chat1",
            text="",
            voice_data=b"audio_bytes",
        )
        assert msg.voice_data == b"audio_bytes"

    def test_message_with_reply(self):
        msg = IncomingMessage(
            platform="telegram",
            user_id="user1",
            chat_id="chat1",
            text="reply text",
            reply_to_message_id="msg123",
        )
        assert msg.reply_to_message_id == "msg123"
