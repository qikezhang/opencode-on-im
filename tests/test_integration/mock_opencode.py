"""Mock OpenCode HTTP server for integration testing."""

import asyncio
import json
from typing import Any
from dataclasses import dataclass, field
from aiohttp import web


@dataclass
class MockSession:
    """Represents a mock OpenCode session."""

    id: str
    title: str = "Test Session"
    messages: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class MockOpenCodeServer:
    """Mock OpenCode HTTP API server for testing.

    Simulates the OpenCode REST API endpoints:
    - GET /global/health
    - GET /session
    - POST /session
    - POST /session/{id}/message
    - POST /session/{id}/prompt_async
    - POST /session/{id}/abort
    - GET /event (SSE)
    """

    host: str = "127.0.0.1"
    port: int = 0  # 0 = auto-assign
    sessions: dict[str, MockSession] = field(default_factory=dict)
    _app: web.Application | None = None
    _runner: web.AppRunner | None = None
    _site: web.TCPSite | None = None
    _event_queues: list[asyncio.Queue[dict[str, Any]]] = field(default_factory=list)
    # Track requests for assertions
    received_requests: list[dict[str, Any]] = field(default_factory=list)
    # Configurable response behavior
    response_text: str = "This is a mock AI response."
    response_delay: float = 0.1  # Simulate processing time

    async def start(self) -> int:
        """Start the mock server. Returns the assigned port."""
        self._app = web.Application()
        self._setup_routes()
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, self.host, self.port)
        await self._site.start()

        # Get actual port if auto-assigned
        assert self._site._server is not None
        actual_port: int = self._site._server.sockets[0].getsockname()[1]
        self.port = actual_port
        return actual_port

    async def stop(self) -> None:
        """Stop the mock server."""
        if self._runner:
            await self._runner.cleanup()

    def _setup_routes(self) -> None:
        """Configure API routes."""
        assert self._app is not None
        self._app.router.add_get("/global/health", self._handle_health)
        self._app.router.add_get("/session", self._handle_list_sessions)
        self._app.router.add_post("/session", self._handle_create_session)
        self._app.router.add_get("/session/{session_id}", self._handle_get_session)
        self._app.router.add_post(
            "/session/{session_id}/message", self._handle_send_message
        )
        self._app.router.add_post(
            "/session/{session_id}/prompt_async", self._handle_send_async
        )
        self._app.router.add_post(
            "/session/{session_id}/abort", self._handle_abort
        )
        self._app.router.add_get("/event", self._handle_sse)
        self._app.router.add_get("/global/event", self._handle_sse)

    async def _handle_health(self, request: web.Request) -> web.Response:
        """GET /global/health - Health check."""
        self.received_requests.append({"method": "GET", "path": "/global/health"})
        return web.json_response({
            "status": "ok",
            "version": "0.1.0-mock",
        })

    async def _handle_list_sessions(self, request: web.Request) -> web.Response:
        """GET /session - List all sessions."""
        self.received_requests.append({"method": "GET", "path": "/session"})
        sessions_data = [
            {"id": s.id, "title": s.title, "messageCount": len(s.messages)}
            for s in self.sessions.values()
        ]
        return web.json_response(sessions_data)

    async def _handle_create_session(self, request: web.Request) -> web.Response:
        """POST /session - Create new session."""
        data = await request.json() if request.body_exists else {}
        self.received_requests.append({
            "method": "POST",
            "path": "/session",
            "data": data,
        })

        session_id = f"ses_{len(self.sessions) + 1:04d}"
        title = data.get("title", f"Session {len(self.sessions) + 1}")
        session = MockSession(id=session_id, title=title)
        self.sessions[session_id] = session

        return web.json_response({
            "id": session_id,
            "title": title,
        })

    async def _handle_get_session(self, request: web.Request) -> web.Response:
        """GET /session/{id} - Get session details."""
        session_id = request.match_info["session_id"]
        self.received_requests.append({
            "method": "GET",
            "path": f"/session/{session_id}",
        })

        session = self.sessions.get(session_id)
        if not session:
            raise web.HTTPNotFound(text="Session not found")

        return web.json_response({
            "id": session.id,
            "title": session.title,
            "messages": session.messages,
        })

    async def _handle_send_message(self, request: web.Request) -> web.Response:
        """POST /session/{id}/message - Send message (blocking)."""
        session_id = request.match_info["session_id"]
        data = await request.json()
        self.received_requests.append({
            "method": "POST",
            "path": f"/session/{session_id}/message",
            "data": data,
        })

        session = self.sessions.get(session_id)
        if not session:
            raise web.HTTPNotFound(text="Session not found")

        # Simulate processing delay
        await asyncio.sleep(self.response_delay)

        # Store user message
        user_msg_id = f"msg_{len(session.messages) + 1:04d}"
        user_msg = {
            "id": user_msg_id,
            "role": "user",
            "parts": data.get("parts", []),
        }
        session.messages.append(user_msg)

        # Generate AI response
        ai_msg_id = f"msg_{len(session.messages) + 1:04d}"
        ai_msg = {
            "id": ai_msg_id,
            "role": "assistant",
            "parts": [{"type": "text", "text": self.response_text}],
        }
        session.messages.append(ai_msg)

        # Emit event to SSE subscribers
        await self._emit_event({
            "type": "message.complete",
            "sessionId": session_id,
            "messageId": ai_msg_id,
            "content": self.response_text,
        })

        return web.json_response(ai_msg)

    async def _handle_send_async(self, request: web.Request) -> web.Response:
        """POST /session/{id}/prompt_async - Send message (non-blocking)."""
        session_id = request.match_info["session_id"]
        data = await request.json()
        self.received_requests.append({
            "method": "POST",
            "path": f"/session/{session_id}/prompt_async",
            "data": data,
        })

        session = self.sessions.get(session_id)
        if not session:
            raise web.HTTPNotFound(text="Session not found")

        # Store user message immediately
        user_msg_id = f"msg_{len(session.messages) + 1:04d}"
        user_msg = {
            "id": user_msg_id,
            "role": "user",
            "parts": data.get("parts", []),
        }
        session.messages.append(user_msg)

        # Schedule async response generation
        asyncio.create_task(
            self._generate_async_response(session_id, user_msg_id)
        )

        return web.json_response({"status": "accepted", "messageId": user_msg_id})

    async def _generate_async_response(
        self, session_id: str, user_msg_id: str
    ) -> None:
        """Generate response asynchronously and emit SSE events."""
        await asyncio.sleep(self.response_delay)

        session = self.sessions.get(session_id)
        if not session:
            return

        ai_msg_id = f"msg_{len(session.messages) + 1:04d}"
        ai_msg = {
            "id": ai_msg_id,
            "role": "assistant",
            "parts": [{"type": "text", "text": self.response_text}],
        }
        session.messages.append(ai_msg)

        # Emit streaming events
        await self._emit_event({
            "type": "message.start",
            "sessionId": session_id,
            "messageId": ai_msg_id,
        })

        # Simulate streaming text
        words = self.response_text.split()
        for i, word in enumerate(words):
            await self._emit_event({
                "type": "message.delta",
                "sessionId": session_id,
                "messageId": ai_msg_id,
                "delta": word + (" " if i < len(words) - 1 else ""),
            })
            await asyncio.sleep(0.01)

        await self._emit_event({
            "type": "message.complete",
            "sessionId": session_id,
            "messageId": ai_msg_id,
            "content": self.response_text,
        })

    async def _handle_abort(self, request: web.Request) -> web.Response:
        """POST /session/{id}/abort - Cancel current task."""
        session_id = request.match_info["session_id"]
        self.received_requests.append({
            "method": "POST",
            "path": f"/session/{session_id}/abort",
        })
        return web.json_response({"status": "aborted"})

    async def _handle_sse(self, request: web.Request) -> web.StreamResponse:
        """GET /event or /global/event - SSE event stream."""
        self.received_requests.append({"method": "GET", "path": "/event"})

        response = web.StreamResponse(
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        await response.prepare(request)

        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._event_queues.append(queue)

        try:
            while True:
                event = await queue.get()
                event_data = f"data: {json.dumps(event)}\n\n"
                await response.write(event_data.encode())
        except asyncio.CancelledError:
            pass
        finally:
            self._event_queues.remove(queue)

        return response

    async def _emit_event(self, event: dict[str, Any]) -> None:
        """Emit an event to all SSE subscribers."""
        for queue in self._event_queues:
            await queue.put(event)

    # Test helpers

    def reset(self) -> None:
        """Reset server state for clean tests."""
        self.sessions.clear()
        self.received_requests.clear()

    def set_response(self, text: str) -> None:
        """Configure the mock AI response."""
        self.response_text = text

    def get_requests_for_path(self, path_pattern: str) -> list[dict[str, Any]]:
        """Get all requests matching a path pattern."""
        return [r for r in self.received_requests if path_pattern in r["path"]]
