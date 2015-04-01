ScriptForm output example
=========================

Output tpyes determine how Scriptform handles the output from a callback. The
options are: `escaped` (default), `html` and `raw`. The `escaped` option wraps
the output of the callback in PRE tags and escapes any HTML entities. The
`html` option doesn't, which lets the script include HTML formatting in the
output. The `raw` option directly streams the output of the script to the
browser. This allows you to stream images, binary files, etc directly to the
browser. The script should include a full HTTP response including appropriate
headers.
