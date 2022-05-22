from ariadne import QueryType, make_executable_schema, graphql_sync
import pyarrow as pa
import pyarrow.flight

import random
import string
import asyncio
import json

type_defs = """
    type Query {
        test_lists(
            length: Int!
        ): Result!
    }

    type Result {
        length: Int!
        int_list: [Int!]
        float_list: [Float!]
        string_list: [String!]
    }
"""

query = QueryType()


@query.field("test_lists")
def resolve_test_lists(_, info, length):

    int_list = []
    for i in range(length):
        n = random.randint(1, 30)
        int_list.append(n)

    float_list = []
    for i in range(length):
        n = random.uniform(1.0, 30.0)
        float_list.append(n)

    string_list = []
    sample_string = "pqrstuvwxy"
    for i in range(length):
        n = "".join((random.choice(sample_string)) for x in range(10))
        string_list.append(n)

    return {
        "length": length,
        "int_list": int_list,
        "float_list": float_list,
        "string_list": string_list,
    }

schema = make_executable_schema(type_defs, [query])

class FlightServer(pyarrow.flight.FlightServerBase):
    def __init__(self, location="grpc://0.0.0.0:8815", **kwargs):
        super(FlightServer, self).__init__(location, **kwargs)
        self._location = location
        print("started server at: " + location)

    def do_get(self, context, ticket):
        query = ticket.ticket.decode('utf-8')
        query = json.loads(query)
        print(query)
        success, result = graphql_sync(schema, query)
        arrow_data = pa.Table.from_pylist([result])
        return pa.flight.RecordBatchStream(arrow_data)

if __name__ == '__main__':
    server = FlightServer()
    server.serve()