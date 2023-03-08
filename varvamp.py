#!/usr/bin/env python
"""
            INFO
------------------------------
This contains the main workflow.

           LICENCE
-------------------------------
todo

         EXPLANATIONS
-------------------------------
varVAMP primer design for viruses with highly variable genomes. varVAMP
first preprocesses the alignment and then creates consensus sequences
that can contain ambiguous characters. Then it searches for conserved
regions as defined by a user defined amount of ambiguous charaters within
the min length of a primer. The conserved regions of a consensus sequence
containing the most prevalent nucleotide (no wobbels) is then digested into
kmers which are considered potential primers if they pass all primer settings.
These primers are further filtered for high scoring primers for each region
where primers were found. Then it constructs all possible amplicons and from
that determines which amplicons are overlapping. A graph based approach is
used to find the best amplicon scheme.
"""

# INFO
__author__ = "Dr. Jonas Fuchs"
__copyright__ = "Copyright 2023"
__license__ = "GPL"
__version__ = "0.2"
__email__ = "jonas.fuchs@uniklinik-freiburg.de"
__status__ = "Development"

# BUILT-INS
import sys
import os
import shutil
import time
import argparse

# varVAMP
from scr import config
from scr import alignment
from scr import consensus
from scr import conserved
from scr import primers
from scr import scheme


# DEFs
def varvamp_progress(progress=0, job="", progress_text=""):
    """
    progress bar, main progress logging and folder creation
    """
    barLength = 40
    block = int(round(barLength*progress))

    if progress == 0:
        if args.console:
            print(
                "\nStarting \033[31m\033[1mvarVAMP ◥(ºwº)◤\033[0m primer design\n",
                flush=True
            )
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        else:
            shutil.rmtree(results_dir)
            os.makedirs(results_dir)
        os.makedirs(all_data_dir)
        with open(results_dir+"varvamp_log.txt", 'w') as f:
            f.write('VARVAMP log \n\n')
    else:
        if progress == 1:
            stop_time = str(round(time.process_time() - start_time, 2))
            progress_text = f"all done \n\n\rvarVAMP created an amplicon scheme in {stop_time} sec!\n"
            job = "Finalizing output."
        if args.console:
            print(
                "\rJob:\t\t " + job + "\nProgress: \t [{0}] {1}%".format("█"*block + "-"*(barLength-block), progress*100) + "\t" + progress_text,
                flush=True
            )
        with open(results_dir+"varvamp_log.txt", 'a') as f:
            print(
                f"\rJob:\t {job} \nResult:\t {progress_text}",
                file=f
            )


def raise_error(message, exit=False):
    """
    raises warnings or errors, writes to log
    """
    # log errors and warnings
    with open(results_dir+"varvamp_log.txt", 'a') as f:
        if exit:
            print(f"ERROR: {message}", file = f)
        else:
            print(f"WARNING: {message}", file = f)
    # always show error message
    if exit:
        sys.exit(f"\n\033[31m\033[1mERROR:\033[0m {message}")
    else:
        if args.console:
            print(
                f"\033[31m\033[1mWARNING:\033[0m {message}"
        )


def raise_arg_errors(args):
    """
    checks arguments for non-valid input and raises warnings
    """
    # threshold error
    if args.threshold > 1 or args.threshold < 0:
        raise_error(
            "threshold can only be between 0-1",
            exit=True
        )
    if args.allowed_ambiguous < 0:
        raise_error(
            "number of ambiguous chars can not be negative",
            exit=True
        )
    if args.allowed_ambiguous > 4:
        raise_error(
            "high number of ambiguous nucleotides in primer leads to a high "
            "degeneracy. Consider reducing."
        )
    if args.opt_length > args.max_length:
        raise_error(
            "optimal length can not be higher than the maximum amplicon length.",
            exit=True
        )
    if args.opt_length < 0 or args.max_length < 0:
        raise_error(
            "amplicon lengths can not be negative.",
            exit=True
        )
    if args.opt_length < 200 or args.max_length < 200:
        raise_error(
            "your amplicon lengths might be to small. Consider increasing"
        )
    if args.overlap < 0:
        raise_error(
            "overlap size can not be negative.",
            exit=True
        )
    if args.overlap < 50:
        raise_error(
            "small overlaps might hinder downstream analyses. Consider increasing."
        )
    if args.overlap > args.opt_length:
        raise_error(
            "overlaps can not be higher than the length of amplicons.",
            exit=True
        )


def confirm_config():
    """
    checks the config. raises error and warnings
    if nececarry.
    """
    error = False

    # check if all variables exists
    all_vars = [
        "FREQUENCY_THRESHOLD",
        "ALLOWED_N_AMB",
        "PRIMER_TMP",
        "PRIMER_GC_RANGE",
        "PRIMER_SIZES",
        "PRIMER_HAIRPIN",
        "MAX_POLYX",
        "MAX_DINUC_REPEATS",
        "MAX_DIMER_TMP",
        "MIN_3_WITHOUT_AMB",
        "MV_CONC",
        "DV_CONC",
        "DNTP_CONC",
        "DNA_CONC",
        "PRIMER_TM_PENALTY",
        "PRIMER_GC_PENALTY",
        "PRIMER_SIZE_PENALTY",
        "PRIMER_MAX_BASE_PENALTY",
        "PRIMER_3_PENALTY",
        "PRIMER_PERMUTATION_PENALTY",
        "MAX_AMPLICON_LENGTH",
        "OPT_AMPLICON_LENGTH",
        "MIN_OVERLAP"
    ]

    for var in all_vars:
        if var not in vars(config):
            raise_error(
                f"{var} does not exist in config!",
            )
            error = True
    # exit if variables are not defined
    if error:
        raise_error(
            "config is missing parameters. Look at the above warnings!",
            exit=True
        )
    # confirm tuples
    for type, tup in [("temp", config.PRIMER_TMP), ("gc",config.PRIMER_GC_RANGE), ("size", config.PRIMER_SIZES)]:
        if len(tup) != 3:
            raise_error(
                f"{type} tuple has to have the form (min, max, opt)!",
            )
            error = True
        if tup[0] > tup[1]:
            raise_error(
                f"min {type} should not exeed max {type}!",
            )
            error = True
        if tup[0] > tup[2]:
            raise_error(
                f"min {type} should not exeed opt {type}!",
            )
            error = True
        if tup[2] > tup[1]:
            raise_error(
                f"opt {type} should not exeed max {type}!",
            )
            error = True
        if any(map(lambda var: var < 0, tup)):
            raise_error(
                f"{type} can not contain negative values!",
            )
            error = True

    # check values that cannot be zero
    non_negative_var = [
        ("max polyx nucleotides", config.MAX_POLYX),
        ("max polyx nucleotides", config.MAX_DINUC_REPEATS),
        ("min number of 3 prime nucleotides without ambiguous nucleotides", config.MIN_3_WITHOUT_AMB),
        ("monovalent cation concentration", config.MV_CONC),
        ("divalent cation concentration", config.DV_CONC),
        ("dNTP concentration", config.DNTP_CONC),
        ("primer temperatur penalty", config.PRIMER_TM_PENALTY),
        ("primer gc penalty", config.PRIMER_GC_PENALTY),
        ("primer size penalty", config.PRIMER_SIZE_PENALTY),
        ("max base penalty", config.PRIMER_MAX_BASE_PENALTY),
        ("primer permutation penalty", config.PRIMER_PERMUTATION_PENALTY)
    ]
    for type, var in non_negative_var:
        if var < 0:
            raise_error(
                f"{type} can not be negative!",
            )
            error = True
    if any(map(lambda var: var < 0, config.PRIMER_3_PENALTY)):
        raise_error(
            "3' penalties can not be zero!"
        )
        error = True
    # exit if variables are not properly defined
    if error:
        raise_error(
            "config has flaws. Look at the above warnings!",
            exit=True
        )
    # specific warnings
    if config.PRIMER_HAIRPIN < 0:
        raise_error(
            "decreasing hairpin melting temp to negative values "
            "will influence successful primer search!"
        )
    if config.MAX_DIMER_TMP < 0:
        raise_error(
            "there is no need to set max dimer melting temp below 0."
        )
    if config.PRIMER_MAX_BASE_PENALTY < 8:
        raise_error(
            "decreasing the base penalty will hardfilter more primers."
        )


if __name__ == "__main__":

    # arg parsing
    parser = argparse.ArgumentParser()
    if len(sys.argv[1:]) < 1:
        parser.print_help()
        sys.exit("\033[31m\033[1mError:\033[0m No arguments")

    parser.add_argument(
        "alignment",
        help="alignment to design primers on"
    )
    parser.add_argument(
        "results",
        help="path for results dir"
    )
    parser.add_argument(
        "-ol",
        "--opt-length",
        help="optimal length of the amplicons",
        type=int,
        default=config.OPT_AMPLICON_LENGTH
    )
    parser.add_argument(
        "-ml",
        "--max-length",
        help="max length of the amplicons",
        type=int,
        default=config.MAX_AMPLICON_LENGTH
    )
    parser.add_argument(
        "-o",
        "--overlap",
        type=float,
        default=config.MIN_OVERLAP,
        help="min overlap of the amplicons"
    )
    parser.add_argument(
        "-t",
        "--threshold",
        type=float,
        default=config.FREQUENCY_THRESHOLD,
        help="threshold for nucleotides in alignment to be considered conserved"
    )
    parser.add_argument(
        "-a",
        "--allowed-ambiguous",
        type=int,
        default=config.ALLOWED_N_AMB,
        help="number of ambiguous characters that are allowed within a primer"
    )
    parser.add_argument(
        "--console",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="show varvamp console output"
    )

    args = parser.parse_args()

    # start time
    start_time = time.process_time()
    # create dirs
    if not args.results.endswith("/"):
        results_dir = args.results+"/"
    else:
        results_dir = args.results
    all_data_dir = args.results+"all_data/"
    # ini progress
    varvamp_progress()

    # check if all arguments are ok
    raise_arg_errors(args)
    # check if config is ok
    confirm_config()

    varvamp_progress(
        0.1,
        "Checking config.",
        "config file passed"
    )

    # preprocess and clean alignment of gaps
    alignment_cleaned, gaps_to_mask = alignment.process_alignment(
        args.alignment,
        args.threshold
    )

    # progress update
    varvamp_progress(
        0.2,
        "Preprocessing alignment and cleaning gaps.",
        f"{len(gaps_to_mask)} gaps with {alignment.calculate_total_masked_gaps(gaps_to_mask)} nucleotides"
    )

    # create consensus sequences
    majority_consensus, ambiguous_consensus = consensus.create_consensus(
        alignment_cleaned,
        args.threshold
    )

    # write to all_data
    consensus.write_fasta(all_data_dir, "majority_consensus", majority_consensus)
    consensus.write_fasta(all_data_dir, "ambiguous_consensus", ambiguous_consensus)


    # progress update
    varvamp_progress(
        0.3,
        "Creating consensus sequences.",
        f"length of the consensus is {len(majority_consensus)} nt"
    )

    # generate conserved region list
    conserved_regions = conserved.find_regions(
        ambiguous_consensus,
        args.allowed_ambiguous
    )

    # raise error if no conserved regions were found
    if not conserved_regions:
        raise_error("nothing conserved. Lower the threshod!", exit = True)

    # progress update
    varvamp_progress(
        0.4,
        "Finding conserved regions.",
        f"{conserved.mean(conserved_regions, majority_consensus)} % conserved"
    )

    # produce kmers for all conserved regions
    kmers = conserved.produce_kmers(
        conserved_regions,
        majority_consensus
    )

    # progress update
    varvamp_progress(
        0.5,
        "Digesting into kmers.",
        f"{len(kmers)} kmers"
    )

    # find potential primers
    left_primer_candidates, right_primer_candidates = primers.find_primers(
        kmers,
        ambiguous_consensus,
        alignment_cleaned
    )

    # raise error if no primers were found
    for type, primer_candidates in [("LEFT", left_primer_candidates),("RIGHT", right_primer_candidates)]:
        if not primer_candidates:
            raise_error(f"no {type} primers found.\n", exit = True)


    # progress update
    varvamp_progress(
        0.6,
        "Filtering for primers.",
        f"{len(left_primer_candidates)} fw and {len(right_primer_candidates)} rw potential primers"
    )

    # find best primers
    left_primer_candidates, right_primer_candidates = primers.find_best_primers(
        left_primer_candidates,
        right_primer_candidates
    )

    # progress update
    varvamp_progress(
        0.7,
        "Considering only high scoring primers.",
        f"{len(left_primer_candidates)} fw and {len(right_primer_candidates)} rw primers"
    )

    # find all possible amplicons
    amplicons = scheme.find_amplicons(
        left_primer_candidates,
        right_primer_candidates,
        args.opt_length,
        args.max_length
    )

    # raise error if no amplicons were found
    if not amplicons:
        raise_error(
            "no amplicons found. Increase the max "
            "amplicon length or lower threshold!\n",
            exit=True
        )

    # build the amplicon graph
    amplicon_graph = scheme.create_amplicon_graph(amplicons, args.overlap)

    # progress update
    varvamp_progress(
        0.8,
        "Finding potential amplicons.",
        str(len(amplicons)) + " potential amplicons"
    )

    coverage, amplicon_scheme = scheme.find_best_covering_scheme(
        amplicons,
        amplicon_graph
    )

    percent_coverage = round(coverage/len(ambiguous_consensus)*100, 2)

    varvamp_progress(
        0.9,
        "Creating amplicon scheme.",
        f"{percent_coverage} % total coverage with {len(amplicon_scheme)} amplicons"
    )

    # raise low coverage warning
    if percent_coverage < 70:
        raise_error(
            "coverage < 70 %. Possible solutions:\n"
            "\t - lower threshold\n"
            "\t - increase amplicons lengths\n"
            "\t - increase number of ambiguous nucleotides\n"
            "\t - relax primer settings (not recommended)\n"
        )

    # final progress
    varvamp_progress(1)
