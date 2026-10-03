from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_client_scope_reconciler_is_generic_idempotent_and_secret_safe():
    raw=(ROOT/"scripts/reconcile-keycloak-client-scope.py").read_text()
    assert 'choices=("plan","apply","verify")' in raw
    assert 'choices=("default","optional")' in raw
    assert "CLIENT_ID=" in raw
    assert "SCOPE=" in raw
    assert "VERIFY=PASS" in raw
    assert "SECRETS_PRINTED=false" in raw
    assert "KCADM_SESSION_EXPIRED" in raw
    assert "authorization.permissions.read" not in raw
    assert "ouf-human-admin" not in raw
