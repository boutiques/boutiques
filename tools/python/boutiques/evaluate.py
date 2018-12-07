#!/usr/bin/env python

from boutiques.logger import print_error


def evaluateEngine(executor, query):
    try:
        # TODO: improve splitting to not fail in valid situations
        layers = query.split("/")[:-1] if "/" in query else [query]
        conditions = query.split("/")[-1] if "/" in query else []
        if len(conditions) > 0:
            if "," in conditions:
                conditions = conditions.split(",")
            else:
                conditions = [conditions]

        objs = executor.desc_dict
        for layer in layers:
            objs = objs[layer]

        query_result = {}
        for obj in objs:
            eligible = True
            for cond in conditions:
                lhs, rhs = cond.split("=")
                try:
                    rhs = float(rhs)
                except ValueError:
                    if rhs == "False":
                        rhs = False
                    elif rhs == "True":
                        rhs = True

                if obj.get(lhs) != rhs:
                    if not (obj.get(lhs) is None and rhs is False):
                        eligible = False

            if eligible:
                if "output-files" in layers:
                    query_result[obj["id"]] = executor.out_dict.get(obj["id"])
                elif "inputs" in layers:
                    # print(obj)
                    query_result[obj["id"]] = executor.in_dict.get(obj["id"])
                elif "groups" in layers:
                    query_result[obj["id"]] = {}
                    for mem in obj['members']:
                        query_result[obj["id"]][mem] = executor.in_dict.get(mem)

        return query_result

    except Exception:
        print_error("Invalid query ({0}). See --help.".format(query))
        return {}
