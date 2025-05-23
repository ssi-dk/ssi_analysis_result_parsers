# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/37_Nmeningitidis_parser.ipynb.

# %% auto 0
__all__ = ['extract_meningotype', 'extract_cc_from_mlst', 'NmeningitidisResults', 'Nmeningitidis_parser',
           'Nmeningitidis_batch_parser']

# %% ../nbs/37_Nmeningitidis_parser.ipynb 3
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
from ssi_analysis_result_parsers import (
    core,
    blast_parser,
)

# from ssi_analysis_result_parsers.blast_parser import extract_presence_absence

# Project specific libraries
from pathlib import Path
import pandas
import numpy
import sys

# %% ../nbs/37_Nmeningitidis_parser.ipynb 6
def extract_meningotype(meningotype_tsv: Path):
    if meningotype_tsv.exists():
        try:
            df = pandas.read_csv(meningotype_tsv, sep="\t")
            if df.shape[0] > 0:
                PorA_split = df.iloc[0]["PorA"].split(",")
                VR1 = PorA_split[0]
                try:
                    VR2 = PorA_split[1]
                except:
                    VR2 = ""
                return {
                    "SEROGROUP": df.iloc[0]["SEROGROUP"],
                    "VR1": VR1,
                    "VR2": VR2,
                    "FetA": df.iloc[0]["FetA"],
                }
            else:
                print(
                    f"Meningotype output file empty at {meningotype_tsv}",
                    file=sys.stderr,
                )
                return None
        except pandas.errors.EmptyDataError:
            print(
                f"Meningotype output file empty at {meningotype_tsv}", file=sys.stderr
            )
            return None
    else:
        print(f"No meningotype output found at {meningotype_tsv}", file=sys.stderr)
        return None

    return None


def extract_cc_from_mlst(
    MLST: str,
    mlst_scheme_tsv: Path = "/users/data/Projects/MICROBIAL_SURVEILLANCE/Resources/Databases/mlst/neisseria/neisseria.txt",
):
    CC = {"CC": ""}
    if mlst_scheme_tsv.exists():
        try:
            with open(mlst_scheme_tsv) as f:
                for line in f:
                    line = line.strip("\n").split("\t")
                    if line[0] == MLST:
                        if line[8][:3] == "ST-":
                            CC["CC"] = line[8].split(" ")[0][3:]
                        return CC
        except Exception as e:
            CC["CC"] = f"Failed to load mlst scheme tsv: {e}"
    else:
        CC["CC"] = "Failed to load mlst scheme tsv, file not found"
    return CC


class NmeningitidisResults(core.PipelineResults):

    @classmethod
    def from_tool_paths(
        cls, meningotype_tsv: Path, MLST: str, mlst_scheme_tsv: Path, sample_name=None
    ):
        """
        Alternative constructor for initializing results for single sample,
        Initializes NmeningitidisResults instance provided paths to outputs from tools (legionella sbt and lag1 presence blast)
        """
        mgk_results = cls.summary(
            meningotype_tsv=Path(meningotype_tsv),
            MLST=MLST,
            mlst_scheme_tsv=Path(mlst_scheme_tsv),
        )
        return cls({sample_name: mgk_results})

    @classmethod
    def from_tool_paths_dict(cls, file_paths: dict):
        """
        Alternative constructor for initializing results for multiple samples,
        Initializes NmeningitidisResults instance by providing a dictionary of paths to outputs from tools (legionella sbt and lag1 presence blast)
        """
        results_dict = {}
        for sample_name, path_dict in file_paths.items():
            mgk_results = cls.summary(
                meningotype_tsv=Path(path_dict["meningotype_results"]),
                MLST=path_dict["MLST"],
                mlst_scheme_tsv=path_dict["mlst_scheme_tsv"],
            )
            results_dict[sample_name] = mgk_results
        return cls(results_dict)

    @classmethod
    def from_tool_paths_dataframe(cls, file_paths_df: pandas.DataFrame):
        """
        Alternative constructor for initializing results for multiple samples,
        Initializes NmeningitidisResults instance by providing a DataFrame of paths to outputs from tools (legionella sbt and lag1 presence blast)
        """
        file_paths = file_paths_df.to_dict(orient="index")

        return cls.from_tool_paths_dict(file_paths=file_paths)

    @classmethod
    def from_tool_paths_tsv(cls, tool_paths_tsv: Path):
        """
        Alternative constructor for initializing results for multiple samples,
        Initializes NmeningitidisResults instance by providing a tsv-file with paths to outputs from tools (legionella sbt and lag1 presence blast)
        """
        file_paths_df = pandas.read_csv(tool_paths_tsv, sep="\t")
        file_paths_df.set_index("sample_name", inplace=True, drop=True)
        return cls.from_tool_paths_dataframe(file_paths_df)

    @staticmethod
    def summary(meningotype_tsv: Path, MLST: str, mlst_scheme_tsv: Path) -> dict:
        meningotype_results = extract_meningotype(meningotype_tsv=Path(meningotype_tsv))
        results_dict = meningotype_results
        cc_dict = extract_cc_from_mlst(MLST=MLST, mlst_scheme_tsv=Path(mlst_scheme_tsv))
        results_dict = core.update_results_dict(
            results_dict, cc_dict, old_duplicate_key_prefix="Clonal_complex: "
        )
        if results_dict is None:
            return {}
        return results_dict

    def __repr__(self):
        return f"< Spyogenes analysis results object. {len(self.results_df)} samples with {len(self.results_df.columns)} result variables > "

# %% ../nbs/37_Nmeningitidis_parser.ipynb 9
@call_parse
def Nmeningitidis_parser(
    meningotype_tsv: Path = None,  # Blast output from blasting EMM and emm-like genes
    MLST: str = None,  # MLST to deduce Clonal complex from
    mlst_scheme_tsv: Path = None,  # Path to pubmlst scheme for neisseria for MLST: CC table
    sample_name: str = None,
    output_file: Path = None,
) -> None:
    """ """
    results = NmeningitidisResults.from_tool_paths(
        meningotype_tsv=meningotype_tsv,
        MLST=MLST,
        mlst_scheme_tsv=mlst_scheme_tsv,
        sample_name=sample_name,
    )
    results.write_tsv(output_file=output_file)


@call_parse
def Nmeningitidis_batch_parser(
    file_path_tsv: Path = None,  # Path to tsv containing file paths to the outputs from tools to be parsed. Must contain headers "sample_name", "sbt_results", and "lag1_blast_results"
    output_file: Path = None,  # Path to output tsv
) -> None:
    """ """
    results = NmeningitidisResults.from_tool_paths_tsv(tool_paths_tsv=file_path_tsv)
    results.write_tsv(output_file)
