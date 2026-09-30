#!/usr/bin/env python3
"""Read safe failure metadata for the actual paused cinema run; no retry or payload."""
import json
import os
import re
import uuid
import r4a_cinema_execution_readback as readback

RUN = '86809c17-3354-45ca-a7e6-57e903944b24'


def symbolic(value):
    if value is None:
        return None
    return str(value) if re.fullmatch(r'[A-Z0-9_]{1,120}', str(value)) else 'NON_SYMBOLIC_REDACTED'


def main():
    if os.geteuid() != 0:
        raise RuntimeError('ROOT_REQUIRED')
    receipt = readback.private(readback.ROOT / 'cinema-source-activation.json')
    if (receipt.get('status') != 'PASS' or receipt.get('sourceActivation') is not True or
        receipt.get('sourceId') != readback.SOURCE or receipt.get('versionId') != readback.VERSION or
        receipt.get('configurationHash') != readback.HASH or receipt.get('publicationId') != readback.PUBLICATION):
        raise RuntimeError('ACTIVATION_RECEIPT_MISMATCH')
    checksum = receipt['checksum']
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', checksum):
        raise RuntimeError('CHECKSUM_INVALID')
    print('R4A_CINEMA_QUARANTINE_DIAGNOSTIC=READ_ONLY RUN_ID=' + RUN, flush=True)
    scope = "run_id='" + RUN + "' and source_id='" + readback.SOURCE + "' and bundle_checksum='" + checksum + "'"
    data = readback.sql('ouf_ingestion', "with r as (select run_id,state,failure_code from ouf_ingestion.ing_run where " + scope + "), q as (select quarantine_id,attempt_id,reason_code,state,lifecycle_state,lifecycle_version,blocking,payload_ref is not null payload_ref_present,evidence_ref like 'contract-or-mapping:%' contract_or_mapping_evidence,evidence_ref like 'schema-surveillance:%' schema_evidence from ouf_ingestion.ing_quarantine where run_id in(select run_id from r)), a as (select attempt_id,attempt_no,state,reason_code from ouf_ingestion.processing_attempt where run_id in(select run_id from r)), e as (select event_type,severity,error_code from ouf_ingestion.operational_event where run_id in(select run_id from r) order by event_id desc limit 20), p as (select state,count(*) count from ouf_ingestion.ing_partition where run_id in(select run_id from r) group by state) select json_build_object('runs',coalesce((select json_agg(r) from r),'[]'::json),'quarantine',coalesce((select json_agg(q) from q),'[]'::json),'attempts',coalesce((select json_agg(a) from a),'[]'::json),'events',coalesce((select json_agg(e) from e),'[]'::json),'partitions',coalesce((select json_agg(p) from p),'[]'::json))")
    if len(data['runs']) != 1:
        raise RuntimeError('EXACT_RUN_NOT_FOUND')
    for section, rows in data.items():
        for row in rows:
            for key in ('run_id','quarantine_id','attempt_id'):
                if row.get(key) is not None:
                    row[key] = str(uuid.UUID(row[key]))
            for key in ('state','reason_code','failure_code','lifecycle_state','event_type','severity','error_code'):
                if key in row:
                    row[key] = symbolic(row[key])
        print('QUARANTINE_' + section.upper() + '=' + json.dumps(rows, sort_keys=True))
    print('R4A_CINEMA_QUARANTINE_DIAGNOSTIC=COMPLETE READ_ONLY=true RETRY=false SOURCE_REACTIVATION=false PAYLOADS_NOT_PRINTED=true SECRETS_NOT_PRINTED=true')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print('R4A_CINEMA_QUARANTINE_DIAGNOSTIC=BLOCKED CODE=' + code + ' READ_ONLY=true SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
