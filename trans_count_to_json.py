"""
Converts the transaction count csv query to a json
"""
import csv
import json

PROJECTS = {
    1: "sentry",
    11276: "javascript",
    300688: "snuba",
    4504044639748096: "gibpotato-backend",
    4504044640927744: "gibpotato-frontend",
}


def main():
    first_line = True
    result = []
    with open("dist-query.csv", "rt") as f:
        reader = csv.reader(f)
        for line in reader:
            if first_line:
                first_line = False
                continue
            project_id = int(line[1])
            name = line[2]
            project_name = PROJECTS.get(project_id)
            freq = float(line[3])
            result.append({
                "name": name,
                "freq": freq,
                "proj_id": project_id,
                "proj_name": project_name
            })

    with open("projects.json", "wt") as f:
        json.dump(result,f, indent=2)

if __name__ == '__main__':
    main()
