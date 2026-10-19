import json
from chain import ROOT,load,save,read
p=load()
for suffix in ('success','error'):
    checked=json.loads((ROOT/('deploy/wallet-adapter-'+suffix+'.json')).read_text(encoding='utf8'))
    if checked['status']!=checked['expectedState']:raise RuntimeError('Adapter transaction not final')
    label='wallet-adapter-'+suffix
    p['transactions'][label]=checked['hash']
    (ROOT/('deploy/receipts/'+label+'.json')).write_text(json.dumps(checked['receipt'],indent=2),encoding='utf8')
    if suffix=='error':p.setdefault('expectedFailures',{})[label]='ZERO_VALUE_UNAUTHORIZED_CALL'
    p.setdefault('walletAdapter',{})[suffix]={k:v for k,v in checked.items() if k!='receipt'}
p.setdefault('probes',{})['https://thewaltdisneycompany.com/']=read(p['probeContract'],'result',['https://thewaltdisneycompany.com/'])
save(p)
print('Imported real adapter success and error receipts, and Disney access probe',flush=True)
