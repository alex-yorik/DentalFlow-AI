# WhatsApp Integration Architecture

## Overview
WhatsApp integration uses Meta's Business API via webhooks.
Incoming messages arrive as POST requests; outgoing messages are sent via WhatsApp Cloud API.

## Webhook Flow

```
Meta Cloud API                  DentalFlow AI
      │                              │
      │  GET /whatsapp/webhook       │
      │  ?hub.mode=subscribe         │
      │  &hub.verify_token=***       │
      │  &hub.challenge=CHALLENGE    │
      │ ─────────────────────────►   │  Verify token matches
      │  ◄───────────────────────── │  Return hub.challenge
      │                              │
      │  POST /whatsapp/webhook      │
      │  { entry: [{ changes: [{     │
      │    value: { messages: [{      │
      │      from: "PHONE_NUMBER",   │
      │      text: { body: "Hello" } │
      │    }]}]}]}                   │
      │ ─────────────────────────►   │  Parse phone + text
      │                              │  Map phone → int (hash)
      │                              │  Lookup / create lead
      │                              │  IncomingMessage(channel_type="whatsapp")
      │                              │  process_message()
      │                              │
      │                              │  WhatsAppOutgoingAdapter.send_message()
      │                              │  └─ stub: log to logger
      │                              │  └─ production: POST to Meta API
```

## Key Files

| File | Purpose |
|------|---------|
| `src/channels/whatsapp/__init__.py` | Package marker |
| `src/channels/whatsapp/adapter.py` | WhatsAppOutgoingAdapter + webhook endpoints |

## WhatsAppOutgoingAdapter

Implements `OutgoingAdapter` protocol from `src/channels/base.py`.

- **Stub mode (current):** Logs outgoing message text via `logger.info(...)`. Response
  stored in in-memory `_response_store` for debugging.
- **Production mode:** Replace stub with:
  ```python
  async def send_message(self, channel_user_id: str, text: str) -> None:
      await http_client.post(
          f"https://graph.facebook.com/v18.0/{phone_number_id}/messages",
          json={
              "messaging_product": "whatsapp",
              "to": channel_user_id,
              "type": "text",
              "text": {"body": text},
          },
          headers={"Authorization": f"Bearer {access_token}"},
      )
  ```

## To activate in main.py

1. Import `router` from `src.channels.whatsapp.adapter`
2. Include in the FastAPI app: `app.include_router(router)`
3. Add WhatsApp config (verify_token, phone_number_id, access_token) to `AppConfig`
4. Replace `WhatsAppOutgoingAdapter.send_message()` stub with real HTTP call

## Dependencies (production)
- `httpx` or `aiohttp` for async HTTP calls
- Meta Business Account with WhatsApp Cloud API credentials

## Security Notes
- Webhook verification prevents spoofed requests (verify_token check)
- All phone numbers are hashed to integers for database storage
- No real credentials should be committed to the repository