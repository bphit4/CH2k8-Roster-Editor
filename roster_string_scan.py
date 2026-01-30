import argparse
import json


def read_utf16le_string(data, pointer, max_bytes=256):
    output = bytearray()
    while pointer + 2 <= len(data) and len(output) < max_bytes:
        if data[pointer:pointer + 2] == b"\x00\x00":
            break
        output.extend(data[pointer:pointer + 2])
        pointer += 2
    return output.decode("utf-16-le", errors="replace")


def is_printable_string(value):
    if not value:
        return False
    printable = sum(1 for ch in value if ch.isprintable())
    return printable / len(value) >= 0.85


def load_known_strings(dump_payload):
    known = set()
    for team in dump_payload.get("teams", []):
        known.update(
            {
                team.get("team_name", ""),
                team.get("team_abbr", ""),
                team.get("team_name_2", ""),
                team.get("nickname", ""),
                team.get("mascot", ""),
            }
        )
        for extra in team.get("extra_strings", []):
            value = extra.get("value")
            if value:
                known.add(value)
    for conference in dump_payload.get("conferences", []):
        value = conference.get("name")
        if value:
            known.add(value)
    known.discard("")
    return known


def scan_for_strings(data, known_strings, min_length, max_length):
    results = []
    seen_offsets = set()
    max_bytes = (max_length + 1) * 2
    for offset in range(0, len(data) - 1, 2):
        if data[offset:offset + 2] == b"\x00\x00":
            continue
        if offset > 0 and data[offset - 2:offset] != b"\x00\x00":
            continue
        if offset in seen_offsets:
            continue
        value = read_utf16le_string(data, offset, max_bytes=max_bytes)
        if not (min_length <= len(value) <= max_length):
            continue
        if value in known_strings:
            continue
        if not is_printable_string(value):
            continue
        seen_offsets.add(offset)
        results.append(
            {
                "offset": offset,
                "offset_hex": hex(offset),
                "length": len(value),
                "value": value,
            }
        )
    return results


def write_csv(path, rows):
    with open(path, "w", encoding="utf-8") as file:
        file.write("offset_hex,length,value\n")
        for row in rows:
            value = str(row["value"]).replace("\"", "\"\"")
            file.write(f"\"{row['offset_hex']}\",{row['length']},\"{value}\"\n")


def main():
    parser = argparse.ArgumentParser(
        description="Scan USERDATA for UTF-16LE strings not already captured in dump.json."
    )
    parser.add_argument("--input", default="USERDATA", help="Path to USERDATA roster file.")
    parser.add_argument("--dump-json", default="dump.json", help="Path to dump.json from roster_dump.py.")
    parser.add_argument("--json-out", default="roster_strings.json", help="Path for JSON output.")
    parser.add_argument("--csv-out", default="roster_strings.csv", help="Path for CSV output.")
    parser.add_argument("--min-length", type=int, default=2, help="Minimum string length to include.")
    parser.add_argument("--max-length", type=int, default=64, help="Maximum string length to include.")
    args = parser.parse_args()

    with open(args.dump_json, "r", encoding="utf-8") as file:
        dump_payload = json.load(file)

    with open(args.input, "rb") as file:
        data = file.read()

    known_strings = load_known_strings(dump_payload)
    strings = scan_for_strings(data, known_strings, args.min_length, args.max_length)

    payload = {
        "file_length": len(data),
        "strings": strings,
    }

    with open(args.json_out, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)

    write_csv(args.csv_out, strings)


if __name__ == "__main__":
    main()
