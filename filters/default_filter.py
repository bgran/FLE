##parameters=mlist

#ind = 0 # Used to keep state of the current level.
curr_level = 0
v = 'visual'
l = 'level'
o = 'obj'


rv = []

for m in mlist:
    m[v] = []
    if m[l] == curr_level:
        m[v] = range(curr_level)
    elif m[l] > curr_level:
        if abs(m[l] - curr_level) > 1:
            raise 'FLE Error', 'delta between curr_level and note.level can not be more than 1!'
        curr_level += 1
        m[v] = range(curr_level)
    else:
        curr_level -= 1
        m[v] = range(curr_level)

    rv.append(m)

return rv
