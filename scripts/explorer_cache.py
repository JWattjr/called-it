"""Reuse this run's audited immutable Explorer records; never cache RPC state."""
import hashlib
import json
import re
from datetime import datetime, timezone


def load_verified_cache(root, source_commit):
    path=root/'.secrets/r5-explorer-cache.json'
    report=json.loads((root/'deploy/r5-explorer-audit.json').read_text())
    raw=path.read_bytes()
    assert report['passed'] is True and report['releaseAttempt']==5
    assert hashlib.sha256(raw).hexdigest()==report['cacheSha256'], 'Explorer pre-audit cache changed'
    cache=json.loads(raw)
    assert cache['releaseAttempt']==5 and cache['sourceCommit']==report['sourceCommit']==source_commit
    return cache['responses']


def cached_json(cache, url, at=None):
    match=re.fullmatch(r'https://explorer-studio\.genlayer\.com/api/transactions/(0x[0-9a-fA-F]{64})',url)
    entry=cache.get(url)
    if not match or not entry or entry.get('httpStatus')!=200:return None
    now=datetime.now(timezone.utc) if at is None else at
    age=(now-datetime.fromisoformat(entry['fetchedAt'])).total_seconds()
    data=entry.get('data',{});transaction=data.get('transaction',data)
    if not 0<=age<=1800 or transaction.get('status')!='FINALIZED' or str(transaction.get('hash','')).lower()!=match.group(1).lower():return None
    return data
