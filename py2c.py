import re, os

#exp_class = re.compile('((.*\n)+?class .*\n((\w|#).*\n)+)*',re.M)
exp_classname = re.compile('\nclass (.*?)(\(|:)',re.M)
exp_lastclassname = re.compile('(.*\n)*\nclass (.*?)(\(|:)',re.M)
exp_superclasses = re.compile('\nclass [a-zA-Z]+\(\n?.*?([#\na-zA-Z.\t, ]*?)\)',re.M)
exp_classdoc1 = re.compile('\nclass .*(\n.*)*?:\n.*"""((.*\n)*?.*)"""',re.M)
exp_classdoc2 = re.compile('((#.*\n)+)class',re.M)
exp_methods = re.compile('def ([a-zA-Z_0-9]+?)\(',re.M)
exp_methoddoc = re.compile('"""((.*\n)*?.*)"""',re.M)
exp_attributes = re.compile('self.([a-zA-Z_0-9]+) ?=',re.M)

def convert(file):
    print "FILE: "+file
    f = open(file,'r')
    py = f.read()
    f.close()

    classes=[('foo',-1)]
    firstpos=0
    while 1:
        res = exp_classname.search(py[firstpos:])
        if res:
            #print res.group(1)
            #print res.start(1)
            firstpos+=res.start(1)+1
            classes += [(res.group(1),firstpos)]
        else:
            break
    classes+=[('bar',len(py))]

    for n in range(len(classes)-2):
        start = classes[n][1]+1
        end = classes[n+2][1]
        print start
        print end
        convertClass(py[start:end])

def convertClass(py):
    cname = exp_classname.search(py).group(1)
    print "CLASS: "+cname
    cdoc=""
    res = exp_classdoc1.search(py)
    if res:
        cdoc = res.group(2)
        res=exp_classdoc2.search(py)
        if res:
            cdoc += '\n'+''.join(res.group(1).split('#'))
    res=exp_superclasses.search(py)
    supers=[]
    if res:
        for item in res.group(1).split(','):
            if item.find('#')>-1:
                continue
            sname = item.strip()
            if len(sname)==0:
                continue
            pos=sname.rfind('.')
            if pos!=-1:
                sname = sname[pos+1:]
            supers+=[sname,]

    methods=[]
    res = exp_methods.split(py)
    if res:
        #print "METHODS: "+str(len(res.groups()))
        for i in range(1,len(res),2):
            res2 = exp_methoddoc.search(res[i+1])
            if res2:
                doc=res2.group(1)
            else:
                doc=""
            methods+=[(res[i],doc),]

    attribs=[]
    res = exp_attributes.split(py)
    if res:
        for i in range(1,len(res),2):
            if res[i] not in attribs:
                attribs+=[res[i],]

    f = open('c/'+cname+'.h','w')
    f.write('#ifndef '+cname.upper()+'_H\n#define '+cname.upper()+'_H\n')
    for super in supers:
        f.write('#include "'+super+'.h"\n')
    f.write('\n/** '+'\n  * '.join(cdoc.split('\n'))+'*/\n')
    f.write('class '+cname)
    if supers:
        f.write(' : public '+', public '.join(supers))
    f.write(' {\n')
    f.write('public:\n')
    f.write('// Attributes:\n')
    for attrib in attribs:
        f.write('\t'+attrib+';\n')
    f.write('\n//Operations:\n')
    for method,doc in methods:
        if doc:
            f.write('/** '+doc+'*/\n')
        f.write('\t'+method+'();\n')
    f.write('};\n')
    f.write('#endif '+cname.upper()+'_H\n')
    f.close()

files = os.listdir('.')
exp = re.compile("^[A-Z].*\.py$")
for file in files:
    if exp.search(file):
        convert(file)


