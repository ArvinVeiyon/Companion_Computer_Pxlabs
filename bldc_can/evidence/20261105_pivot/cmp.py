import csv,sys,collections
def stats(rcf,esf):
    rc=list(csv.DictReader(open(rcf))); es=list(csv.DictReader(open(esf)))
    rct=[(float(r['t']),float(r['roll']),float(r['throttle'])) for r in rc]
    import bisect; ts=[x[0] for x in rct]
    def stick(t):
        i=max(0,bisect.bisect_right(ts,t)-1); return rct[i][1],rct[i][2]
    dur=float(es[-1]['t'])-float(es[0]['t'])
    ep=collections.Counter(); prev={}
    for r in es:
        w=r['wheel']; f=r['fault']!='0'
        if f and not prev.get(w): ep[w]+=1
        prev[w]=f
    out={'dur':dur,'faults':dict(ep),'ftot':sum(ep.values())}
    # per direction, per wheel: during |roll|>0.25 & thr==0
    for d,name in [(1,'roll+'),(-1,'roll-')]:
        per={}
        for w in ['FR','FL','RR','RL']:
            s=[r for r in es if r['wheel']==w]
            sel=[r for r in s if (lambda st: st[0]*d>0.25 and abs(st[1])<0.02)(stick(float(r['t'])))]
            if not sel: continue
            lim=sum(abs(float(r['i_mot']))>=LIM-0.1 for r in sel)/len(sel)
            stall=sum(abs(float(r['i_mot']))>=LIM-0.5 and abs(int(r['rpm']))<300 for r in sel)/len(sel)
            rpm=sum(abs(int(r['rpm'])) for r in sel)/len(sel)
            per[w]=(rpm,lim,stall,len(sel))
        out[name]=per
    return out
for label,rcf,esf in [(a.split('|')[0],a.split('|')[1],a.split('|')[2]) for a in sys.argv[1:]]:
    o=stats(rcf,esf)
    print(f"== {label}: {o['dur']:.0f}s  trips {o['ftot']} ({o['ftot']/o['dur']*60:.1f}/min) {o['faults']}")
    for d in ['roll+','roll-']:
        print(f"  {d}: "+"  ".join(f"{w} |rpm|{v[0]:4.0f} @14A {100*v[1]:3.0f}% stall {100*v[2]:3.0f}%" for w,v in o[d].items())+f"  (n={list(o[d].values())[0][3] if o[d] else 0})")
