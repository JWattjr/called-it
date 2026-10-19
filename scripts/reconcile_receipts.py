"""Read-only recovery of public receipts for previously journalled hashes."""
import json
from eth_account import Account
from genlayer_py import create_client, studionet
from chain import ROOT, load, save, final, success

p=load()
c=create_client(chain=studionet,account=Account.create())
queue=list(p['transactions'].items())
for label,h in queue:
    path=ROOT/'deploy/receipts'/(label+'.json')
    if path.exists():
        receipt=json.loads(path.read_text(encoding='utf8'))
        if receipt.get('hash')!=h:
            raise RuntimeError('Saved receipt hash differs from journal: '+label)
    else:
        try:receipt=final(c,h,label)
        except RuntimeError:
            if label not in p.get('expectedFailures',{}):raise
            receipt=json.loads(path.read_text(encoding='utf8'))
    if success(receipt):
        for i,child in enumerate(receipt.get('triggered_transactions') or []):
            child_label=label+'-child-'+str(i)
            if child_label not in p['transactions']:
                p['transactions'][child_label]=child
                queue.append((child_label,child))
                save(p)
print('Every journalled hash has a saved public receipt; no writes submitted.',flush=True)
