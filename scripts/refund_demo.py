"""Approved two-wei live test: invalid deposit credit + failed payable recovery."""
import json
from chain import ROOT,load,save,tx,read,signer,success

p=load();address=p['contracts']['TakeEscrow']['address'];wallet=signer().address.lower()
tx(p,'refund-invalid-amount',address,'deposit',['unknown-demo-take'],value=1)
label='refund-runtime-failure'
p.setdefault('expectedFailures',{})[label]='FAILED_PAYABLE'
save(p)
try:
    tx(p,label,address,'deposit',[],value=1)
except RuntimeError as error:
    if 'Finalized execution error:' not in str(error):raise
r=json.loads((ROOT/'deploy/receipts'/(label+'.json')).read_text(encoding='utf8'))
if success(r) or r.get('value_credited') is not True:raise RuntimeError('Expected a real finalized failed payable with native credit; inspect retained receipt')
tx(p,'refund-recover-failure',address,'recover_failed_deposit',[p['transactions'][label]])
current=read(address,'get_credit',[wallet])
if int(current['available_wei'])==2:
    p.setdefault('refundDemo',{})['before']=current
    save(p)
elif not (int(current.get('claim',{}).get('amount',0))==2 and current['claim']['status'] in ('PENDING','PAID')):
    raise RuntimeError('Both approved test wei must be refundable or already claimed in this resumable run')
receipt=tx(p,'refund-pull-credit',address,'claim_credit',[1])
children=receipt.get('triggered_transactions') or []
if len(children)!=1:raise RuntimeError('Expected one exact refund native child')
tx(p,'refund-verify-credit',address,'verify_claim',['CREDIT',wallet,1,p['transactions']['refund-pull-credit'],children[0]])
p['refundDemo']={**p.get('refundDemo',{}),'wallet':wallet,'after':read(address,'get_credit',[wallet]),'failedParent':p['transactions'][label],'nativeChild':children[0]}
save(p)
print('Two-wei refund test finalized and native credit verified',flush=True)
