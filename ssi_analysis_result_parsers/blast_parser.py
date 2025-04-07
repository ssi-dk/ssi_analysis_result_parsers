# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/39_Legionella_parser.ipynb.

# %% auto 0
__all__ = ['presence_absence', 'allele_matches']

# %% ../nbs/39_Legionella_parser.ipynb 3
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

# %% ../nbs/39_Legionella_parser.ipynb 9
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
    config_file: str = None,  # config file to set env vars from
) -> None:
    """ """
    # config = core.get_config(config_file)  # Set env vars and get config variables
    allele_dict = extract_allele_matches(
        blast_output_tsv=blast_output,
        tsv_header=blast_tsv_header,
        include_match_stats=include_match_stats,
    )
