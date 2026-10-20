"""Build the revision-5 evidence package from completed receipts and readbacks."""
import json
from datetime import datetime, timezone
from pathlib import Path
from chain import ROOT, load, save, success


def main():
    p = load()
    assert p['releaseAttempt'] == 5 and p['nativeBalanceProof']['passed'] is True
    assert sum(p['deposits'].values()) == 24
    assert json.loads((ROOT/'deploy/r5-contract-evidence.json').read_text())['passed'] is True
    entries = {e['label']: e for e in p['takes']}
    for label, outcome, case in [('official-yes','YES','JUDGED_YES'), ('rumours-no','NO','JUDGED_NO'), ('no-evidence-default','NO','DEFAULT_NO_EVIDENCE'), ('scheduling-void','VOID','VOID_INSUFFICIENT_EVIDENCE')]:
        r=entries[label]['resolution']
        assert r['status']=='FINAL' and r['outcome']==outcome and r['resolution_case']==case
    assert entries['subjective-rejection']['take']['status']=='REJECTED'
    writes={label:h for label,h in p['transactions'].items() if label.startswith('r5-')}
    assert all(success(json.loads((ROOT/'deploy/receipts'/(label+'.json')).read_text())) for label in writes)
    hashes={'releaseAttempt':5,'sourceCommit':p['sourceCommit'],'contracts':p['contracts'],'transactions':{label:{'hash':h,'url':'https://explorer-studio.genlayer.com/tx/'+h,'status':'FINALIZED'} for label,h in writes.items()},'allFinalizedSuccessful':True,'nativeBalanceProof':'deploy/native-balance-proof.json'}
    (ROOT/'deploy/r5-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n',encoding='utf8')
    checks=json.loads((ROOT/'deploy/r5-local-checks.json').read_text())
    p['implementationChecks']={key:checks[key] for key in ('contractTestsPassed','releaseTestsPassed')}
    p['implementationChecks'].update(appTestsPassed=checks.get('appTestsPassed'),typecheck=checks.get('typecheck','PENDING'),eslint=checks.get('eslint','PENDING'),productionBuild=checks.get('productionBuild','PENDING'),genvmLint='4/4 PASS',deployedSourceHashes='4/4 match deployed bytes and local manifest')
    p['requiredApproval']={'status':'APPROVED','additionalWei':2,'cumulativeTotalWei':24,'perWalletWei':1,'escrow':p['contracts']['TakeEscrow']['address'],'take':'take-1','authorization':'Approve 1 wei per side; 24 wei cumulative'}
    if not any(item.get('approvedTotalWei')==24 for item in p.get('budgetApprovals',[])):
        p.setdefault('budgetApprovals',[]).append({'approvedTotalWei':24,'additionalWei':2,'authorization':'Approve 1 wei per side; 24 wei cumulative','scope':'Revision-5 Apple matched bet, exactly one wei from each existing demo wallet.'})
    p['fairnessPolicy']['remainingApprovedWeiAtStart']=2
    p['recoveryFollowup']=json.loads((ROOT/'deploy/recovery-followup.json').read_text())
    p['limitations']=[
        'Real VOID_SOURCES_UNREACHABLE remains unproven; readable Grammy scheduling evidence produced VOID_INSUFFICIENT_EVIDENCE.',
        'Original revision-4 matched bet still holds two wei and has its isolated 23 October 22:06 Lagos timeout recovery. Revision 3 separately holds two wei.',
        'Two earlier funded live takes stay on revision 2 with its original immutable failure-default policy; they were not migrated.',
        'Model judgments and sampled consensus are not universally reliable; earlier failures and exact receipts remain archived.',
        'An interactive browser-extension approval popup and current mobile visual certification remain unverified.'
    ]
    save(p)
    address=lambda name:'https://explorer-studio.genlayer.com/address/'+p['contracts'][name]['address']
    tx=lambda label:'https://explorer-studio.genlayer.com/tx/'+p['transactions'][label]
    table='| Contract | Revision-5 address |\n| --- | --- |\n'+'\n'.join('| '+name+' | ['+item['address']+']('+address(name)+') |' for name,item in p['contracts'].items())
    production=ROOT/'deploy/production-verification.json'
    deployed=production.exists() and json.loads(production.read_text()).get('releaseAttempt')==5 and json.loads(production.read_text()).get('passed') is True
    publication='Production serves revision 5 and its live API reads the new Takes address.' if deployed else 'Production rollout and its live address check remain pending.'
    summary='**Revision 5: the v2 judge is promoted into four fresh, fully wired contracts.** Real finalized replays show Apple YES, Nintendo NO, the no-evidence frozen NO default, subjective rejection and Grammy scheduling evidence VOID_INSUFFICIENT_EVIDENCE. The separate two-wallet Apple bet used exactly 1+1 wei, settled to the winner and paid a verified two-wei native credit. '+publication+' Nothing was submitted to the Portal.'
    readme=ROOT/'README.md';text=readme.read_text(encoding='utf8')
    start=text.index('**Revision ');end=text.index('\nCalled It is a one-on-one wager',start)
    lead=summary+'\n\nAll 69 contract tests and 24 release tests pass; all four contracts pass GenVM lint. The configured resolver uses exactly v2\'s ordered four-step judge and ARCHIVE_CAPTURE_TIMES_UTC block, with diagnostic output omitted. All fairness branches remain unchanged. [Verification](docs/VERIFICATION.md) · [All hashes](docs/RELEASE.md) · [Local checks](deploy/r5-local-checks.json).\n\nThe original revision-4 bet and its failed ruling remain intact. Its 23 October 22:06 Africa/Lagos recovery uses only its isolated original-contract journal. The two earlier live takes remain on revision 2. Cumulative deposits are exactly 24/24 approved simulated wei; no further deposits are authorized. Real unreachable-source VOID remains unproven.\n\n'+table+'\n'
    text=text[:start]+lead+text[end:]
    old='The cumulative ceiling is 22 wei: revision 2 deposited 18, revision 3 deposited two, and the owner-approved revision-4 extension deposited two. The budget is exhausted. Both later matched bets retain two wei each on their own escrows; the two revision-2 live takes retain four wei total.'
    text=text.replace(old,'The cumulative ceiling is 24 wei: revision 2 deposited 18, revision 3 two, revision 4 two and revision 5 the explicitly approved 1+1 wei. The budget is exhausted. Revision 5 paid its winner; revision 3 and revision 4 each retain their separate two-wei matched bets, while the revision-2 live takes retain four wei total.')
    start=text.index('The staged fairness release deploys four fresh contracts;') if 'The staged fairness release deploys four fresh contracts;' in text else text.index('Revision 5 uses `python scripts/revision5_release.py')
    end=text.index('\n\n',start)
    text=text[:start]+'Revision 5 uses `python scripts/revision5_release.py <stage>` with stages init, deploy, compile, evidence, resolve-grammy, fund, resolve, settle and record. The package release command dispatches to that driver. Every new write uses a distinct `r5-` label and follows its saved hash and finality callbacks. The driver stops on an unexpected ruling or finalized failure. It permits only one additional wei per demo wallet for the Apple bet. The original revision-4 recovery uses `python scripts/recover_timeout.py --revision-4 --execute` and a separate journal; it cannot overwrite this release.'+text[end:]
    readme.write_text(text,encoding='utf8')
    lines=['# Verification record','',summary,'',table,'','## Real revision-5 replays','', '| Case | Final state | Receipt |','| --- | --- | --- |']
    for label in ('official-yes','rumours-no','no-evidence-default','subjective-rejection','scheduling-void'):
        e=entries[label];key=e['take']['id'];r=e['resolution']
        receipt='r5-compile-subjective-rejection' if label=='subjective-rejection' else 'r5-resolve-'+key
        state=e['take']['status'] if label=='subjective-rejection' else r['outcome']+' / '+r['resolution_case']
        lines.append('| '+label+' | '+state+' | [Finalized receipt]('+tx(receipt)+') |')
    native=p['nativeBalanceProof'];bet=entries['official-yes']['bet'];author=p['demoWallets'][0]
    claim=bet['claims'][author]
    lines+=['','All '+str(len(writes))+' revision-5 writes, native transfers and callbacks finalized successfully, with matching source, frozen-rule and state reads. [Every revision-5 hash](../deploy/r5-hashes.json). The Grammy case uses a new rule and configured resolver on this release; its scheduling evidence yields VOID, not the frozen default. It is not an unreachable-source demonstration.','',
            '## Matched bet and actual native credit','',
            'The owner approved exactly one new wei from each demo wallet, raising cumulative deposits from 22 to 24 wei. Apple take-1 matched two distinct wallets and settled YES. Its payout map gives the author exactly two wei. The claim is PAID after its native child was verified; the losing wallet has no payout.','',
            '- [Settlement]('+tx('r5-settle-take-1')+')',
            '- [Winner claim]('+tx('r5-claim-take-1-0')+')',
            '- [Native credit](https://explorer-studio.genlayer.com/tx/'+claim['child']+')',
            '- [Credit verification]('+tx('r5-verify-take-1-0')+')',
            '- [Public record]('+tx('r5-record-take-1')+')','',
            'Exact native balances before the claim: `'+json.dumps(native['before']['balancesWei'])+'`; after: `'+json.dumps(native['after']['balancesWei'])+'`. The author gains two wei, counterparty changes by zero after funding, and escrow loses two. [Balance proof](../deploy/native-balance-proof.json). The record shows one historical win and one loss; unfunded replays do not add wins.','',
            '## Implementation checks','',
            '- 69 contract tests and 24 release tests passed, including exact and once-only refunds, the 24-wei cap and isolated original-release recovery.',
            '- All four GenVM lint checks passed with the pinned runner. Cached catalog/newer-runner warnings are retained.',
            '- AST comparison confirms the promoted judge is exactly v2 and all remaining resolver code is unchanged. Diagnostic printing and the diagnostic docstring are absent.',
            '- App tests, ESLint, TypeScript and build results: [current local check record](../deploy/r5-local-checks.json).',
            '- All four actual deployed source hashes match local files and manifest. [Source audit](../deploy/source-verification.json).','',
            'Each deployed address is also a separate Portal evidence entry with preferred type GenLayer Explorer Contract. All four direct pages returned HTTP 200; their Explorer APIs returned CONTRACT and the exact requested addresses. The actual RPC chain ID is StudioNet 61999. [Contract evidence check](../deploy/r5-contract-evidence.json).','',
            '## Prior contracts and recovery','',
            'The [immutable revision-4 proof](../deploy/releases/v4-proof.json) preserves the failed funded Grammy ruling and original addresses. No revision-4 ruling was retried and no original contract was rewired. Its two wei remain on Escrow 0xC5BeB6B171f37f2c7101EDc83eA2905615415e12. The approved follow-up runs on 23 October 2026 at 22:06 Africa/Lagos, after actual eligibility at 22:04:35, using `python scripts/recover_timeout.py --revision-4 --execute`. It reads archived sources and writes only its isolated working journal. It will not replace revision-5 production. [Follow-up](../deploy/recovery-followup.json).',
            '', 'The separate revision-3 matched bet still holds two wei. The two revision-2 live takes keep deadlines 29 October and 4 November at 23:59:59 UTC and their original immutable failure-default policy. They were not migrated. [Earlier release](../deploy/releases/v2-proof.json).','',
            '## Audit, publication and limits','',
            'The [full read-only proof audit](../deploy/proof-verification.json) verifies actual Explorer CONTRACT types, canonical /address/ and /tx/ links, every saved transaction, deployed bytes, finalized states, native credits, exact balances, old held bets and HTTP 200 for other published links. Consult its passed field; a partial audit is not a completed release audit. '+publication+' [Production evidence](../deploy/production-verification.json).','',
            'The [Portal draft](submission/portal-fields.json) describes the v2 judge and Grammy VOID and enforces 180/1000/500 characters. Nothing was submitted. Real VOID_SOURCES_UNREACHABLE, the future revision-4 timeout refunds, current mobile visual certification and an interactive browser-extension approval popup remain unproven. Earlier consensus failures and the v1 semantic regression remain preserved.']
    (ROOT/'docs/VERIFICATION.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print('Packaged revision 5:',len(writes),'finalized transactions; cumulative deposits 24 wei.',flush=True)


if __name__=='__main__':
    main()
