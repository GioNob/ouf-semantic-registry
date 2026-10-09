#!/usr/bin/env python3
"""Read packaged national-provider settings without jobs, provider calls or service changes."""
import hashlib,json,os,stat,subprocess,sys,tempfile,zipfile
from pathlib import Path
from urllib.parse import urlsplit

DEFAULTS_SHA="a2799f0a63c93464c0940957a9537da72b3ca13aebf89f510469fec7c1fb6572"
CONTAINER="ouf-semantic"
STAGE="PRECHECK"

def require(ok):
    if not ok:raise ValueError("CONFIGURATION_UNPROVEN")

def run(argv,timeout=30):
    return subprocess.run(argv,capture_output=True,timeout=timeout)

def inspect():
    result=run(["docker","inspect",CONTAINER])
    require(result.returncode==0 and len(result.stdout)<=1048576)
    rows=json.loads(result.stdout);require(len(rows)==1)
    return rows[0]

def fingerprint(row):
    return {k:row[k] for k in ("Id","Image","Config","Mounts","NetworkSettings")}

def summary(row,packaged_hash,external_config_present,packaged_override_count=0):
    env={}
    for item in row["Config"].get("Env") or []:
        name,separator,value=item.partition("=")
        require(separator and name not in env);env[name]=value
    def normalized(name):return name.replace(".","_").replace("-","_").upper()
    override_names=sorted(name for name in env if
        normalized(name)=="SPRING_APPLICATION_JSON" or normalized(name).startswith(("SPRING_CONFIG","SPRING_PROFILES","OUF_SEMANTIC_PROVIDERS_","OUF_SEMANTIC_DISCOVERY_WORKER_"))
        or normalized(name) in ("JAVA_TOOL_OPTIONS","JDK_JAVA_OPTIONS","JAVA_OPTS","_JAVA_OPTIONS"))
    command=(row["Config"].get("Entrypoint") or [])+(row["Config"].get("Cmd") or [])
    command_matches=command==["java","-XX:MaxRAMPercentage=75","-jar","/app/application.jar"]
    unexpected_mounts=sum(m["Destination"] not in
        ("/run/ouf-semantic-auth","/run/secrets/semantic-read-owner.key") for m in row.get("Mounts",[]))
    base_proven=(row["State"]["Running"] is True and packaged_hash==DEFAULTS_SHA and
        row["Config"].get("WorkingDir")=="/app" and command_matches and not override_names
        and not unexpected_mounts and not external_config_present and packaged_override_count==0)
    def flag(key,default):
        value=env.get(key,str(default)).strip().lower()
        return {"true":True,"false":False}.get(value,"UNPROVEN") if base_proven else "UNPROVEN"
    provider=flag("OUF_SCHEMA_GOV_ENABLED",False)
    worker=flag("OUF_DISCOVERY_WORKER_ENABLED",True)
    try:
        origin=urlsplit(env.get("OUF_SCHEMA_GOV_GATEWAY_BASE_URL","https://gateway.invalid"))
        configured=bool(origin.hostname) and origin.hostname!="gateway.invalid" and origin.scheme=="https" \
            and not origin.username and not origin.password and not origin.query and not origin.fragment
    except ValueError:configured=False
    blockers=[]
    if provider is not True:blockers.append("PROVIDER_DISABLED_OR_UNPROVEN")
    if worker is not True:blockers.append("WORKER_DISABLED_OR_UNPROVEN")
    if not configured:blockers.append("GATEWAY_ORIGIN_MISSING_OR_UNSAFE")
    return dict(status="READ_ONLY_PACKAGED_CONFIGURATION",running=row["State"]["Running"],
        packagedDefaultsMatchReviewedSource=packaged_hash==DEFAULTS_SHA,
        startupCommandMatchesReviewedSource=command_matches,
        overrideEnvironmentNames=override_names,unexpectedMountCount=unexpected_mounts,
        externalConfigurationPresent=external_config_present,packagedOverrideCount=packaged_override_count,configurationProven=base_proven,
        providerEnabled=provider,workerEnabled=worker,gatewayOriginConfigured=configured,
        configurationBlockers=blockers,providerConnectivityProven=False,
        mcpDiscoveryBindingProven=False,providerCalls=0,discoveryJobsCreated=0,
        containerLifecycleOperations=0,configurationWrites=0,secretValuesPrinted=False)

def main():
    global STAGE
    require(os.geteuid()==0 and sys.flags.isolated and sys.dont_write_bytecode)
    os.umask(0o077)
    STAGE="INSPECT_RUNNING_SEMANTIC"
    before=inspect();require(before["State"]["Running"] is True)
    STAGE="READ_PACKAGED_DEFAULTS"
    with tempfile.TemporaryDirectory(prefix="ouf-discovery-config.") as directory:
        jar=Path(directory)/"application.jar"
        result=run(["docker","cp",CONTAINER+":/app/application.jar",str(jar)],timeout=60)
        require(result.returncode==0)
        info=jar.lstat();require(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and 0<info.st_size<=134217728)
        with zipfile.ZipFile(jar) as archive:
            matches=[i for i in archive.infolist() if i.filename=="BOOT-INF/classes/application.yml"]
            require(len(matches)==1 and 0<matches[0].file_size<=65536)
            packaged_hash=hashlib.sha256(archive.read(matches[0])).hexdigest()
            packaged_override_count=sum(
                i.filename.startswith("BOOT-INF/classes/application-") and i.filename.endswith((".properties",".yml",".yaml"))
                or i.filename in ("BOOT-INF/classes/application.properties","BOOT-INF/classes/application.yaml",
                    "BOOT-INF/classes/bootstrap.properties","BOOT-INF/classes/bootstrap.yml","BOOT-INF/classes/bootstrap.yaml")
                for i in archive.infolist())
    STAGE="CHECK_EXTERNAL_CONFIGURATION"
    check=run(["docker","exec",CONTAINER,"sh","-c",
        'for f in /app/application.properties /app/application.yml /app/application.yaml /app/config /config; do if [ -e "$f" ]; then exit 10; fi; done'])
    require(check.returncode in (0,10))
    result=summary(before,packaged_hash,check.returncode==10,packaged_override_count)
    STAGE="VERIFY_RUNTIME_UNCHANGED"
    after=inspect();require(after["State"]["Running"] is True and fingerprint(before)==fingerprint(after))
    print("TEATRI_DISCOVERY_CONFIGURATION="+json.dumps(result,sort_keys=True),flush=True)

if __name__=="__main__":
    try:main()
    except Exception:
        print("TEATRI_DISCOVERY_CONFIGURATION=BLOCKED STAGE="+STAGE+" READ_ONLY=true NO_RAW_OUTPUT=true",flush=True)
        sys.exit(1)
