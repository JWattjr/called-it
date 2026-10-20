"""Package the stopped revision-3 attempt locally; no network calls or signing."""
import base64,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from chain import load,save,ROOT

p=load()
assert p.get('releaseAttempt')==3
failures=[]
for label in ('r3-resolve-take-1','r3-resolve-take-1-owner-recovery-1'):
    r=json.loads((ROOT/'deploy/receipts'/(label+'.json')).read_text())
    leader=(r['consensus_data']['leader_receipt'] or [{}])[0]
    assert r['status']=='FINALIZED' and leader['execution_result']=='ERROR'
    failures.append({'label':label,'hash':r['hash'],'status':'FINALIZED','result':r['result_name'],'execution':'ERROR','error':base64.b64decode(leader['result'])[1:].decode('utf8'),'stateApplied':False})
for contract in p['contracts'].values():
    assert hashlib.sha256((ROOT/'contracts'/contract['source']).read_bytes()).hexdigest()==contract['sha256']
assert sum(p['deposits'].values())==20
source=next(e for e in p['takes'] if e['label']=='sources-unreachable')
p.update(releaseStatus='STOPPED_FINALIZED_ERROR',failedResolutionAttempts=failures,stopFailure=failures[-1],blockers=[
    'Apple resolution and the owner-authorized single recovery both finalized with execution errors. Chain writes stopped.',
    'Revision-3 Apple YES, Nintendo NO and no-evidence default live resolutions remain unproven.',
    'Real VOID_SOURCES_UNREACHABLE is unproven: all admitted article preflights were FETCHED; no result was forced.',
    'Two-wallet matched bet holds 2 wei; settlement, verified native claims and new public records remain unproven.',
    'Full revision-3 network and publication link audit incomplete; production redeploy and push were not performed.'
],unreachableProof={'proven':False,'actualCase':'NOT_RESOLVED_STOPPED_ON_APPLE_FAILURE','take':source['take']['id'],'preflights':[v['preflight'] for v in source['resolution']['evidence']],'note':'Honest unlisted article fetched successfully. No real access failure was manufactured; no resolution attempted after Apple failure.'},implementationChecks={'contractTestsPassed':50,'releaseTestsPassed':4,'appTestsPassed':7,'typecheck':'PASS','eslint':'PASS','productionBuild':'PASS','genvmLint':'All four passed during implementation; unchanged resolver rechecked PASS during recovery.'},limitations=[
    'Model output reliability remains unresolved: nonverbatim quote and invalid resolution schema caused finalized errors.',
    'Local mocked fetch and timeout tests do not prove real network refunds.',
    'The approved cumulative deposit budget is exhausted at 20 wei; no additional deposit is authorized.',
    'The 29 October and 4 November live takes stay on revision 2 with its original immutable policy.',
    'Production remains revision 2. Local revision-3 commits and the stopped-run package have not been pushed. No Portal submission.'
],publication={'productionRevision':2,'newProductionDeployment':False,'newChangesPushed':False,'portalSubmitted':False})
save(p)
(ROOT/'deploy/proof-verification.json').write_text(json.dumps({'checkedAt':datetime.now(timezone.utc).isoformat(),'passed':False,'readOnly':True,'failures':p['blockers'],'executionFailures':failures,'localChecks':p['implementationChecks'],'partialLinkAudit':'deploy/fairness-link-audit.json','note':'Full revision-3 audit was not run after the live proof stopped. The earlier green report is archived under deploy/releases/v2-proof-verification.json.'},indent=2)+'\n',encoding='utf8')
print('Stopped-run artifacts updated locally. No transaction or publication performed.')
