#!/usr/bin/env python

# Copyright 2015 - 2017:
#   The Royal Institution for the Advancement of Learning McGill University,
#   Centre National de la Recherche Scientifique,
#   University of Southern California,
#   Concordia University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


def evaluateEngine(executor, query):
    try:
        #TODO: improve splitting to not fail in valid situations
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

                if obj[lhs] != rhs:
                    eligible = False

            if eligible:
                if "output-files" in layers:
                    query_result[obj["id"]] = executor.out_dict.get(obj["id"])
                elif "inputs" in layers:
                    # print(obj)
                    query_result[obj["id"]] = executor.in_dict.get(obj["id"])
                elif "groups" in layers:
                    query_result[obj["id"]] = {mem : executor.in_dict.get(mem)
                                               for mem in obj['members']}

        return query_result

    except:
        print("Invalid query ({}). See --help.".format(query))
        return {}

