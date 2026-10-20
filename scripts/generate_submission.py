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
lines+=['','## All transaction receipts','']
for name,url in links.get('transactions',{}).items():lines.append(f'- [{name}]({url})')
lines+=['','## Blockers','']+[('- '+b) for b in p.get('blockers',[])]
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
if p.get('releaseAttempt',0)>=3 and not p.get('unreachableProof',{}).get('proven'):
 portal['description']+=' Real blocked-source VOID is unproven in this run.'
if p.get('releaseStatus','').startswith('STOPPED'):
 portal['description']+=' Live proof stopped on model-output errors.'
if p.get('releaseStatus','').startswith('AWAITING_DEPOSIT'):
 portal['description']+=' Matched settlement awaits deposit approval.'
assert len(portal['oneLiner'])<=180 and len(portal['description'])<=1000 and len(portal['expectedOutcome'])<=500
(ROOT/'docs/submission/portal-fields.json').write_text(json.dumps(portal,indent=2)+'\n',encoding='utf8')
print('Generated release report and Portal draft from recorded proof; no Portal submission made.')
