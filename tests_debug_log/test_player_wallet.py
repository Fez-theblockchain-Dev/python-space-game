"""
Tests for persistent recording of new-player IP addresses.

Scope
-----
Every time a new player hits ``POST /api/player/join``, the server must
durably record the originating IP address in the ``player_ip_records`` table
(``backend_apis.models.PlayerIPRecord``). These tests exercise that contract
end-to-end against the real FastAPI app, swapping in an isolated in-memory
SQLite database via ``app.dependency_overrides[get_db]`` so the production
Postgres target is never touched.

What we verify
--------------
1. A brand-new player join writes exactly one IP row.
2. The row survives closing the DB session and reopening a fresh one
   (the "persistent" part of the record keeping).
3. Repeat joins from the same IP bump ``connection_count`` and
   ``last_seen_at`` instead of creating duplicates.
4. Different source IPs for the same UUID yield separate rows.
5. ``X-Forwarded-For`` is honored (real end-user IP behind a proxy/CDN).
6. The ``/api/player/ip-log/{uuid}`` endpoint returns the recorded data.
7. The join endpoint itself still succeeds when IP logging would fail
   (logging must never block a player from joining).
"""
from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend_apis.models import Base, PlayerIPRecord  # noqa: E402
from backend_apis.database import get_db  # noqa: E402
import server as server_module  # noqa: E402


def make_isolated_engine():
    """
    Fresh in-memory SQLite engine shared across threads.

    ``StaticPool`` + ``check_same_thread=False`` keeps the same underlying
    connection (and therefore the same ``:memory:`` DB) across the
    ``TestClient`` request thread and the test thread.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    return engine


class PlayerIPRecordingTestCase(unittest.TestCase):
    """Integration tests for persistent IP recording on /api/player/join."""

    def setUp(self):
        self.engine = make_isolated_engine()
        self.TestSession = sessionmaker(
            bind=self.engine, autoflush=False, autocommit=False, future=True
        )

        def override_get_db():
            db = self.TestSession()
            try:
                yield db
            finally:
                db.close()

        self.override_get_db = override_get_db
        server_module.app.dependency_overrides[get_db] = override_get_db

        self.client = TestClient(server_module.app)

        server_module.connected_players.clear()

    def tearDown(self):
        server_module.app.dependency_overrides.pop(get_db, None)
        self.client.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()
        server_module.connected_players.clear()

    def join(self, name: str, *, ip: str | None = None, user_agent: str | None = None):
        headers = {}
        if ip is not None:
            headers["X-Forwarded-For"] = ip
        if user_agent is not None:
            headers["User-Agent"] = user_agent
        response = self.client.post(
            "/api/player/join",
            json={"player_name": name},
            headers=headers,
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def all_records(self, db: Session | None = None) -> list[PlayerIPRecord]:
        owned = db is None
        db = db or self.TestSession()
        try:
            return db.query(PlayerIPRecord).order_by(PlayerIPRecord.id.asc()).all()
        finally:
            if owned:
                db.close()

    def test_new_player_join_writes_ip_row(self):
        """First-time join from a fresh IP creates exactly one record."""
        body = self.join("Astra", ip="203.0.113.7", user_agent="pytest/1.0")

        self.assertTrue(body["success"])
        player_id = body["player_id"]

        records = self.all_records()
        self.assertEqual(len(records), 1)
        row = records[0]
        self.assertEqual(row.player_uuid, player_id)
        self.assertEqual(row.player_name, "Astra")
        self.assertEqual(row.ip_address, "203.0.113.7")
        self.assertEqual(row.user_agent, "pytest/1.0")
        self.assertEqual(row.connection_count, 1)
        self.assertIsNotNone(row.first_seen_at)
        self.assertIsNotNone(row.last_seen_at)

    def test_ip_record_is_persistent_across_sessions(self):
        """The row must survive closing and reopening the DB session."""
        body = self.join("Rook", ip="198.51.100.22")
        player_id = body["player_id"]

        db1 = self.TestSession()
        try:
            first_read = (
                db1.query(PlayerIPRecord)
                .filter(PlayerIPRecord.player_uuid == player_id)
                .one()
            )
            self.assertEqual(first_read.ip_address, "198.51.100.22")
        finally:
            db1.close()

        db2 = self.TestSession()
        try:
            second_read = (
                db2.query(PlayerIPRecord)
                .filter(PlayerIPRecord.player_uuid == player_id)
                .one()
            )
            self.assertEqual(second_read.ip_address, "198.51.100.22")
            self.assertEqual(second_read.player_name, "Rook")
        finally:
            db2.close()

    def test_distinct_players_from_distinct_ips(self):
        """Two separate player joins from two separate IPs produce two rows."""
        body_a = self.join("Nova", ip="203.0.113.10")
        body_b = self.join("Quill", ip="203.0.113.11")

        records = self.all_records()
        self.assertEqual(len(records), 2)

        by_uuid = {r.player_uuid: r for r in records}
        self.assertIn(body_a["player_id"], by_uuid)
        self.assertIn(body_b["player_id"], by_uuid)
        self.assertEqual(by_uuid[body_a["player_id"]].ip_address, "203.0.113.10")
        self.assertEqual(by_uuid[body_b["player_id"]].ip_address, "203.0.113.11")

    def test_same_uuid_two_ips_creates_two_rows(self):
        """If the same player_uuid is seen from two IPs we keep both rows."""
        fixed_uuid = "abcdef12"
        with patch("server.uuid.uuid4") as mock_uuid4:
            mock_uuid4.return_value.__str__.return_value = fixed_uuid + "-rest"

            self.join("Orbit", ip="203.0.113.50")
            self.join("Orbit", ip="203.0.113.51")

        records = (
            self.all_records()
        )
        matching = [r for r in records if r.player_uuid == fixed_uuid]
        self.assertEqual(len(matching), 2)
        ips = sorted(r.ip_address for r in matching)
        self.assertEqual(ips, ["203.0.113.50", "203.0.113.51"])
        for row in matching:
            self.assertEqual(row.connection_count, 1)

    def test_repeat_join_from_same_ip_increments_count(self):
        """Repeat joins with the same (uuid, ip) upsert instead of duplicating."""
        fixed_uuid = "deadbeef"
        with patch("server.uuid.uuid4") as mock_uuid4:
            mock_uuid4.return_value.__str__.return_value = fixed_uuid + "-rest"

            self.join("Echo", ip="192.0.2.5")
            self.join("Echo", ip="192.0.2.5")
            self.join("Echo", ip="192.0.2.5")

        records = [
            r for r in self.all_records() if r.player_uuid == fixed_uuid
        ]
        self.assertEqual(len(records), 1, "expected a single upserted row")
        self.assertEqual(records[0].connection_count, 3)
        self.assertEqual(records[0].ip_address, "192.0.2.5")
        self.assertGreaterEqual(records[0].last_seen_at, records[0].first_seen_at)

    def test_x_forwarded_for_is_preferred_over_socket_peer(self):
        """When X-Forwarded-For is present we record the first hop, not the TCP peer."""
        self.join(
            "Proxy",
            ip="8.8.8.8, 10.0.0.1, 10.0.0.2",
        )

        records = self.all_records()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].ip_address, "8.8.8.8")

    def test_ip_log_endpoint_returns_recorded_entries(self):
        """GET /api/player/ip-log/{uuid} surfaces persisted records."""
        body = self.join("Sable", ip="203.0.113.200", user_agent="agent-007")
        player_id = body["player_id"]

        resp = self.client.get(f"/api/player/ip-log/{player_id}")
        self.assertEqual(resp.status_code, 200, resp.text)
        payload = resp.json()
        self.assertEqual(payload["player_uuid"], player_id)
        self.assertEqual(payload["count"], 1)
        self.assertEqual(len(payload["records"]), 1)
        entry = payload["records"][0]
        self.assertEqual(entry["ip_address"], "203.0.113.200")
        self.assertEqual(entry["user_agent"], "agent-007")
        self.assertEqual(entry["connection_count"], 1)

    def test_ip_log_endpoint_empty_for_unknown_uuid(self):
        resp = self.client.get("/api/player/ip-log/no-such-player")
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertEqual(payload["count"], 0)
        self.assertEqual(payload["records"], [])

    def test_join_still_succeeds_if_ip_logging_raises(self):
        """
        A failure in ``record_player_ip`` must not break the join flow —
        IP logging is best-effort observability, not a precondition.
        """
        with patch(
            "server.record_player_ip",
            side_effect=RuntimeError("simulated DB outage"),
        ):
            response = self.client.post(
                "/api/player/join",
                json={"player_name": "Resilient"},
                headers={"X-Forwarded-For": "203.0.113.99"},
            )

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["player_name"], "Resilient")

        self.assertEqual(self.all_records(), [])


class PlayerIPRecordModelTestCase(unittest.TestCase):
    """Sanity-check the ORM model itself, independent of the HTTP layer."""

    def setUp(self):
        self.engine = make_isolated_engine()
        self.Session = sessionmaker(bind=self.engine, future=True)

    def tearDown(self):
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_unique_constraint_on_uuid_ip_pair(self):
        """Two rows with the same (player_uuid, ip_address) must violate the
        table's uniqueness constraint — the app upserts to avoid this in
        normal flow, but the constraint is the guardrail."""
        db = self.Session()
        try:
            db.add(
                PlayerIPRecord(
                    player_uuid="u1",
                    ip_address="1.2.3.4",
                    connection_count=1,
                )
            )
            db.commit()

            db.add(
                PlayerIPRecord(
                    player_uuid="u1",
                    ip_address="1.2.3.4",
                    connection_count=1,
                )
            )
            with self.assertRaises(Exception):
                db.commit()
            db.rollback()
        finally:
            db.close()

    def test_to_dict_shape(self):
        db = self.Session()
        try:
            row = PlayerIPRecord(
                player_uuid="u-shape",
                player_name="Shape",
                ip_address="9.9.9.9",
                user_agent="ua",
                connection_count=4,
            )
            db.add(row)
            db.commit()
            db.refresh(row)

            d = row.to_dict()
            self.assertEqual(
                set(d.keys()),
                {
                    "player_uuid",
                    "player_name",
                    "ip_address",
                    "user_agent",
                    "connection_count",
                    "first_seen_at",
                    "last_seen_at",
                },
            )
            self.assertEqual(d["player_uuid"], "u-shape")
            self.assertEqual(d["connection_count"], 4)
            self.assertIsInstance(d["first_seen_at"], str)
            self.assertIsInstance(d["last_seen_at"], str)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
