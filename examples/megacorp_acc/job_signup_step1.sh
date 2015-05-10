#!/bin/sh

cat << EOF
HTTP/1.1 301 Moved Permanently
Location: form?form_name=signup_step_2&first_name=$first_name&last_name=$last_name&email_address=$email_address
Content-Type: text/html
Content-Length: 174
 
<html>
<head>
<title>Redir</title>
</head>
<body>
</body>
</html>
EOF
