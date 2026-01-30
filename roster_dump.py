import argparse
import binascii
import json
import re

TEAM_BLOCK_LENGTH = 0x2C0
TEAM_OFFSETS_FILE = "team_offsets.txt"
USERDATA_FILE = "USERDATA"

CONFERENCE_INFO_TABLE_START = 0x34597C
CONFERENCE_INFO_TABLE_END = 0x361198
CONFERENCE_BLOCK_LENGTH = 0xB94


def read_be_u32(data, offset):
    return int.from_bytes(data[offset:offset + 4], byteorder="big", signed=False)


def read_utf16le_string(data, pointer):
    output = bytearray()
    while data[pointer:pointer + 2] != b"\x00\x00":
        output.extend(data[pointer:pointer + 2])
        pointer += 2
    return output.decode("utf-16-le", errors="surrogatepass")


def load_team_offsets(path):
    offsets = []
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            match = re.search(r"offset:\s*(\d+)", line)
            if match:
                offsets.append(int(match.group(1)))
    return offsets


def chunked_hex(data, width=16):
    lines = []
    for index in range(0, len(data), width):
        chunk = data[index:index + width]
        lines.append(binascii.hexlify(chunk).decode("ascii"))
    return lines


def parse_teams(data, team_offsets):
    teams = []
    for team_index, team_offset in enumerate(team_offsets):
        strings = []
        pointers = []
        for field_index in range(5):
            pointer_offset = team_offset + field_index * 4
            pointer_value = read_be_u32(data, pointer_offset)
            string_pointer = pointer_offset + pointer_value
            string_value = read_utf16le_string(data, string_pointer)
            strings.append(string_value)
            pointers.append(
                {
                    "field_index": field_index,
                    "pointer_offset": pointer_offset,
                    "pointer_value": pointer_value,
                    "string_pointer": string_pointer,
                }
            )

        block = data[team_offset:team_offset + TEAM_BLOCK_LENGTH]
        teams.append(
            {
                "index": team_index,
                "offset": team_offset,
                "offset_hex": hex(team_offset),
                "team_name": strings[0],
                "team_abbr": strings[1],
                "team_name_2": strings[2],
                "nickname": strings[3],
                "mascot": strings[4],
                "pointers": pointers,
                "block_hex": chunked_hex(block),
            }
        )
    return teams


def parse_conferences(data):
    conferences = []
    for offset in range(CONFERENCE_INFO_TABLE_START, CONFERENCE_INFO_TABLE_END, CONFERENCE_BLOCK_LENGTH):
        pointer = read_be_u32(data, offset)
        conference_name_offset = offset + pointer
        conference_name = read_utf16le_string(data, conference_name_offset)
        conferences.append(
            {
                "offset": offset,
                "offset_hex": hex(offset),
                "name": conference_name,
                "name_pointer": conference_name_offset,
            }
        )
    return conferences


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8") as file:
        file.write(",".join(header))
        file.write("\n")
        for row in rows:
            escaped = [f"\"{str(value).replace('\"', '\"\"')}\"" for value in row]
            file.write(",".join(escaped))
            file.write("\n")


def main():
    parser = argparse.ArgumentParser(
        description="Decode College Hoops 2k8 roster USERDATA into structured JSON/CSV exports."
    )
    parser.add_argument("--input", default=USERDATA_FILE, help="Path to USERDATA roster file.")
    parser.add_argument("--team-offsets", default=TEAM_OFFSETS_FILE, help="Path to team_offsets.txt.")
    parser.add_argument("--json-out", default="roster_dump.json", help="Path for JSON output.")
    parser.add_argument("--teams-csv", default="teams.csv", help="Path for team CSV output.")
    parser.add_argument("--conferences-csv", default="conferences.csv", help="Path for conference CSV output.")
    args = parser.parse_args()

    with open(args.input, "rb") as file:
        data = file.read()

    team_offsets = load_team_offsets(args.team_offsets)
    teams = parse_teams(data, team_offsets)
    conferences = parse_conferences(data)

    payload = {
        "file_length": len(data),
        "teams": teams,
        "conferences": conferences,
    }

    with open(args.json_out, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)

    write_csv(
        args.teams_csv,
        ["index", "offset_hex", "team_name", "team_abbr", "team_name_2", "nickname", "mascot"],
        [
            [
                team["index"],
                team["offset_hex"],
                team["team_name"],
                team["team_abbr"],
                team["team_name_2"],
                team["nickname"],
                team["mascot"],
            ]
            for team in teams
        ],
    )

    write_csv(
        args.conferences_csv,
        ["offset_hex", "name"],
        [[conference["offset_hex"], conference["name"]] for conference in conferences],
    )

    print(f"Wrote {args.json_out} with {len(teams)} teams and {len(conferences)} conferences.")
    print(f"Wrote {args.teams_csv} and {args.conferences_csv}.")


if __name__ == "__main__":
    main()
