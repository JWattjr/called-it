import hashlib
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

sys.path.insert(0,str(Path('scripts').resolve()))
from explorer_cache import cached_json,load_verified_cache

H='0x'+'ab'*32
URL='https://explorer-studio.genlayer.com/api/transactions/'+H
NOW=datetime(2026,10,20,tzinfo=timezone.utc)


def test_fresh_exact_final_record_can_be_reused():
    data={'hash':H,'status':'FINALIZED'}
    entry={'httpStatus':200,'fetchedAt':(NOW-timedelta(seconds=60)).isoformat(),'data':data}
    assert cached_json({URL:entry},URL,at=NOW)==data


def test_expired_wrong_identity_nonfinal_or_non200_records_require_live_fetch():
    valid={'httpStatus':200,'fetchedAt':NOW.isoformat(),'data':{'hash':H,'status':'FINALIZED'}}
    cases=[{**valid,'fetchedAt':(NOW-timedelta(seconds=1801)).isoformat()},
           {**valid,'data':{'hash':'0x'+'cd'*32,'status':'FINALIZED'}},
           {**valid,'data':{'hash':H,'status':'ACCEPTED'}},
           {**valid,'httpStatus':503}]
    assert all(cached_json({URL:entry},URL,at=NOW) is None for entry in cases)
    assert cached_json({URL:valid},URL+'?other=1',at=NOW) is None


def test_cache_must_match_the_published_audit_digest_and_source(tmp_path):
    (tmp_path/'.secrets').mkdir();(tmp_path/'deploy').mkdir()
    path=tmp_path/'.secrets/r5-explorer-cache.json'
    path.write_text(json.dumps({'releaseAttempt':5,'sourceCommit':'source','responses':{}}))
    report={'passed':True,'releaseAttempt':5,'sourceCommit':'source','cacheSha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    (tmp_path/'deploy/r5-explorer-audit.json').write_text(json.dumps(report))
    assert load_verified_cache(tmp_path,'source')=={}
    path.write_text(path.read_text()+' ')
    with pytest.raises(AssertionError,match='cache changed'):load_verified_cache(tmp_path,'source')
