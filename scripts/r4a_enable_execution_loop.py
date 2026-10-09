#!/usr/bin/env python3
"""Reuse the proven rollout to enable execution while preserving activation=true."""
import argparse
import contextlib
import hashlib
from pathlib import Path
import sys
import r4a_enable_activation_worker as worker
import r4a_execution_loop_inventory as inventory

ROOT = worker.ROOT
BASE_STATE = ROOT / 'ingestion-activation-worker-prepare.json'
BASE_RECEIPT = ROOT / 'ingestion-activation-worker-switch.json'
STATE = ROOT / 'ingestion-execution-loop-prepare.json'
RECEIPT = ROOT / 'ingestion-execution-loop-switch.json'

# Configure the shared algorithm in this isolated CLI process. No code from
# another rollout is running; default activation CLI behavior stays unchanged.
worker.NAME = 'ouf-ingestion-r4a-execution-loop-candidate'
worker.STATE = STATE
worker.RECEIPT = RECEIPT
worker.KEY = 'ouf.ingestion.execution.enabled'
worker.STAGE_PREFIX = 'execution-loop-'
worker.ROLLBACK_PREFIX = 'ouf-ingestion-execution-loop-rollback-'
worker.FAILED_PREFIX = 'ouf-ingestion-execution-loop-failed-'
worker.FAILURE_MARKERS += ('ING_AUTOMATIC_DELIVERY_FAILED', 'ING_AUTOMATIC_EXECUTION_FAILED')
original_queues = worker.queues_empty
original_totals = worker.totals
original_save = worker.save


def queues_empty(quiet=False):
    original_queues(quiet)
    count = worker.rollout.sql("select count(*) from ouf_ingestion.handoff_outbox where state in ('READY','DELIVERING','FAILED_RETRYABLE')")
    if not quiet:
        print('EXECUTION_LOOP_EXISTING_DELIVERABLE_HANDOFFS=' + count)
    if count != '0':
        raise RuntimeError('EXECUTION_LOOP_EXISTING_HANDOFFS_REVIEW_REQUIRED')


def totals():
    return original_totals() + (worker.rollout.sql('select count(*) from ouf_ingestion.handoff_outbox'),)


def save(receipt):
    value = dict(receipt)
    value['enabledProperty'] = worker.KEY
    if 'workerEnabled' in value:
        value['executionEnabled'] = value.pop('workerEnabled')
        value['activationEnabled'] = True
    original_save(value)


def context():
    base = worker.rollout.private_json(BASE_STATE)
    receipt = worker.rollout.private_json(BASE_RECEIPT)
    refresher = worker.rollout.private_json(ROOT / 'publication-refresher-adoption.json')
    row = worker.prepare.probe.candidate_row(worker.access.prepare.SOURCE, worker.access.prepare.VERSION, worker.access.prepare.HASH)
    if row['state'] != 'APPROVED':
        raise RuntimeError('SOURCE_NOT_APPROVED')
    live = worker.prepare.probe.inspect('ouf-ingestion')
    image = worker.prepare.probe.inspect(live['Image'], 'image')
    if (base.get('status') != 'PASS' or receipt.get('status') != 'PASS' or receipt.get('workerEnabled') is not True or
        live['Id'] != base.get('candidateId') or live['Image'] != base.get('imageId') or
        image['Config'].get('Labels', {}).get('org.opencontainers.image.revision') != worker.prepare.REVISION or
        refresher.get('status') != 'PASS' or refresher.get('discoveryHttp') != 200 or
        refresher.get('configReadScopePresent') is not True):
        raise RuntimeError('EXECUTION_ACTIVATION_BASELINE_DRIFT')
    worker.prepare.guard(live, image)
    settings = worker.rollout.tokens_fresh(live, 'ouf-lab')
    path = Path(next(m['Source'] for m in live['Mounts'] if m['Destination'] == worker.prepare.probe.PROPERTIES))
    original = path.read_bytes()
    if str(path) != base.get('properties') or hashlib.sha256(original).hexdigest() != base.get('propertiesSha256'):
        raise RuntimeError('ACTIVATION_PROPERTIES_BASELINE_DRIFT')
    if worker.prepare.environment(live) != worker.prepare.environment(base['old']):
        raise RuntimeError('ACTIVATION_ENV_BASELINE_DRIFT')
    facts = inventory.facts(live, original.decode('utf-8'))
    if (facts.get('ING_ACTIVATION_LOOP_EFFECTIVE_DIAGNOSTIC') != 'TRUE' or
        facts.get('ING_EXECUTION_LOOP_PROPERTY_COUNT') != '0' or facts.get('ING_EXECUTION_LOOP_ENV') != 'ABSENT' or
        facts.get('ING_EXECUTION_LOOP_COMMAND_OVERRIDE_PRESENT') != 'false' or
        facts.get('ING_SPRING_APPLICATION_JSON_PRESENT') != 'false' or
        facts.get('ING_EXECUTION_LOOP_EFFECTIVE_DIAGNOSTIC') != 'FALSE'):
        raise RuntimeError('EXECUTION_DISABLED_OR_ACTIVATION_ENABLED_NOT_PROVEN')
    if any(worker.prepare.probe.literal_property(original.decode(), key) != value for key, value in settings.items()):
        raise RuntimeError('EXECUTION_TRANSPORT_DRIFT')
    token_path = Path(next(m['Source'] for m in live['Mounts'] if m['Destination'] == worker.prepare.probe.AUTH)) / Path(settings['ouf.ingestion.activation.token-file']).relative_to(worker.prepare.probe.AUTH)
    token, claims = worker.access.token_claims(token_path)
    if worker.access.prepare.CAP not in str(claims.get('scope', '')).split():
        raise RuntimeError('EXECUTION_TOKEN_CONFIG_READ_SCOPE_MISSING')
    worker.access.discovery(settings, token)
    queues_empty()
    history = worker.rollout.history()
    if len([x for x in history if x['version'] is not None]) != 14 or not all(x['success'] for x in history) or history[-1]['version'] != '14':
        raise RuntimeError('EXECUTION_FLYWAY14_DRIFT')
    worker.rollout.ready(1)
    return live, image, path, original, row, history, totals()


worker.context = context
worker.queues_empty = queues_empty
worker.totals = totals
worker.save = save


class Output:
    def __init__(self, stream):
        self.stream = stream
    def write(self, text):
        return self.stream.write(text.replace('R4A_ACTIVATION_WORKER', 'R4A_EXECUTION_LOOP')
            .replace('WORKER_ENABLED=true', 'EXECUTION_ENABLED=true ACTIVATION_ENABLED=true')
            .replace('WORKER_DISABLED_RESTORED=true', 'EXECUTION_DISABLED_RESTORED=true ACTIVATION_ENABLED_PRESERVED=true'))
    def flush(self):
        self.stream.flush()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'plan', 'apply'))
    try:
        args = parser.parse_args()
        with contextlib.redirect_stdout(Output(sys.stdout)):
            worker.main(args.mode)
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print('R4A_EXECUTION_LOOP=BLOCKED CODE=' + code + ' SOURCE_ACTIVATION=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
