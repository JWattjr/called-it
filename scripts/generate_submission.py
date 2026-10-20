"""Generate documentation and a Portal draft from real recorded proof; never submit."""
import json
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
p=json.loads((ROOT/'deploy/proof.json').read_text(encoding='utf8'))
links=json.loads((ROOT/'deploy/links.json').read_text(encoding='utf8'))
lines=['# Called It release evidence','',f"Recorded: {p.get('recordedAt','not yet recorded')}",f"Status: {p.get('releaseStatus','IN_PROGRESS')}",'',f"App: {p.get('website','Deployment pending')}",f"Repository: {p.get('github','Publication pending')}",f"Source commit: `{p.get('sourceCommit','not recorded')}`",'','## Contracts','']
for name,url in links.get('contracts',{}).items():lines.append(f'- [{name}]({url})')
lines+=['','## Takes and outcomes','']
for e in p.get('takes',[]):
    t=e['take'];r=e['resolution'];b=e['bet']
    lines.extend([f"### {t['id']} — {e.get('label','')}",'',t['text'],'',f"{'Historical replay' if t['historical'] else 'Live'} · {t['status']} · verdict {r.get('verdict') or 'pending'} · outcome {r.get('outcome') or 'pending'} · escrow {b.get('status','unfunded')}",''])
    lines.append('Event deadline: '+datetime.fromtimestamp(t['rule']['deadline'],timezone.utc).isoformat())
    if r.get('resolution_case'):lines.append('Resolution case: '+r['resolution_case'])
    if r.get('reason'):lines.append('Ruling: '+r['reason'])
    if t['status']=='REJECTED':lines.append('Compiler decision: '+t['decision']+' — '+t['reason'])
    if b.get('claims'):lines.append('Native claims: '+json.dumps(b['claims'],ensure_ascii=False))
    lines.append('')
    for evidence in r.get('evidence',[]):lines.append(f"- [Immutable evidence]({evidence['url']})")
    for name,url in links.get('transactions',{}).items():
        if t['id'] in name or e.get('label','__none__') in name:lines.append(f'- [{name}]({url})')
if p.get('legacyLiveTakes'):
    lines+=['','## Pending live takes remain on the previous deployment','', 'These funded takes retain the earlier immutable default policy. They were not migrated or reopened. See [the archived release](../deploy/releases/v2-proof.json).','']
    for e in p['legacyLiveTakes']:
        t=e['take'];lines.append('- '+t['text']+' Deadline: '+datetime.fromtimestamp(t['rule']['deadline'],timezone.utc).isoformat()+'. Earlier Takes contract: '+e['contracts']['Takes']['address'])
if p.get('previousUnsettledBets'):
    lines+=['','## Earlier matched bets remain on their original escrow','']
    for e in p['previousUnsettledBets']:
        b=e['entry']['bet']
        lines.append('- Revision '+str(e['attempt'])+' '+b['id']+': '+b['status']+', '+b['total']+' wei held. Escrow '+e['contracts']['TakeEscrow']['address']+'. Refund deadline '+datetime.fromtimestamp(b['refund_deadline'],timezone.utc).isoformat()+'. The new deployment did not migrate or pay this bet.')
if p.get('unreachableProof'):lines+=['','## Honest unreachable-source proof status','',json.dumps(p['unreachableProof'],ensure_ascii=False),'']
if p.get('consensusDiagnostics'):
    diagnostic=p['consensusDiagnostics']
    lines+=['','## Isolated unfunded diagnostic candidate','',
            'Status: '+diagnostic['status']+'. This candidate is not configured as the escrow resolver and cannot settle the original bet.','']
    for name,url in links.get('diagnosticContracts',{}).items():lines.append(f'- [{name}]({url})')
    for key,case in diagnostic.get('cases',{}).items():
        result=case['resolution']
        lines.append('- '+key+': expected '+case['expectedOutcome']+', actual '+result['outcome']+' / '+result['resolution_case']+'; regression '+('PASS' if case['passed'] else 'FAIL')+'.')
    lines+=['','See [consensus diagnosis](CONSENSUS-DIAGNOSIS.md) and [the diagnostic report](../deploy/consensus-diagnostics.json).']
if p.get('previousConsensusDiagnostics'):
    lines+=['','## Earlier diagnostic candidates','']
    for previous in p['previousConsensusDiagnostics']:
        version=previous.get('version',1)
        lines.append('- Version '+str(version)+': '+previous['status']+'. Its original source, rulings and failure remain in [the archived diagnostic](../deploy/consensus-diagnostics-v'+str(version)+'.json).')
if p.get('recoveryFollowup'):
    lines+=['','## Approved timeout follow-up','',
            'The original revision-4 bet has a separate one-time recovery scheduled for 23 October 2026 at 22:06 Africa/Lagos, after actual timeout eligibility at 22:04:35. It uses its isolated revision-4 journal and original contracts, independently of the current release. No additional deposits or Portal submission. See [recovery status](../deploy/timeout-recovery.json).']
if p.get('releaseAttempt')==5:
    lines+=['','## Revision-5 configured judge and matched proof','',
            'The configured resolver adopts exactly v2\'s ordered four-step decision prompt and ARCHIVE_CAPTURE_TIMES_UTC block, without diagnostic output. All fairness branches remain unchanged. The real Grammy scheduling replay resolves VOID_INSUFFICIENT_EVIDENCE. Apple is the separate approved 1+1 wei matched bet; inspect finalized settlement, native-credit verification and the public record in the proof.','',
            'Owner approved exactly one additional wei per wallet, raising cumulative deposits from 22 to 24 wei. The revision-4 archive, original held stakes and scheduled recovery are separate. See [verification](VERIFICATION.md) and [the immutable revision-4 archive](../deploy/releases/v4-proof.json).']
lines+=['','## All transaction receipts','']
for name,url in links.get('transactions',{}).items():lines.append(f'- [{name}]({url})')
if p.get('blockers'):lines+=['','## Blockers','']+[('- '+b) for b in p['blockers']]
(ROOT/'docs/RELEASE.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
portal={
 'contributionType':'Projects','projectName':'Called It','primaryTag':'Gaming','tag1':'Outcome Verification','tag2':'Prediction Markets',
 'oneLiner':'Put GEN on your hot take. GenLayer validators decide who called it.',
 'description':'Called It turns a public hot take into a head-to-head bet. GenLayer validators compile one claim into a frozen, hashed official-announcement rule before staking, then independently judge immutable archive or Wikipedia evidence. Consensus checks both the verdict and every decisive quote against each validator’s fetched copy. Four contracts separate compilation, escrow, resolution and public records. Code owns odds, deposits, deadlines and verified pull payouts. Only absent evidence applies the default; source failure or consensus timeout voids and refunds both stakes. The app exposes rules, evidence, quotes, finalized receipts and a public called-it record without requiring a wallet. Historical replays are clearly labelled. StudioNet uses simulated GEN. Two earlier live takes stay on their original contracts. See the release report for verified live outcomes and remaining limitations.',
 'howTo':[
  {'heading':'Inspect a take','instruction':'Open the feed without a wallet. Read the frozen rule, hash, deadline and default. Historical replays are labelled; Read live queries finalized state.'},
  {'heading':'Compile before staking','instruction':'Connect a StudioNet wallet, post one public claim and review its finalized rule or rejection. Prepare and fund the author stake only after reading the complete rule.'},
  {'heading':'Take the other side','instruction':'Use a different wallet to reserve the counterparty slot. Review the ratio, exact matching stake and potential payout, then deposit before the reservation expires.'},
  {'heading':'Resolve from receipts','instruction':'After the deadline, preview permanent sources and review the stored FETCHED or UNAVAILABLE preflight before sealing. Known-blocked hosts are rejected; failed sources never pay the default side. Then request one narrow ruling.'},
  {'heading':'Settle and verify','instruction':'Settle a finalized result, pull the payout, verify its native child receipt and sync the public record. Review all receipts and run npm run verify:proof.'}
 ],
 'expectedOutcome':'An accepted compilation freezes a precise rule before stakes. Absent evidence applies the default; source failure or consensus timeout refunds both sides. A judged bet resolves YES or NO; settlement conserves wei and the winner pulls a receipt-verified payout. Unaccepted and timed-out takes expose refunds. Only finalized matched settlements update profiles. The read-only proof verifier checks deployed code, actual outcomes, payouts and canonical explorer records.',
 'contractLinks':list(links.get('contracts',{}).values()),'website':p.get('website',''),'github':p.get('github',''),'demoVideo':'',
 'evidence':[p['github']+'/blob/main/'+path for path in ('deploy/proof.json','deploy/proof-verification.json','docs/VERIFICATION.md','docs/RELEASE.md','docs/TUTORIAL.md')] if p.get('github') else []
}
portal['evidence']=list(links.get('contracts',{}).values())+portal['evidence']
portal['evidenceEntries']=[{'label':name,'preferredEvidenceType':'GenLayer Explorer Contract','network':p.get('network'),'chainId':p.get('chainId'),'url':url} for name,url in links.get('contracts',{}).items()]
if p.get('releaseAttempt')==5:
 portal['description']='Called It turns a public hot take into a head-to-head bet settled by GenLayer validators. Compilation freezes a hashed rule before staking. The revision-5 v2 judge uses an ordered four-step decision and explicit archive capture times; validators independently judge evidence and verify every decisive quote. Real replays show Apple YES, Nintendo NO, the frozen default only for absent evidence, subjective rejection, and Grammy scheduling evidence VOID. Four newly wired contracts separate compilation, escrow, resolution and public records. A two-wallet 1+1 wei Apple bet settles to its winner, who pulls a verified native payout. Source failure or consensus timeout refunds both stakes. StudioNet GEN is simulated. The two earlier live takes and revision-4 timeout recovery remain on their original contracts. Real unreachable-source VOID remains unproven. The app exposes rules, evidence, rulings and finalized receipts without requiring a wallet.'
if p.get('releaseAttempt',0)>=3 and p.get('releaseAttempt')!=5 and not p.get('unreachableProof',{}).get('proven'):
 portal['description']+=' Real blocked-source VOID is unproven in this run.'
if p.get('releaseStatus','').startswith('STOPPED'):
 portal['description']+=(' Matched proof stopped on consensus disagreement.' if p.get('releaseStatus')=='STOPPED_CONSENSUS_DISAGREEMENT' else ' Candidate failed its Nintendo regression.' if p.get('releaseStatus')=='STOPPED_DIAGNOSTIC_REGRESSION' else ' Live proof stopped on model-output errors.')
if p.get('releaseStatus','').startswith('AWAITING_DEPOSIT'):
 portal['description']+=' Matched settlement awaits deposit approval.'
if p.get('releaseStatus')=='AWAITING_TIMEOUT_RECOVERY':
 portal['description']+=' Original matched ruling failed; refund pending.'
assert len(portal['oneLiner'])<=180 and len(portal['description'])<=1000 and len(portal['expectedOutcome'])<=500
(ROOT/'docs/submission/portal-fields.json').write_text(json.dumps(portal,indent=2)+'\n',encoding='utf8')
print('Generated release report and Portal draft from recorded proof; no Portal submission made.')
