"""Resumable fairness releases; immutable prior attempts and deposit approval retained."""
import hashlib,json,sys,time
from pathlib import Path
from datetime import datetime,timezone
from chain import ROOT,load,save,tx,read,signer,journal_lock

FILES={'Takes':'takes.py','TakeEscrow':'take_escrow.py','TakeResolver':'take_resolver.py','CalledItRecord':'called_it_record.py'}
ATTEMPT=4 if '--revision-4' in sys.argv else 3
PREFIX='r'+str(ATTEMPT)+'-'
def stamp(s):return int(datetime.fromisoformat(s.replace('Z','+00:00')).timestamp())
CASES=[
 {'label':'official-yes','text':'Apple officially announces Apple Vision Pro.','category':'tech','as_of':stamp('2023-06-03T00:00:00Z'),'deadline':stamp('2023-06-06T23:59:59Z'),'evidence':'https://web.archive.org/web/20230605190503id_/https://www.apple.com/newsroom/2023/06/introducing-apple-vision-pro/'},
 {'label':'rumours-no','text':'Nintendo officially reveals its next console under the retail name Nintendo Switch 2.','category':'tech','as_of':stamp('2025-01-01T00:00:00Z'),'deadline':stamp('2025-01-09T23:59:59Z'),'evidence':'https://en.wikipedia.org/w/index.php?title=Nintendo_Switch_2&oldid=1268215322'},
 {'label':'no-evidence-default','text':'Apple officially announces a foldable iPhone.','category':'tech','as_of':stamp('2025-01-01T00:00:00Z'),'deadline':stamp('2025-01-09T23:59:59Z')},
 {'label':'subjective-rejection','text':"Apple's next headset will be a flop.",'category':'tech','as_of':stamp('2025-01-01T00:00:00Z'),'deadline':stamp('2025-01-09T23:59:59Z')},
 {'label':'sources-unreachable','text':'The Recording Academy officially announces the nominations for the 67th GRAMMY Awards.','category':'entertainment','as_of':stamp('2024-11-01T00:00:00Z'),'deadline':stamp('2024-11-10T23:59:59Z'),'evidence':'https://web.archive.org/web/20241108004348id_/https://www.grammy.com/news/2025-grammys-nominations-full-winners-nominees-list'}
]
p=load()
def address(name):return p['contracts'][name]['address']
def write(label,name,method,args,index=0,value=0):return tx(p,PREFIX+label,address(name),method,args,index=index,value=value)
def record():
    entries=[]
    for key in read(address('Takes'),'get_ids',[0,100]):
        t=read(address('Takes'),'get_take',[key]);case=next(c for c in CASES if c['text']==t['text'])
        entries.append({'take':t,'bet':read(address('TakeEscrow'),'get_bet',[key]),'resolution':read(address('TakeResolver'),'get_resolution',[key]),'label':case['label']})
    p['takes']=entries;p['profiles']=[read(address('CalledItRecord'),'get_profile',[signer(i).address]) for i in range(2)]
    p['recordedAt']=datetime.now(timezone.utc).isoformat();save(p)
    return {e['label']:e for e in entries}
def entries():
    at=p.get('recordedAt')
    if p.get('takes') and at and (datetime.now(timezone.utc)-datetime.fromisoformat(at)).total_seconds()<30:return {e['label']:e for e in p['takes']}
    return record()

def initialize():
    if p.get('releaseAttempt')==ATTEMPT:return
    previous_attempt=p.get('releaseAttempt',2)
    if previous_attempt!=ATTEMPT-1:raise RuntimeError('Initialize only the next consecutive release')
    folder=ROOT/'deploy/releases';folder.mkdir(exist_ok=True)
    archived=folder/('v'+str(previous_attempt)+'-proof.json')
    if archived.exists():raise RuntimeError('Existing archived release; reconcile before initialization')
    archived.write_text(json.dumps(p,indent=2)+'\n',encoding='utf8')
    for name in ('proof-verification.json','production-verification.json'):
        source=ROOT/'deploy'/name
        if source.exists():(folder/('v'+str(previous_attempt)+'-'+name)).write_bytes(source.read_bytes())
    previous={'contracts':p['contracts'],'attempt':previous_attempt,'proof':str(archived.relative_to(ROOT)).replace('\\','/'),'reason':'Immutable earlier release retained; new release uses fresh contracts.'}
    p.setdefault('previousReleases',[]).append(previous)
    if not p.get('legacyLiveTakes'):p['legacyLiveTakes']=[{'take':e['take'],'bet':e['bet'],'contracts':p['contracts']} for e in p['takes'] if e['bet'].get('status')=='OPEN' and not e['take']['historical']]
    for e in p['takes']:
        if e['bet'].get('status')=='MATCHED':p.setdefault('previousUnsettledBets',[]).append({'attempt':previous_attempt,'contracts':p['contracts'],'entry':e})
    for failure in p.get('failedResolutionAttempts',[]):p.setdefault('expectedFailures',{})[failure['label']]='CONSENSUS_DISAGREEMENT'
    p.update(releaseAttempt=ATTEMPT,deploymentPrefix=PREFIX,contracts={},takes=[],profiles=[],releaseStatus='IN_PROGRESS',blockers=['Revision '+str(ATTEMPT)+' deployment and live proof in progress.'])
    for key in ('refundDemo','walletAdapter','resolutionAttempts','verification','implementationChecks','authorizedRecovery','failedResolutionAttempts','stopFailure','unreachableProof','localRepair','recordedAt'):p.pop(key,None)
    p['fairnessPolicy']={'default':'DEFAULT_NO_EVIDENCE only','technicalFailure':'VOID_SOURCES_UNREACHABLE or VOID_TIMEOUT; full original deposits refunded','blockedHosts':['reuters.com','apnews.com','oscars.org'],'failedPreflight':'Owner approved an unlisted source; immutable metadata must verify; actual resolution fetch failure required.','remainingApprovedWeiAtStart':20-sum(p.get('deposits',{}).values()),'oldLiveTakes':'Remain funded on revision 2; no migration.'}
    import subprocess
    p['sourceCommit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    # save() preserves concurrent journals and the original cumulative deposits.
    with journal_lock('proof'):
        target=ROOT/'deploy/proof.json';tmp=target.with_suffix('.tmp');tmp.write_text(json.dumps(p,indent=2)+'\n',encoding='utf8');tmp.replace(target)
    (ROOT/'deploy/proof-verification.json').write_text(json.dumps({'passed':False,'failures':['New fairness release not yet audited.']}),encoding='utf8')

stage=sys.argv[1] if len(sys.argv)>1 else 'record'
if stage=='init':initialize()
elif stage=='deploy':
    if p.get('releaseAttempt')!=ATTEMPT:raise RuntimeError('Initialize the selected revision first')
    for name,file in FILES.items():
        code=(ROOT/'contracts'/file).read_text(encoding='utf8');digest=hashlib.sha256(code.encode()).hexdigest()
        if name in p['contracts']:
            if p['contracts'][name]['sha256']!=digest:raise RuntimeError('Immutable source changed after deployment')
            continue
        receipt=tx(p,PREFIX+'deploy-'+name,code=code,args=[] if name=='Takes' else [address('Takes')])
        p['contracts'][name]={'address':receipt.get('recipient',receipt.get('to_address')),'source':file,'sha256':digest};save(p)
    write('configure','Takes','configure',[address('TakeResolver'),address('TakeEscrow'),address('CalledItRecord')])
    config=read(address('Takes'),'get_config')
    assert all(config[k].lower()==address(n).lower() for k,n in [('resolver','TakeResolver'),('escrow','TakeEscrow'),('record','CalledItRecord')])
elif stage=='compile':
    for case in CASES:
        write('compile-'+case['label'],'Takes','compile',[case['text'],case['category'],case['deadline'],1,1,'NO',case['as_of']])
        t=read(address('Takes'),'get_take',['take-'+str(CASES.index(case)+1)])
        assert t['status']==('REJECTED' if case['label']=='subjective-rejection' else 'COMPILED'), 'Unexpected compiler result; STOP'
    record()
elif stage=='fund':
    e=entries()['sources-unreachable'];key=e['take']['id']
    write('prepare-'+key,'TakeEscrow','prepare_open',[key]);write('deposit-author-'+key,'TakeEscrow','deposit',[key],value=1)
    write('accept-'+key,'TakeEscrow','prepare_accept',[key],index=1);write('deposit-counter-'+key,'TakeEscrow','deposit',[key],index=1,value=1)
    b=read(address('TakeEscrow'),'get_bet',[key]);assert b['status']=='MATCHED' and b['total']=='2'
    record()
elif stage=='evidence':
    items=entries()
    for case in CASES:
        if case.get('evidence'):write('evidence-'+items[case['label']]['take']['id'],'TakeResolver','submit_evidence',[items[case['label']]['take']['id'],case['evidence'],'Apply the frozen rule. Treat source access failure as technical VOID, never as a default-side win.'])
    record()
elif stage=='recover-apple':
    assert ATTEMPT==3 and p.get('releaseAttempt')==3, 'Recovery stage is only for the archived revision-3 attempt'
    # One recovery expressly authorized by the owner's "proceed" after the
    # finalized failure. This is not a polling retry or an automatic retry loop.
    from chain import success
    failed=ROOT/'deploy/receipts/r3-resolve-take-1.json'
    receipt=json.loads(failed.read_text())
    assert receipt.get('status')=='FINALIZED' and not success(receipt)
    key='take-1'
    r=read(address('TakeResolver'),'get_resolution',[key])
    if r.get('status')!='FINAL':
        assert r.get('status')=='OPEN', 'Recovery requires unchanged OPEN state'
        p['authorizedRecovery']={'failedHash':p['transactions']['r3-resolve-take-1'],'reason':'Owner said proceed after the quote-guard failure; one new zero-value attempt on unchanged rule and evidence.','label':'r3-resolve-take-1-owner-recovery-1','quoteGuardChanged':False}
        save(p)
        write('resolve-take-1-owner-recovery-1','TakeResolver','resolve',[key])
        r=read(address('TakeResolver'),'get_resolution',[key])
    assert r.get('status')=='FINAL' and r.get('verdict')=='YES', 'Unexpected Apple recovery result; STOP'
    record()
elif stage=='resolve':
    items=entries()
    for label,e in items.items():
        if e['take']['status']!='COMPILED':continue
        if '--core-only' in sys.argv and label=='sources-unreachable':continue
        if e['resolution'].get('status')=='FINAL':
            if label in ('official-yes','rumours-no'):assert e['resolution']['verdict']==('YES' if label=='official-yes' else 'NO')
            continue
        key=e['take']['id']
        write('seal-author-'+key,'TakeResolver','seal_evidence',[key])
        if e['bet'].get('counterparty'):write('seal-counter-'+key,'TakeResolver','seal_evidence',[key],index=1)
        write('resolve-'+key,'TakeResolver','resolve',[key])
        r=read(address('TakeResolver'),'get_resolution',[key]);assert r['status']=='FINAL'
        if label in ('official-yes','rumours-no'):assert r['verdict']==('YES' if label=='official-yes' else 'NO'), 'Unexpected ruling; STOP'
        if label=='no-evidence-default':assert r['resolution_case']=='DEFAULT_NO_EVIDENCE'
        if label=='sources-unreachable':
            preflights=[v.get('preflight',{}) for v in r.get('evidence',[])]
            blocked=any(v.get('status')=='UNAVAILABLE' and 'HTTP ' in v.get('error','') for v in preflights)
            p['unreachableProof']={'proven':r['resolution_case']=='VOID_SOURCES_UNREACHABLE' and blocked,'actualCase':r['resolution_case'],'take':key,'preflights':preflights,'note':'Actual validators decide; no fetch status was mocked or forced. A blocked-host proof also requires a recorded failed HTTP preflight.'};save(p)
    record()
elif stage=='settle':
    items=entries()
    for e in items.values():
        key=e['take']['id'];b=e['bet'];r=e['resolution']
        if not b or r.get('status')!='FINAL':continue
        write('settle-'+key,'TakeEscrow','settle',[key])
        b=read(address('TakeEscrow'),'get_bet',[key]);assert b['status']=='SETTLED'
        for i in range(2):
            wallet=signer(i).address.lower()
            if not int(b.get('payouts',{}).get(wallet,0)):continue
            receipt=write('claim-'+key+'-'+str(i),'TakeEscrow','claim',[key,1],index=i)
            children=receipt.get('triggered_transactions') or [];assert len(children)==1
            write('verify-'+key+'-'+str(i),'TakeEscrow','verify_claim',[key,wallet,1,p['transactions'][PREFIX+'claim-'+key+'-'+str(i)],children[0]],index=i)
        write('record-'+key,'CalledItRecord','sync',[key])
    record()
elif stage=='record':record()
else:raise SystemExit('Stages: init deploy compile fund evidence recover-apple resolve settle record')
