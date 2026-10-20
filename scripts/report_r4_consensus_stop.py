"""Record the failed matched ruling; no network calls, retry or publication."""
import base64,json
from datetime import datetime,timezone
from genlayer_py.abi.calldata import decode
from chain import ROOT,load,save,success

p=load();assert p['releaseAttempt']==4 and sum(p['deposits'].values())==22
label='r4-resolve-take-5';r=json.loads((ROOT/'deploy/receipts'/(label+'.json')).read_text())
assert r['status']=='FINALIZED' and r['result_name']=='MAJORITY_DISAGREE' and not success(r)
leader=r['consensus_data']['leader_receipt'][0]
proposal=decode(base64.b64decode(leader['eq_outputs']['0'])[1:])
e=next(e for e in p['takes'] if e['label']=='sources-unreachable')
assert e['resolution']['status']=='OPEN' and e['bet']['status']=='MATCHED' and e['bet']['total']=='2' and not e['bet']['claims']
failure={'label':label,'hash':r['hash'],'status':'FINALIZED','result':'MAJORITY_DISAGREE','leaderExecution':leader['execution_result'],'votes':{v:list(r['consensus_data']['votes'].values()).count(v) for v in set(r['consensus_data']['votes'].values())},'unacceptedLeaderProposal':{k:proposal[k] for k in ('verdict','resolution_case','reason')},'stateApplied':False,'individualValidatorReasons':'Not exposed by the receipt; disagreement cause is not proven.'}
p.update(releaseStatus='STOPPED_CONSENSUS_DISAGREEMENT',stopFailure=failure,failedResolutionAttempts=[failure],
    blockers=['The matched Grammy ruling finalized MAJORITY_DISAGREE; no ruling was applied. Chain writes stopped with no retry.',
        'New escrow still holds the two original stakes in MATCHED state. Settlement, claims and public record are unproven.',
        'Real blocked-source VOID is unproven: the article fetched successfully and no final result was reached.',
        'Full publication audit, Vercel production deployment and push were not performed after the failure.'],
    unreachableProof={'proven':False,'actualCase':'NO_FINAL_CONSENSUS','take':'take-5','preflights':[v['preflight'] for v in e['resolution']['evidence']],'note':'The unlisted article was FETCHED; the leader proposed NO but the network rejected it. This was not a finalized NO or VOID.'},
    limitations=['Models can still disagree despite valid schema and exact quotations. The rejected leader proposal does not establish an outcome.',
        'The specific reason each validator disagreed is not exposed; interpretation ambiguity is an inference, not a proven diagnosis.',
        'Mocked 401/403 and 48-hour timeout tests do not constitute live proof of those cases.',
        'Cumulative deposits are 22/22 wei. Two wei remain on this escrow, two on revision 3, and four in the earlier revision-2 live takes.',
        'Browser-extension wallet approval popups were not exercised. Production still serves revision 2. No Portal submission.'])
p['implementationChecks']['releaseTestsPassed']=6
save(p)
count=sum(k.startswith('r4-') for k in p['transactions'])
report={'checkedAt':datetime.now(timezone.utc).isoformat(),'passed':False,'complete':False,'readOnly':True,'failures':p['blockers'],'executionFailures':[failure],'localChecks':p['implementationChecks'],'newWriteSummary':{'finalizedSuccessful':count-1,'finalizedRejected':1},'nativeBalanceRecord':'deploy/native-balance-proof.json','note':'The core Apple YES, Nintendo NO, no-evidence default and rejection proofs passed. The later matched ruling failed consensus. No complete release audit or publication was attempted.'}
(ROOT/'deploy/proof-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print('Stopped matched-consensus failure recorded; no retry, deposit or publication.')
