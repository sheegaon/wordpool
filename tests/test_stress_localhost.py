"""
Stress and load tests for Quipflip API on localhost.

These tests simulate high-load scenarios and edge cases.
IMPORTANT: Backend must be running on http://localhost:8000

Run with: pytest tests/test_stress_localhost.py -v
"""
import httpx
import pytest
import concurrent.futures
import time
from typing import List, Dict

BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0


class TestClient:
    """Helper class for making API requests."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.client = httpx.Client(base_url=BASE_URL, timeout=TIMEOUT)

    def headers(self) -> Dict[str, str]:
        if self.api_key:
            return {"X-API-Key": self.api_key}
        return {}

    def get(self, path: str, **kwargs):
        return self.client.get(path, headers=self.headers(), **kwargs)

    def post(self, path: str, **kwargs):
        return self.client.post(path, headers=self.headers(), **kwargs)

    def close(self):
        self.client.close()


@pytest.fixture(scope="session")
def verify_server_running():
    """Verify backend is running."""
    try:
        response = httpx.get(f"{BASE_URL}/health", timeout=5.0)
        if response.status_code != 200:
            pytest.fail(f"Server unhealthy: {response.status_code}")
    except httpx.ConnectError:
        pytest.fail(
            "Cannot connect to http://localhost:8000\n"
            "Start server: uvicorn backend.main:app --reload"
        )


class TestHighVolumePlayerCreation:
    """Test creating many players rapidly."""

    def test_create_100_players(self, verify_server_running):
        """Create 100 players in quick succession."""
        client = TestClient()
        players = []

        start_time = time.time()

        for i in range(100):
            response = client.post("/player")
            assert response.status_code == 201
            players.append(response.json())

        end_time = time.time()
        duration = end_time - start_time

        print(f"\nCreated 100 players in {duration:.2f} seconds")
        print(f"Average: {duration/100:.3f} seconds per player")

        # Verify all players have unique IDs and API keys
        player_ids = [p["player_id"] for p in players]
        api_keys = [p["api_key"] for p in players]

        assert len(set(player_ids)) == 100, "Duplicate player IDs found"
        assert len(set(api_keys)) == 100, "Duplicate API keys found"

        client.close()


class TestConcurrentRounds:
    """Test concurrent round operations."""

    def test_concurrent_prompt_rounds(self, verify_server_running):
        """Test multiple players starting prompt rounds simultaneously."""
        num_players = 20

        # Create players
        players = []
        for _ in range(num_players):
            client = TestClient()
            player = client.post("/player").json()
            players.append(player)
            client.close()

        # Start prompt rounds concurrently
        def start_prompt(api_key):
            client = TestClient(api_key)
            try:
                response = client.post("/rounds/prompt", json={})
                return response.status_code, response.json()
            finally:
                client.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(start_prompt, player["api_key"])
                for player in players
            ]
            results = [future.result() for future in futures]

        # All should succeed
        success_count = sum(1 for status, _ in results if status == 200)
        print(f"\n{success_count}/{num_players} prompt rounds started successfully")

        assert success_count == num_players

    def test_concurrent_balance_checks(self, verify_server_running):
        """Test concurrent balance check requests."""
        # Create player
        client = TestClient()
        player = client.post("/player").json()
        api_key = player["api_key"]
        client.close()

        # Make 50 concurrent balance requests
        def check_balance():
            client = TestClient(api_key)
            try:
                response = client.get("/player/balance")
                return response.status_code, response.json()
            finally:
                client.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_balance) for _ in range(50)]
            results = [future.result() for future in futures]

        # All should succeed with same balance
        assert all(status == 200 for status, _ in results)
        balances = [data["balance"] for _, data in results]
        assert all(b == balances[0] for b in balances), "Balance inconsistency detected"


class TestRateLimiting:
    """Test rate limiting behavior."""

    def test_rapid_requests(self, verify_server_running):
        """Test making many requests rapidly."""
        client = TestClient()
        player = client.post("/player").json()
        auth_client = TestClient(player["api_key"])

        # Make 150 rapid requests (rate limit is 100/min)
        responses = []
        start_time = time.time()

        for i in range(150):
            response = auth_client.get("/player/balance")
            responses.append(response.status_code)

        end_time = time.time()
        duration = end_time - start_time

        # Count rate limited responses (429)
        rate_limited = sum(1 for status in responses if status == 429)
        successful = sum(1 for status in responses if status == 200)

        print(f"\nMade 150 requests in {duration:.2f} seconds")
        print(f"Successful: {successful}, Rate limited: {rate_limited}")

        # Note: Rate limiting may or may not be enabled
        # This test documents behavior rather than asserting specific limits

        client.close()
        auth_client.close()


class TestQueueStress:
    """Test queue system under load."""

    def test_queue_many_prompts(self, verify_server_running):
        """Test adding many prompts to queue."""
        players = []
        word_list = [
            "beautiful", "wonderful", "amazing", "fantastic", "incredible",
            "peaceful", "joyful", "happy", "excited", "grateful",
            "creative", "brilliant", "clever", "smart", "wise",
            "strong", "brave", "bold", "fierce", "mighty"
        ]

        # Create 20 players and submit prompts
        for i in range(20):
            client = TestClient()
            player = client.post("/player").json()
            players.append(player)

            auth_client = TestClient(player["api_key"])
            prompt_round = auth_client.post("/rounds/prompt", json={})

            if prompt_round.status_code == 200:
                round_id = prompt_round.json()["round_id"]
                word = word_list[i % len(word_list)]
                auth_client.post(
                    f"/rounds/{round_id}/submit",
                    json={"phrase": word}
                )

            client.close()
            auth_client.close()

        # Check queue status
        check_client = TestClient()
        player = check_client.post("/player").json()
        auth_check = TestClient(player["api_key"])

        availability = auth_check.get("/rounds/available").json()
        prompts_waiting = availability["prompts_waiting"]

        print(f"\n{prompts_waiting} prompts in queue after stress test")

        assert prompts_waiting > 0, "No prompts in queue"

        check_client.close()
        auth_check.close()


class TestDatabaseConsistency:
    """Test database consistency under concurrent operations."""

    def test_concurrent_transactions(self, verify_server_running):
        """Test balance consistency with concurrent operations."""
        # Create player
        client = TestClient()
        player = client.post("/player").json()
        api_key = player["api_key"]
        client.close()

        initial_balance = 1000

        # Start 5 prompt rounds concurrently (should cost 500 total)
        # But only one should succeed due to "one round at a time" rule
        def start_prompt():
            client = TestClient(api_key)
            try:
                response = client.post("/rounds/prompt", json={})
                return response.status_code
            finally:
                client.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(start_prompt) for _ in range(5)]
            results = [future.result() for future in futures]

        # Count successes
        successes = sum(1 for status in results if status == 200)
        failures = sum(1 for status in results if status == 400)

        print(f"\nConcurrent round attempts: {successes} succeeded, {failures} failed")

        # Only one should succeed
        assert successes == 1, "Multiple concurrent rounds should not succeed"

        # Check final balance
        check_client = TestClient(api_key)
        final_balance = check_client.get("/player/balance").json()["balance"]

        expected_balance = initial_balance - 100  # One round at $100
        assert final_balance == expected_balance, \
            f"Balance mismatch: expected {expected_balance}, got {final_balance}"

        check_client.close()


class TestLongRunningOperations:
    """Test system behavior with long-running scenarios."""

    def test_sequential_rounds(self, verify_server_running):
        """Test player completing many rounds sequentially."""
        client = TestClient()
        player = client.post("/player").json()
        auth_client = TestClient(player["api_key"])

        words = [
            "happy", "joyful", "peaceful", "calm", "serene",
            "bright", "shining", "glowing", "radiant", "brilliant"
        ]

        successful_rounds = 0

        # Try to complete 10 sequential prompt rounds
        for i in range(min(10, len(words))):
            # Check if we have enough balance
            balance = auth_client.get("/player/balance").json()["balance"]
            if balance < 100:
                print(f"\nInsufficient balance after {i} rounds")
                break

            # Start round
            round_response = auth_client.post("/rounds/prompt", json={})
            if round_response.status_code != 200:
                print(f"\nCould not start round {i+1}: {round_response.status_code}")
                break

            round_id = round_response.json()["round_id"]

            # Submit phrase
            submit_response = auth_client.post(
                f"/rounds/{round_id}/submit",
                json={"phrase": words[i]}
            )

            if submit_response.status_code == 200:
                successful_rounds += 1
            else:
                print(f"\nSubmission failed: {submit_response.status_code}")
                break

            # Small delay between rounds
            time.sleep(0.1)

        print(f"\nCompleted {successful_rounds} sequential rounds")

        assert successful_rounds >= 9, "Should complete at least 9 rounds with $1000"

        client.close()
        auth_client.close()


class TestErrorRecovery:
    """Test system recovery from error conditions."""

    def test_recovery_from_invalid_submissions(self, verify_server_running):
        """Test system handles invalid submissions gracefully."""
        client = TestClient()
        player = client.post("/player").json()
        auth_client = TestClient(player["api_key"])

        # Start prompt round
        round_response = auth_client.post("/rounds/prompt", json={})
        round_id = round_response.json()["round_id"]

        # Try multiple invalid submissions
        invalid_phrases = [
            "x",  # too short
            "verylongwordthatistoobig" * 10,  # too long (>100 chars)
            "test123",  # numbers
            "test-word",  # hyphen
        ]

        for phrase in invalid_phrases:
            response = auth_client.post(
                f"/rounds/{round_id}/submit",
                json={"phrase": phrase}
            )
            assert response.status_code == 422  # Changed from 400 to 422 for validation errors

        # Valid submission should still work
        valid_response = auth_client.post(
            f"/rounds/{round_id}/submit",
            json={"phrase": "happy"}
        )
        assert valid_response.status_code == 200

        client.close()
        auth_client.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Quipflip Stress Tests")
    print("=" * 60)
    print("\nBackend must be running on http://localhost:8000")
    print("Start: uvicorn backend.main:app --reload")
    print("\nRun: pytest tests/test_stress_localhost.py -v -s")
    print("=" * 60)
