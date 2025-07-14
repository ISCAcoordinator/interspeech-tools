import pathlib
import subprocess

import pylatex

SUPPORTED_COMPILATION_TOOLS = ["latexmk", "lualatex"]


def latexify(input: str | None) -> str:
    """Convert a given string to a LaTeX compatible string

    Parameters
    ----------
    input : str, optional
        The given string

    Returns
    -------
    str
        The LaTeX compatible string

    """
    input = "" if input is None else input
    if input.strip() == "":
        return input

    input = input.replace("\n\n", "\n")
    input = pylatex.utils.escape_latex(input)
    return input


def is_tool(tool_name: str) -> bool:
    """Check if the given tool name is refers to an existing tool

    Parameters
    ----------
    tool_name : str
        The tool name

    Returns
    -------
    bool
        True if the name refers to an existing tool, False else

    """

    # from whichcraft import which
    from shutil import which

    return which(tool_name) is not None


def compile(main_file: pathlib.Path, tool: str = "latexmk"):
    """Compile the given main LaTeX file using the given tool

    latexmk will be prioritize as it aims to use the full sequence.
    If using lualatex, it will compile only once and therefore references won't be resolved

    Parameters
    ----------
    main_file : pathlib.Path
        the main LaTeX file
    tool : str
        The tool to run to compile

    Raises
    ------
    Exception
        if the tool is invalid or no tools are available

    """
    if (tool != "auto") and (not is_tool(tool)):
        raise Exception(f"{tool} is not available")

    if (tool != "auto") and (not tool in SUPPORTED_COMPILATION_TOOLS):
        raise Exception(f'The tool "{tool}" is not supported. Only latexmk and lualatex are supported.')

    if tool == "auto":
        i_tool = 0
        tool = SUPPORTED_COMPILATION_TOOLS[i_tool]
        while (not is_tool(tool)) and (i_tool < (len(SUPPORTED_COMPILATION_TOOLS) - 1)):
            i_tool += 1
            tool = SUPPORTED_COMPILATION_TOOLS[i_tool]

        if not is_tool(tool):
            raise Exception("There is not compatible latex compilation tools")

    # Now execute
    workdir = main_file.parent
    if tool == "latexmk":
        p = subprocess.Popen(["latexmk", "-pdflatex=lualatex", "-pdf", main_file.name], cwd=workdir)
        p.wait()
    elif tool == "lualatex":
        for _ in range(2):
            p = subprocess.Popen(["lualatex", main_file.name], cwd=workdir)
            p.wait()
    else:
        raise Exception(
            "There is no compatible latex tools (lualatex needs to be available at a minimum; "
            + "pdflatex and xelatex are not supported)"
        )
