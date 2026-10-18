# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
import json
from genlayer import *

class AccessProbe(gl.Contract):
    results: TreeMap[str,str]
    def __init__(self):
        pass

    @gl.public.write
    def probe(self, url: str) -> None:
        def fetch():
            try:
                r=gl.nondet.web.get(url,headers={'User-Agent':'Mozilla/5.0 CalledIt/1.0'})
                text=r.body.decode('utf8',errors='replace')
                return {'status':r.status,'length':len(text),'sample':text[:240]}
            except Exception:
                return {'status':0,'length':0,'sample':'Validator fetch failed'}
        def validate(result):
            own=fetch()
            return isinstance(result,gl.vm.Return) and own['status']==result.calldata['status'] and (own['length']>500)==(result.calldata['length']>500)
        self.results[url]=json.dumps(gl.vm.run_nondet_unsafe(fetch,validate))

    @gl.public.view
    def result(self,url: str) -> str:
        return self.results.get(url,'{}')
