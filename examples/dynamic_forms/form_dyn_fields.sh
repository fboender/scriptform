#!/bin/sh

OPTIONS=$(cat <<'END_HEREDOC'
[
    ["test", "Test DB"],
    ["acc", "Acc DB"],
    ["prod", "Prod DB"]
]
END_HEREDOC
)

cat << END_TEXT
[
    {
        "name": "target_db",
        "title": "Database to import to",
        "type": "radio",
        "options": $OPTIONS
    },
    {
        "name": "sql_file",
        "title": "SQL file",
        "type": "file"
    }
]
END_TEXT
