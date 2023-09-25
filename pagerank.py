from google.cloud import storage
import pandas as pd
import re
from tqdm import tqdm
import os
import concurrent.futures
import time


def calc_pagerank(n:int, out_matrix:list[dict[int,int]], in_matrix:list[dict[int,int]]):
    print("Starting PageRank algorithm...")
    PR_list = [(i, 0.0) for i in range(n)]
    prevPRSum = 0.0
    currPRSum = 0.0
    iters = 0

    # Precompute C: List of total outgoing links for each page
    C = [0 for _ in range(n)]
    for i in range(len(out_matrix)):
        C[i] = sum(out_matrix[i].values())

    while True:
        new_PRs = [(i, 0.0) for i in range(n)]

        for target in range(len(PR_list)):
            # Use PageRank algorithm to calculate new PR value
            PR = 0.15

            for source in in_matrix[target].keys():
                PR += 0.85 * (PR_list[source][1] / C[source])
            
            new_PRs[target] = (target, PR)

        prevPRSum = currPRSum
        currPRSum = sum([x for _,x in new_PRs])
        PR_list = new_PRs
        iters += 1

        if (abs(prevPRSum - currPRSum) / currPRSum < 0.005):
            break

    for i in range(len(PR_list)):
        PR_list[i] = (i, (PR_list[i][1] / currPRSum))

    print("Done in " + str(iters) + " iterations")
    return PR_list

def adj_matrix_worker(blob):
    #source = int(blob.name.split('.')[0])
    source = int(blob.name.split('/')[1].split('.')[0])

    out_edges = []

    with blob.open('r') as f:
        contents = f.read()

    outlinks = re.findall(r"\d+.html", contents)
    out = list(map(lambda s: int(s.split('.')[0]), outlinks))

    for i in out:
        out_edges.append((source, i))

    return out_edges

def parse_blobs_into_adj_matrix(blobs):
    """
    out_matrix is a list of dicts, where
    out_matrix[i] accesses a dictionary containing the outgoing links and counts of i's page

    in_matrix is a list of dicts, where
    in_matrix[i] accesses a dictionary containing the incoming links and counts of pages that link to page i
    """
    print("Starting parsing blobs...")
    out_edges = []
    out_matrix = [{} for _ in range(len(blobs))]
    in_matrix = [{} for _ in range(len(blobs))]

    # with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
    #     for blob in tqdm(blobs):
    #         future = executor.submit(adj_matrix_worker, blob)
    #         out_edges.extend(future.result())

    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        for e in tqdm(executor.map(adj_matrix_worker, blobs), total=10000):
            out_edges.extend(e)

    print("Done")
    print("Converting to adj matrix...")
    
    for (source, target) in out_edges:
        if target in out_matrix[source]:
            out_matrix[source][target] += 1
        else:
            out_matrix[source][target] = 1

        if source in in_matrix[target]:
            in_matrix[target][source] += 1
        else:
            in_matrix[target][source] = 1

    print("Done")
    return out_matrix, in_matrix

def main():
    storage_client = storage.Client()
    #bucket_name = "bu-ds561-eawang-hw2-sample"
    bucket_name = "bu-ds561-eawang-hw2-pagerank"

    print("Fetching blobs from bucket...")
    bucket = storage_client.bucket(bucket_name)
    blobs = list(bucket.list_blobs())
    print("Done")

    #blobs = os.listdir("./files")

    # Parse input files and precompute adjacency matrices
    out_matrix, in_matrix = parse_blobs_into_adj_matrix(blobs)

    # TODO: Calc stats


    # TODO: Calc PageRank
    start = time.perf_counter()
    pagerank = calc_pagerank(len(blobs), out_matrix, in_matrix)
    end = time.perf_counter()

    # TODO: Print results
    pagerank.sort(key=lambda x: x[1],reverse=True)
    print(pagerank[:5])

    print("PageRank timer: ", str(end - start))

    return

if __name__ == "__main__":
    main()
