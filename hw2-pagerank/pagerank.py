from google.cloud import storage
import numpy as np
import re
from tqdm import tqdm
import os
import concurrent.futures
import time


def calc_statistics(out_matrix, in_matrix):
    print("Starting in/out degrees statistics...")
    out_stats, in_stats, out_degrees, in_degrees = [], [], [], []

    for x in range(len(out_matrix)):
        out_degrees.append(sum(out_matrix[x].values()))

    for x in range(len(in_matrix)):
        in_degrees.append(sum(in_matrix[x].values()))

    out_degrees = np.array(out_degrees)
    in_degrees = np.array(in_degrees)

    # Average
    out_stats.append(np.mean(out_degrees))
    in_stats.append(np.mean(in_degrees))

    # Median
    out_stats.append(np.median(out_degrees))
    in_stats.append(np.median(in_degrees))

    # Max
    out_stats.append(np.max(out_degrees))
    in_stats.append(np.max(in_degrees))

    # Min
    out_stats.append(np.min(out_degrees))
    in_stats.append(np.min(in_degrees))

    # Quintiles
    out_stats.append(np.quantile(out_degrees, q=[0.2, 0.4, 0.6, 0.8, 1.0]))
    in_stats.append(np.quantile(in_degrees, q=[0.2, 0.4, 0.6, 0.8, 1.0]))

    print("Done")
    return out_stats, in_stats

def calc_pagerank(n:int, out_matrix:list[dict[int,int]], in_matrix:list[dict[int,int]]):
    print("Starting PageRank algorithm...")
    PR_list = [(i, 0.0) for i in range(n)]
    prevPRSum = 0.0
    currPRSum = 0.0
    iters = 0

    # Precompute C: List of total outgoing links for each page
    out_sums = [0 for _ in range(n)]
    for i in range(len(out_matrix)):
        out_sums[i] = sum(out_matrix[i].values())
    C = np.array(out_sums)

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

    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()*5) as executor:
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

    out_m = np.array(out_matrix)
    in_m = np.array(in_matrix)

    print("Done")
    return out_m, in_m

def print_stats(out_stats, in_stats):
    stats = ["Mean: ", "Median: ", "Max: ", "Min: ", "Quintiles: "]

    print("OUTGOING LINKS STATS:")
    for i in range(len(out_stats)):
        print('\t' + stats[i] + str(out_stats[i]))

    print()

    print("INCOMING LINKS STATS:")
    for i in range(len(in_stats)):
        print('\t' + stats[i] + str(in_stats[i]))

    return

def print_pagerank(pagerank):
    pagerank.sort(key=lambda x: x[1],reverse=True)

    print("Top 5 PageRanks:")
    for i in range(5):
        print("\tRank " + str(i+1) + ": Page " + str(pagerank[i][0]) + " - " + str(pagerank[i][1]) )

    return

def main():
    storage_client = storage.Client()
    #bucket_name = "bu-ds561-eawang-hw2-sample"
    bucket_name = "bu-ds561-eawang-hw2-pagerank"

    print("Fetching blobs from bucket...")
    bucket = storage_client.bucket(bucket_name)
    blobs = list(bucket.list_blobs())
    print("Done")

    # Parse input files and precompute adjacency matrices
    out_matrix, in_matrix = parse_blobs_into_adj_matrix(blobs)

    # TODO: Calc stats
    out_stats, in_stats = calc_statistics(out_matrix, in_matrix)

    # TODO: Calc PageRank
    start = time.perf_counter()
    pagerank = calc_pagerank(len(blobs), out_matrix, in_matrix)
    end = time.perf_counter()

    # TODO: Print results
    print()
    print_stats(out_stats, in_stats)
    print()
    print_pagerank(pagerank)

    print("PageRank timer: ", str(end - start))

    return

if __name__ == "__main__":
    main()
