#! /usr/bin/env python
import sys, string, re

magic_sep = 'Index: '

if __name__ == '__main__':
        file = sys.argv[1]
        print "Reading: %s" % (file)
        buf = open(file, "r").readlines()
        print "Reading: file size: %s" % (len(buf))

        p = []
        prev_patch = ""
        for line in buf:
                if line[:len(magic_sep)] == magic_sep:
                        # write stuff, and clean p
                        if prev_patch:
                                print "Writing: %s" % (prev_patch+'.patch')
                                open(prev_patch+'.patch', 'w').write(
                                        string.join(p, ''))
                                prev_patch = line[len(magic_sep):-1]
                                prev_patch = re.sub("/", "_", prev_patch)
                                p = []
                        else:
                                # We are just starting things here.
                                prev_patch = line[len(magic_sep):-1]
                                prev_patch = re.sub("/", "_", prev_patch)
                p.append(line)
        print "Writing: %s" % (prev_patch+'.patch')
        open(prev_patch+'.patch', 'w').write(string.join(p, ''))


