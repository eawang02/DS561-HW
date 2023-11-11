
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import apache_beam.io.fileio as fileio
import logging
import argparse
from google.cloud import storage
import re
import time


class ProcessHtmlFiles(beam.DoFn):
    def process(self, element):
        filepath, contents = element

        source = filepath.split('/')[-1]
        targets = re.findall(r"\d+.html", contents)

        tuples = [(source, t) for t in targets]

        return tuples


def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--bucket',
        default='gs://bu-ds561-eawang-hw2-pagerank',
        help='The bucket name to fetch from.')
    parser.add_argument(
        '--filepath',
        default='*.html',
        help='The path/pattern to find input files (including directory).')
    # parser.add_argument(
    #     '--output',
    #     default='output',
    #     help='Output file to write results to (in bucket path)')
    
    known_args, pipeline_args = parser.parse_known_args(argv)
    pipeline_options = PipelineOptions(pipeline_args)

    start = time.perf_counter()

    with beam.Pipeline(options=pipeline_options) as pipeline:
        target = known_args.bucket + '/' + known_args.filepath
        # output = known_args.bucket + '/' + known_args.output

        readable_files = (
            pipeline
            | fileio.MatchFiles(target)
            | fileio.ReadMatches()
            | beam.Reshuffle()
        )

        files_and_contents = (
            readable_files
            | beam.Map(lambda x: (x.metadata.path, x.read_utf8()))
        )
        
        source_target_tuples = (
            files_and_contents
            | 'Create tuples' >> beam.ParDo(ProcessHtmlFiles())
        )

        outdegree_counts = (
            source_target_tuples
            | 'PairSourceWithOne'   >> beam.Map(lambda x: (x[0], 1))
            | 'CombineSourceCounts' >> beam.CombinePerKey(sum)
            | 'Top5Outdegrees'      >> beam.combiners.Top.Of(5, key=lambda x: x[1])
            | 'PrintOutdegrees'     >> beam.Map(lambda x: logging.info(f"Top 5 Outdegree Files: {x}"))
        )

        indegree_counts = (
            source_target_tuples
            | 'PairTargetWithOne'   >> beam.Map(lambda x: (x[1], 1))
            | 'CombineTargetCounts' >> beam.CombinePerKey(sum)
            | 'Top5Indegrees'       >> beam.combiners.Top.Of(5, key=lambda x: x[1])
            | 'PrintIndegrees'      >> beam.Map(lambda x: logging.info(f"Top 5 Indegree Files: {x}"))
        )

    end = time.perf_counter()
    print("Time taken:", end - start)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()
