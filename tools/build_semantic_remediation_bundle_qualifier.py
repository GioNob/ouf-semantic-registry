"""Build the isolated byte-qualification command with hash-checked source closure."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
NAMES=('verify_semantic_image_archive','prepare_semantic_image_sbom','review_semantic_image_vulnerabilities','qualify_semantic_remediation_bundle')
def main():
    sources={name:(ROOT/(name+'.py')).read_text() for name in NAMES}
    hashes={name:hashlib.sha256(code.encode()).hexdigest() for name,code in sources.items()}
    entry='''#!/usr/bin/env python3
import hashlib,sys,types
SOURCE_HASHES=__SOURCE_HASH_VALUES__
SOURCES=__SOURCE_CODE_VALUES__
package=types.ModuleType('tools');package.__path__=[];sys.modules['tools']=package
for name,code in SOURCES.items():
    if hashlib.sha256(code.encode()).hexdigest()!=SOURCE_HASHES[name]:raise SystemExit('SOURCE_CLOSURE_UNPROVEN')
    module=types.ModuleType('tools.'+name);module.__file__='<embedded:'+name+'>'
    sys.modules[module.__name__]=module;setattr(package,name,module)
    exec(compile(code,module.__file__,'exec'),module.__dict__)
raise SystemExit(sys.modules['tools.qualify_semantic_remediation_bundle'].main())
'''
    entry=entry.replace('__SOURCE_HASH_VALUES__',repr(hashes),1).replace('__SOURCE_CODE_VALUES__',repr(sources),1)
    # Dictionary insertion order is the dependency import order.
    (ROOT/'semantic_remediation_bundle_qualifier.py').write_text(entry)
if __name__=='__main__':main()
