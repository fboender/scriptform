#!/usr/bin/python

import os
import pwd
import grp

pw = pwd.getpwuid(os.getuid())
gr = grp.getgrgid(pw.pw_gid)
groups = [g.gr_gid for g in grp.getgrall() if pw.pw_name in g.gr_mem]
priv_esc = True
try:
    os.seteuid(0)
except OSError:
    priv_esc = False

print """Running as:

uid = {0}
gid = {1}
groups = {2}""".format(pw.pw_uid, gr.gr_gid, str(groups))

