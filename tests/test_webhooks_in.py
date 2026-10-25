"""Generic webhook source (roadmap B-126): signature + replay.

The door's three locks, attacked one at a time:

- a delivery signed with the shown-once secret lands as
  chunks on the bound source, in order;
- a bad signature, an unknown token, and a stale timestamp
  are each refused (401) and archive NOTHING;
- the same signed delivery twice is a replay: refused (409)
  the second time, chunks not duplicated;
- neither the token nor the signing secret exists anywhere
  in the database file (hash + derivation, never storage).
"""

import json
import time

from conftest import bearer, make_group, register
from gpa.services import webhooks_in as webhook_service


def world(client):
    owner = register(client)
    group = make_group(client, owner)
    source = client.post(
        f"/api/v1/groups/{group['id']}/sources",
        json={
            "kind": "chat_paste",
            "title": "Form feed",
            "granted_scope": "webhook feed",
            "chunks": [{"text": "Feed opened.", "sender": "Organiser"}],
        },
        headers=bearer(owner),
    )
    assert source.status_code == 201, source.text
    endpoint = client.post(
        f"/api/v1/groups/{group['id']}/webhook-endpoints",
        json={"source_id": source.json()["id"]},
        headers=bearer(owner),
    )
    assert endpoint.status_code == 201, endpoint.text
    return owner, group, source.json(), endpoint.json()


def deliver(client, endpoint, payload, *, secret=None, timestamp=None, signature=None):
    raw = json.dumps(payload).encode("utf-8")
    stamp = str(timestamp if timestamp is not None else int(time.time()))
    sig = signature
    if sig is None:
        sig = webhook_service.signature_for(
            secret if secret is not None else endpoint["signing_secret"],
            stamp, raw,
        )
    return client.post(
        endpoint["url_path"],
        content=raw,
        headers={"x-gpa-signature": sig, "x-gpa-timestamp": stamp},
    )


def chunk_texts(client, owner, group, source_id):
    detail = client.get(
        f"/api/v1/groups/{group['id']}/sources/{source_id}", headers=bearer(owner)
    )
    return [c["text"] for c in detail.json()["chunks"]]


PAYLOAD = {
    "messages": [
        {"sender": "Form", "text": "Two more chairs, please.",
         "sent_at": "2026-10-22T09:00:00+00:00"},
        {"sender": "Form", "text": "And a bigger urn."},
    ]
}


def test_signed_delivery_lands_as_chunks(client):
    owner, group, source, endpoint = world(client)
    # Shown once: the creation response carries both secrets.
    assert endpoint["token"] and endpoint["signing_secret"]
    assert endpoint["url_path"].endswith(endpoint["token"])

    response = deliver(client, endpoint, PAYLOAD)
    assert response.status_code == 201, response.text
    assert response.json() == {"source_id": source["id"], "chunks_added": 2}
    assert chunk_texts(client, owner, group, source["id"]) == [
        "Feed opened.", "Two more chairs, please.", "And a bigger urn.",
    ]

    # The list view shows neither secret ever again.
    listed = client.get(
        f"/api/v1/groups/{group['id']}/webhook-endpoints", headers=bearer(owner)
    ).json()
    assert listed[0]["token"] is None
    assert listed[0]["signing_secret"] is None
    assert listed[0]["token_prefix"] == endpoint["token_prefix"]


def test_bad_signature_and_unknown_token_archive_nothing(client):
    owner, group, source, endpoint = world(client)
    forged = deliver(client, endpoint, PAYLOAD, secret="not-the-secret")
    assert forged.status_code == 401, forged.text

    unknown = client.post(
        "/api/v1/webhooks/source/no-such-token",
        content=json.dumps(PAYLOAD).encode("utf-8"),
        headers={"x-gpa-signature": "ab" * 32, "x-gpa-timestamp": str(int(time.time()))},
    )
    assert unknown.status_code == 401, unknown.text
    assert chunk_texts(client, owner, group, source["id"]) == ["Feed opened."]


def test_stale_timestamp_is_refused_even_with_a_true_signature(client):
    owner, group, source, endpoint = world(client)
    stale = int(time.time()) - webhook_service.REPLAY_WINDOW_SECONDS - 60
    response = deliver(client, endpoint, PAYLOAD, timestamp=stale)
    assert response.status_code == 401, response.text
    assert chunk_texts(client, owner, group, source["id"]) == ["Feed opened."]


def test_replay_is_refused_and_never_duplicates(client):
    owner, group, source, endpoint = world(client)
    first = deliver(client, endpoint, PAYLOAD)
    assert first.status_code == 201, first.text
    replay = deliver(client, endpoint, PAYLOAD)  # same stamp, same signature
    assert replay.status_code == 409, replay.text
    assert chunk_texts(client, owner, group, source["id"]) == [
        "Feed opened.", "Two more chairs, please.", "And a bigger urn.",
    ]


def test_revoked_endpoint_refuses(client):
    owner, group, source, endpoint = world(client)
    revoked = client.delete(
        f"/api/v1/groups/{group['id']}/webhook-endpoints/{endpoint['id']}",
        headers=bearer(owner),
    )
    assert revoked.status_code == 204, revoked.text
    response = deliver(client, endpoint, PAYLOAD)
    assert response.status_code == 401, response.text
    assert chunk_texts(client, owner, group, source["id"]) == ["Feed opened."]


def test_secrets_are_nowhere_in_the_database_file(client, settings):
    owner, group, source, endpoint = world(client)
    deliver(client, endpoint, PAYLOAD)
    raw = (settings.database_url.replace("sqlite:///", "/"))
    from pathlib import Path

    blob = Path(raw).read_bytes()
    assert endpoint["token"].encode("utf-8") not in blob
    assert endpoint["signing_secret"].encode("utf-8") not in blob
