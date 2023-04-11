from pandas import DataFrame
import json
from urllib import request

IMPLICIT_TRANSACTIONS_CONDITION = {
    "op": "and",
    "inner": []
}


def json_rules_to_frame(file_url: str) -> DataFrame:
    with request.urlopen(file_url) as f:
        rules = json.load(f)
    simple_rules = []
    for rule in rules:
        rule_id = rule["id"]
        if rule["condition"] == IMPLICIT_TRANSACTIONS_CONDITION:
            name = "*"
        else:
            name = rule["condition"]["inner"][0]["value"][0]

        if rule["type"] == "transaction" and 1400 <= rule_id < 1500:
            simple_rules.append({
                "factor": rule["samplingValue"]["value"],
                "name": name
            })

    ret_val = DataFrame(data=simple_rules)
    return ret_val


def idx_to_label(idx:int):
    base="abcdefghijklmnopqrstuvw"
    l = len(base)
    result = ""
    if idx <= 0 :
        return"a"
    count =0
    while idx>0:
        result+=base[idx%l]
        idx //= l
        count+=1
        if count % 3 == 0:
            result+="-"


    if result[-1] == '-':
        result = result[:-1]

    return result



# for debug
if __name__ == '__main__':
    pd = json_rules_to_frame("https://raw.githubusercontent.com/RaduW/volume-rebalance/main/rules-2023-03-30.json")
    print(pd)
