"""Verify public release file identities, links, source syntax and explicit byte reuse."""
from pathlib import Path
import json,hashlib,re,ast
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    m=json.loads((ROOT/'MANIFEST.json').read_text('utf-8'))
    expected={x['path']:x for x in m['files']}
    actual={x.relative_to(ROOT).as_posix():x for x in ROOT.rglob('*') if x.is_file() and '.git' not in x.relative_to(ROOT).parts}
    legacy={x['path']:x for x in m.get('preserved_legacy',[])}
    assert set(actual)==set(expected)|set(legacy)|{'MANIFEST.json','SHA256SUMS.txt'}
    for n,x in legacy.items():
        b=actual[n].read_bytes();assert len(b)==x['bytes'] and hashlib.sha1(b'blob '+str(len(b)).encode('ascii')+b'\0'+b).hexdigest()==x['git_sha'],n
    for n,x in expected.items():
        f=actual[n];assert f.stat().st_size==x['bytes'] and sha(f)==x['sha256'],n
        assert f.suffix.lower() not in {'.pt','.pth','.npz','.npy','.pkl','.pem','.key','.docx'},n
        if f.suffix=='.py':ast.parse(f.read_text('utf-8'))
        if f.suffix in {'.md','.py','.json','.txt','.svg'}:
            b=f.read_bytes()
            assert not re.search(rb'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|/home/[a-z][A-Za-z0-9_-]*/|[CG]:[/\\]Users[/\\])',b),n
        if f.suffix=='.md':
            for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',f.read_text('utf-8')):
                if link.startswith(('https://','http://','#','mailto:')):continue
                target=link.split('#',1)[0].strip('<>');assert (f.parent/target).exists(),(n,link)
    reuse=json.loads((ROOT/'provenance/explicit_companion_reuse.json').read_text('utf-8'))
    assert len(reuse['entries'])==79
    for x in reuse['entries']:assert expected[x['path']]['sha256']==x['sha256']
    rows=(ROOT/'SHA256SUMS.txt').read_text('utf-8').splitlines()
    for row in rows:
        h,n=row.split('  ',1);assert sha(ROOT/n)==h,n
    assert len(rows)==len(expected)+1
    print(json.dumps(dict(status='ALL_PUBLIC_FILES_IDENTITIES_LINKS_SYNTAX_AND_REUSE_PASS',files=len(actual),exact_reused_explicit_files=79,bytes=sum(f.stat().st_size for f in actual.values())),indent=2))
if __name__=='__main__':main()
