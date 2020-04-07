#!/usr/bin/python3
import os
import subprocess
import re


def get_text_of_pdf(filename):
    return subprocess.check_output(["pdftotext", filename, "-"]).decode("utf-8")


def identify_sheet(filename):
    lines = get_text_of_pdf(filename).splitlines()
    regexes = {
        "gls": r'č. krab. ([0-9]*).*',
        "team": r'.*Do krab. č.: ([0-9]*).*',
    }
    for line in lines:
        for stype, regex in regexes.items():
            match = re.search(regex, line)
            if match:
                return stype, match.group(1)


def rename_sheet(filename):
    stype, num = identify_sheet(filename)
    os.rename(
        filename,
        os.path.join(
            os.path.dirname(filename),
            num + "-" + stype + ".pdf"
        )
    )
