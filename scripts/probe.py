import hashlib
from chain import ROOT,load,save,tx,read

p=load()
if not p.get('probeContract'):
    code=(ROOT/'contracts/access_probe.py').read_text()
    r=tx(p,'probe-deploy',code=code)
    p['probeContract']=r.get('recipient',r.get('to_address'))
    p['probeSourceSha256']=hashlib.sha256(code.encode()).hexdigest()
    save(p)
urls=[
 'https://web.archive.org/cdx/search/cdx?url=www.apple.com/newsroom/2023/06/introducing-apple-vision-pro/&output=json&fl=timestamp,original&filter=statuscode:200&limit=1',
 'https://web.archive.org/web/20230605200500id_/https://www.apple.com/newsroom/2023/06/introducing-apple-vision-pro/',
 'https://en.wikipedia.org/w/index.php?title=Apple_Vision_Pro&oldid=1158818135',
 'https://www.apple.com/newsroom/2023/06/introducing-apple-vision-pro/',
 'https://www.realmadrid.com/',
 'https://www.nintendo.com/',
 'https://www.oscars.org/',
 'https://reuters.com/',
 'https://apnews.com/',
 'https://bbc.com/'
]
p.setdefault('probes',{})
for i,url in enumerate(urls):
    if url in p['probes']:continue
    tx(p,'probe-'+str(i),p['probeContract'],'probe',[url])
    p['probes'][url]=read(p['probeContract'],'result',[url])
    save(p)
    print(url,p['probes'][url],flush=True)
