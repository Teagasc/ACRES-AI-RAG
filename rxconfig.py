import reflex as rx

config = rx.Config(
    app_name="chat",
    api_url="http://localhost:8000",  # This is the URL the frontend will use for WebSocket connections.
)
