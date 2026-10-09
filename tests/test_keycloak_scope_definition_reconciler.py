import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"reconcile-keycloak-client-scope-definition.py"

def load_module():
    spec=importlib.util.spec_from_file_location("scope_definition",SCRIPT)
    module=importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module

def test_desired_scope_is_oidc_and_included_in_token_scope():
    m=load_module()
    doc=m.desired("ouf.semantic.read")
    assert doc["protocol"]=="openid-connect"
    assert doc["attributes"]["include.in.token.scope"]=="true"
    assert doc["attributes"]["display.on.consent.screen"]=="false"

def test_scope_name_validation_accepts_ouf_capability_names():
    m=load_module()
    m.validate_name("ouf.onboarding.configuration.read","SCOPE")
