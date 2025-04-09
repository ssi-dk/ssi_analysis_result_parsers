# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/11_blast_parser.ipynb.

# %% auto 0
__all__ = ['extract_presence_absence', 'extract_allele_matches', 'presence_absence', 'allele_matches']

# %% ../nbs/11_blast_parser.ipynb 3
# standard libs
import os
import re

# Common to template
# add into settings.ini, requirements, package name is python-dotenv, for conda build ensure `conda config --add channels conda-forge`
import dotenv  # for loading config from .env files, https://pypi.org/project/python-dotenv/
import envyaml  # Allows to loads env vars into a yaml file, https://github.com/thesimj/envyaml
import fastcore  # To add functionality related to nbdev development, https://github.com/fastai/fastcore/
from fastcore import (
    test,
)
from fastcore.script import (
    call_parse,
)  # for @call_parse, https://fastcore.fast.ai/script
import json  # for nicely printing json and yaml

# import functions from core module (optional, but most likely needed).
from . import core

# Project specific libraries
from pathlib import Path
import pandas
import sys

# %% ../nbs/11_blast_parser.ipynb 6
def extract_presence_absence(
    blast_output_tsv: Path,
    tsv_header: str = "qseqid sseqid pident length qlen qstart qend sstart send sseq evalue bitscore",
    hits_as_string: bool = True,
    include_match_stats=False,
    pident_threshold: float = 90,
    plen_threshold: float = 60,
    gene_names: list = None,
) -> dict:
    """
    Parse blast output tsv for best matching alleles
    returns:
    if include_match stats:
        { <gene_name_1>: <allele_number>,  <gene_name_2>: <allele_number>,  <gene_name_3>: <allele_number> ...}
    else:
        a dictionary (allele_dict) in the format { <gene_name_1>: <allele_number>,  <gene_name_2>: <allele_number>,  <gene_name_3>: <allele_number> ...}

    """
    if os.path.exists(blast_output_tsv):
        try:
            blast_df = pandas.read_csv(blast_output_tsv, sep="\t", header=None)

            blast_df.columns = tsv_header.split(" ")
            blast_df["plen"] = blast_df["length"] / blast_df["qlen"] * 100
            blast_df_unique = (
                blast_df.sort_values(by=["bitscore"], ascending=False)
                .groupby("qseqid")
                .first()
            )
            blast_df_filtered = blast_df_unique.query(
                "plen > @plen_threshold and pident > @pident_threshold"
            )
            blast_dict = dict(blast_df_filtered.to_dict(orient="index"))
        except pandas.errors.EmptyDataError:
            blast_dict = {}
        if hits_as_string:
            if include_match_stats:
                results = []
                for gene, d in blast_dict.items():
                    results.append(f"{gene}__{d['pident']}__{d['plen']}")
                result_dict = {"genes_found": ", ".join(results)}
                return result_dict

            else:
                result_dict = {
                    "genes_found": ", ".join(list(blast_df_filtered.index.values))
                }
                return result_dict

        else:
            result_dict = {}
            if gene_names is None:
                gene_names = blast_dict.keys()
            for gene in gene_names:
                if gene in blast_dict:
                    if include_match_stats:
                        result_dict[gene] = (
                            f"{blast_dict[gene]['pident']}__{blast_dict[gene]['plen']}"
                        )
                    else:
                        result_dict[gene] = "1"
                else:
                    result_dict[gene] = "0"
            return result_dict

    else:
        print(f"No blast output found at {blast_output_tsv}", file=sys.stderr)


def extract_allele_matches(
    blast_output_tsv: Path, tsv_header: str, include_match_stats=False
) -> dict:
    """
    Parse blast output tsv for best matching alleles
    returns:
    if include_match stats:
        { <gene_name_1>: <allele_number>__<pident>__<plen>,  <gene_name_2>: <allele_number>__<pident>__<plen>,  <gene_name_3>: <allele_number>__<pident>__<plen> ...}
    else:
        a dictionary (allele_dict) in the format { <gene_name_1>: <allele_number>,  <gene_name_2>: <allele_number>,  <gene_name_3>: <allele_number> ...}

    """
    allele_dict = {}
    detailed_dict = {}
    if os.path.exists(blast_output_tsv):
        blast_df = pandas.read_csv(blast_output_tsv, sep="\t", header=None)
        blast_df.columns = tsv_header.split(" ")
        blast_df.set_index("qseqid", drop=False)
        blast_df["plen"] = blast_df["length"] / blast_df["qlen"] * 100
        blast_df[["gene", "allele"]] = blast_df["qseqid"].str.split("_", expand=True)
        blast_df_unique = (
            blast_df.sort_values(by=["bitscore"], ascending=False)
            .groupby("gene")
            .first()
        )
        for gene, d in blast_df_unique.to_dict(orient="index").items():
            allele_dict[gene] = d["allele"]
            detailed_dict[gene] = f"{d['allele']}__{d['pident']}__{d['plen']}"
    else:
        print(f"No blast output found at {blast_output_tsv}", file=sys.stderr)

    if include_match_stats:
        return detailed_dict
    else:
        return allele_dict

# %% ../nbs/11_blast_parser.ipynb 9
from fastcore.script import call_parse


@call_parse
def presence_absence(
    blast_output: Path = None,  # Path to blast output file. Generated with --outfmt 6 option
    blast_tsv_header: str = "qseqid sseqid pident length qlen qstart qend sstart send sseq evalue bitscore",  # headers in blast output
    hits_as_string: bool = True,  # True to print a comma separated list of found genes on a single line. False to return a key: value pair for each gene
    include_match_stats: bool = False,  # True to include percent identity and percent length in output, false to only include present/absent
    percent_identityt: float = 90,  # percent identity threshold for considering a gene present
    percent_length: float = 60,  # percent length threshold for considering a gene present
    gene_names: list = None,  # name of genes to look for when hits_as_string = False
    output_file: Path = None,
    config_file: str = None,  # config file to set env vars from
) -> None:
    """ """
    # config = core.get_config(config_file)  # Set env vars and get config variables
    gene_presence_dict = extract_presence_absence(
        blast_output_tsv=blast_output,
        tsv_header=blast_tsv_header,
        hits_as_string=hits_as_string,
        include_match_stats=include_match_stats,
        pident_threshold=percent_identityt,
        plen_threshold=percent_length,
        gene_names=gene_names,
    )


@call_parse
def allele_matches(
    blast_output: Path = None,  # Path to blast output file. Generated with --outfmt 6 option
    blast_tsv_header: str = "qseqid sseqid pident length qlen qstart qend sstart send sseq evalue bitscore",  # headers in blast output
    include_match_stats: bool = False,  # True to include percent identity and percent length in output, false to only include allele number
    output_file: Path = None,
    config_file: str = None,  # config file to set env vars from
) -> None:
    """ """
    # config = core.get_config(config_file)  # Set env vars and get config variables
    allele_dict = extract_allele_matches(
        blast_output_tsv=blast_output,
        tsv_header=blast_tsv_header,
        include_match_stats=include_match_stats,
        output_file=None,
    )
