"""
Demo script to test LoggingContextMiddleware in action.

This script starts a temporary FastAPI server and makes test requests
to verify structured logging with request context.
"""
import asyncio
import httpx
import json
import time
from fastapi import FastAPI, Request
from app.middleware.logging_middleware import LoggingContextMiddleware
from app.core.logging import setup_logging, get_logger

# Setup structured logging in development mode (colored output)
setup_logging()
logger = get_logger(__name__)

# Create test app
app = FastAPI(title="Logging Middleware Demo")
app.add_middleware(LoggingContextMiddleware)


@app.get("/test")
async def test_endpoint():
    """Test endpoint that generates logs."""
    logger.info("Processing test request")
    logger.debug(
        "Debug information from endpoint",
        extra={"extra_fields": {"custom_field": "custom_value"}},
    )
    return {"message": "success", "timestamp": time.time()}


@app.get("/error")
async def error_endpoint():
    """Test endpoint that generates an error."""
    logger.warning("About to raise an error")
    raise ValueError("Test error for logging")


async def make_test_requests():
    """Make test requests to the demo server."""
    base_url = "http://127.0.0.1:8000"

    async with httpx.AsyncClient() as client:
        print("\n" + "=" * 60)
        print("MAKING TEST REQUESTS")
        print("=" * 60 + "\n")

        # Test 1: Normal request
        print("TEST 1: Normal request without custom headers")
        response = await client.get(f"{base_url}/test")
        print(f"Response status: {response.status_code}")
        print(f"X-Request-ID header: {response.headers.get('X-Request-ID')}")
        print(f"Response body: {response.json()}\n")

        await asyncio.sleep(0.5)

        # Test 2: Request with correlation ID
        print("TEST 2: Request with X-Correlation-ID header")
        correlation_id = "test-correlation-123"
        response = await client.get(
            f"{base_url}/test", headers={"X-Correlation-ID": correlation_id}
        )
        print(f"Response status: {response.status_code}")
        print(f"X-Request-ID header: {response.headers.get('X-Request-ID')}")
        print(f"Correlation ID sent: {correlation_id}\n")

        await asyncio.sleep(0.5)

        # Test 3: Error handling
        print("TEST 3: Request that triggers an error")
        try:
            response = await client.get(f"{base_url}/error")
        except Exception:
            pass
        print("Error logged (check logs above)\n")

        print("=" * 60)
        print("DEMO COMPLETE")
        print("=" * 60)
        print("\nCheck the logs above to see:")
        print("1. Request IDs automatically generated")
        print("2. Correlation IDs propagated from headers")
        print("3. Structured JSON logs in development format")
        print("4. Request start and completion logging")
        print("5. Error logging with full context")


if __name__ == "__main__":
    import uvicorn
    import threading

    print("\n" + "=" * 60)
    print("LOGGING MIDDLEWARE DEMONSTRATION")
    print("Sprint 3 Phase 1: Structured Logging Foundation")
    print("=" * 60)
    print("\nStarting demo server on http://127.0.0.1:8000")
    print("Watch the structured logs below:\n")

    # Run server in background thread
    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for server to start
    time.sleep(2)

    # Make test requests
    asyncio.run(make_test_requests())

    # Give time to see final logs
    time.sleep(1)
