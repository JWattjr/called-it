"""Local checkpoint after core live proofs; never creates deposit authorization."""
import json
from datetime import datetime,timezone
from chain import ROOT,load,save,success

p=load();assert p['releaseAttempt']==4
entries={e['label']:e for e in p['takes']}
assert entries['official-yes']['resolution']['status']=='FINAL' and entries['official-yes']['resolution']['outcome']=='YES'
assert entries['rumours-no']['resolution']['status']=='FINAL' and entries['rumours-no']['resolution']['outcome']=='NO'
assert entries['no-evidence-default']['resolution']['resolution_case']=='DEFAULT_NO_EVIDENCE'
assert entries['subjective-rejection']['take']['status']=='REJECTED'
assert not entries['sources-unreachable']['bet'] and entries['sources-unreachable']['resolution']['status']=='OPEN'
assert sum(p['deposits'].values())==20
for label in p['transactions']:
    if label.startswith('r4-'):assert success(json.loads((ROOT/'deploy/receipts'/(label+'.json')).read_text()))
p.update(releaseStatus='AWAITING_DEPOSIT_APPROVAL',approvedDepositBudgetWei=20,
    requiredApproval={'status':'PENDING','additionalWei':2,'cumulativeTotalWei':22,'escrow':p['contracts']['TakeEscrow']['address'],'take':'take-5','purpose':'One wei from each existing demo wallet for the repaired deployment matched-bet, settlement and verified native-credit proof. Simulated StudioNet GEN only.'},
    blockers=['Owner decision pending: two additional wei would raise the cumulative deposit ceiling from 20 to 22. No new deposit has been made.',
        'New matched-bet settlement, verified native claims and record remain unproven pending the deposit decision.',
        'Real VOID_SOURCES_UNREACHABLE remains unproven: the unlisted article preflight was FETCHED; no failure was manufactured.',
        'Full publication link audit, production deployment and final push remain pending.'],
    implementationChecks={'contractTestsPassed':69,'releaseTestsPassed':5,'appTestsPassed':7,'typecheck':'PASS','eslint':'PASS','productionBuild':'PASS','genvmLint':'All four deployed contracts PASS','deployedSourceHashes':'4/4 match local bytes and manifest'},
    limitations=['External models and sources can still fail; the bounded correction does not guarantee availability. Both revision-3 failures are archived.',
        'Mocked 401/403 and timeout refunds do not constitute real network proof of those cases.',
        'The two earlier live takes remain on revision 2. The earlier revision-3 matched bet still holds two wei on its own escrow.',
        'The browser live-read flow is verified; interactive extension-wallet approval popups have not been exercised in this release.',
        'Production still serves revision 2; the repaired release is not yet published. No Portal submission.'],
    unreachableProof={'proven':False,'actualCase':'AWAITING_MATCHED_BET_AND_RESOLUTION','take':'take-5','preflights':[e['preflight'] for e in entries['sources-unreachable']['resolution']['evidence']],'note':'The real unlisted article fetched successfully. Only actual failure of all resolution fetches can prove the technical VOID case.'})
save(p)
checks=[{'check':'Real '+label,'passed':True} for label in ('Apple YES','Nintendo NO','DEFAULT_NO_EVIDENCE','subjective rejection')]
report={'checkedAt':datetime.now(timezone.utc).isoformat(),'passed':False,'complete':False,'readOnly':True,'checks':checks,'failures':[],'unproven':p['blockers'],'localChecks':p['implementationChecks'],'sourceAudit':'deploy/source-verification.json','contractApiAudit':'deploy/contract-link-audit.json','partialLinkAudit':'deploy/fairness-link-audit.json','note':'Core live proofs passed. This is a checkpoint, not a complete release audit. Owner approval has not been inferred or created.'}
(ROOT/'deploy/proof-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print('Core live proofs passed; checkpoint saved. Additional deposits remain unauthorized.')
