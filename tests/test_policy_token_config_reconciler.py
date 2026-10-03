import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"reconcile-policy-token-config.py"

def load_module():
    spec=importlib.util.spec_from_file_location("policy_token_config",SCRIPT)
    module=importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module

def test_normalize_preserves_explicit_order_and_deduplicates():
    m=load_module()
    assert m.normalize([
        "authorization.bundle.read",
        "ouf.semantic.read ouf.onboarding.configuration.read",
        "ouf.semantic.read",
    ])=="authorization.bundle.read ouf.semantic.read ouf.onboarding.configuration.read"

def test_render_changes_only_required_scope(tmp_path):
    m=load_module()
    path=tmp_path/"udp.conf"
    path.write_text(
        "OUF_POLICY_TOKEN_CLIENT_ID=ouf-udp\n"
        "OUF_POLICY_TOKEN_REQUIRED_SCOPE=authorization.bundle.read\n"
        "OUF_POLICY_TOKEN_SECRET_FILE=/secret\n"
    )
    state=m.inspect(path,"authorization.bundle.read ouf.semantic.read")
    rendered=m.render(state,"authorization.bundle.read ouf.semantic.read")
    assert rendered==(
        "OUF_POLICY_TOKEN_CLIENT_ID=ouf-udp\n"
        "OUF_POLICY_TOKEN_REQUIRED_SCOPE=authorization.bundle.read ouf.semantic.read\n"
        "OUF_POLICY_TOKEN_SECRET_FILE=/secret\n"
    )

def test_duplicate_scope_key_fails_closed(tmp_path):
    m=load_module()
    path=tmp_path/"udp.conf"
    path.write_text(
        "OUF_POLICY_TOKEN_REQUIRED_SCOPE=a\n"
        "OUF_POLICY_TOKEN_REQUIRED_SCOPE=b\n"
    )
    try:
        m.inspect(path,"a")
        assert False
    except m.ReconcileError as exc:
        assert str(exc)=="DUPLICATE_SCOPE_KEY"
