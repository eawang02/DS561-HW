from google.cloud import storage
import pandas as pd
import re


def calc_pagerank(n, out_matrix, in_matrix):
    pagerank_list = [0 for _ in range(n)]

    return pagerank_list

def parse_blobs_into_adj_matrix(blobs):
    """
    out_matrix is a list of dicts, where
    out_matrix[i] accesses a dictionary containing the outgoing links and counts of i's page

    in_matrix is a list of dicts, where
    in_matrix[i] accesses a dictionary containing the incoming links and counts of pages that link to page i
    """
    print("Starting parsing blobs into adj matrix...")
    out_matrix = [{} for _ in range(len(blobs))]
    in_matrix = [{} for _ in range(len(blobs))]

    for blob in blobs:
        source = int(blob.name.split('.')[0])

        with blob.open("r") as f:
            contents = f.read()
            outlinks = re.findall(r"\d+.html", contents)
            outDict = {}
            out = list(map(lambda s: int(s.split('.')[0]), outlinks))

            for i in out:
                if i in outDict:
                    outDict[i] += 1
                else:
                    outDict[i] = 1

                if source in in_matrix[i]:
                    in_matrix[i][source] += 1
                else:
                    in_matrix[i][source] = 1

            out_matrix[source] = outDict

    print("Done")
    return out_matrix, in_matrix

def main():
    storage_client = storage.Client(project="ds561cloudcomputing")
    bucket_name = "bu-ds561-eawang-hw2-sample"
    blobs = list(storage_client.list_blobs(bucket_name))

    # Parse input files and precompute adjacency matrices
    out_matrix, in_matrix = parse_blobs_into_adj_matrix(blobs)

    # TODO: Calc and print stats


    # TODO: Calc PageRank
    pagerank = calc_pagerank(len(blobs), out_matrix, in_matrix)

    # TODO: Print results


    return

if __name__ == "__main__":
    main()
