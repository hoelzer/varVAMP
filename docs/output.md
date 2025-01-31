## varVAMP output

varVAMP produces multiple main output files:


| Output | Description |
| --- | --- |
| ambiguous_consensus.fasta | The consensus sequence containing ambiguous nucleotides. |
| amplicon_plot.pdf | A nice overview for your final amplicon design. |
| amplicons.bed | A bed file showing the amplicon location compared to the consensus sequence. |
| per_base_mismatches.pdf | Barplot of the percent mismatches at each nucleotide position of the primer. |
| primer_to_amplicon_assignments.tabular | Simple tab separated file, which primers belong together. Useful for bioinformatic workflows that include primer trimming |
| primers.bed | A bed file with the primer locations. Includes the primer score. The lower, the better. |
| primer.tsv | A tab separated file with important parameters for the primers including the sequence with ambiguous nucleotides (already in the right strand) and the gc and temperature of the best fitting primer as well as for the mean for all permutations of the primer. |
| unsolvable_primer_dimers.tsv | Only produced if there are primer dimers without replacements. Tells which primers form dimers and at which temperature.
| varvamp_log.txt | Log file. |


It also produces some secondary output files [*data/*]:

| Output | Description |
| --- | --- |
| alignment_cleaned | The preprocessed alignment. |
| all_primers.bed | A bed file with all high scoring primers that varVAMP found. |
| conserved_regions.bed | A bed file showing where the conserved regions lie on the ambiguous consensus. |
| majority_consensus.fasta | Consensus sequence that does not have ambiguous characters but instead has the most prevalent nucleotide at each position. |

#### [Previous: Usage](./usage.md)&emsp;&emsp;[Next: How varVAMP works](./how_varvamp_works.md)
