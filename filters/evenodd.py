##parameters=mlist
i=0
rv=[]
for m in mlist:
    if i&1:
        rv.append(m)
    i+=1
return rv
