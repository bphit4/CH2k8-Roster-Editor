# CH2k8-Roster-Editor

## Roster export helper

`roster_dump.py` reads the `USERDATA` roster file, uses `team_offsets.txt` to locate each team block, and exports:

- `dump.json` with decoded team strings, pointer metadata, per-team block hex, and any extra UTF-16 strings detected in each team block.
- `teams.csv` with the decoded team name fields.
- `conferences.csv` with conference names from the conference table.

Run it from the repo root:

```bash
python roster_dump.py --input USERDATA
```

## String scan helper

To continue parsing the roster file beyond the team/conference tables, use the string scan helper. It loads
`dump.json`, filters out known team/conference strings, and reports any other UTF-16LE strings found in the
roster file.

```bash
python roster_string_scan.py --input USERDATA --dump-json dump.json
```
