"""Shell-command parsing shared by the hooks that inspect a Bash tool command.

Splits a command into its simple commands with the directory each one runs in, resolves the
directory and subcommand of a `git` invocation, and works out the directory a shell is left in
after a command. Standard library only.
"""

import os
import re
import shlex


def _tokens_of(part):
    try:
        return shlex.split(part)
    except ValueError:
        return part.split()


def segments_with_directory(command, cwd):
    """Split a shell command into its simple commands, each with the directory it runs in.

    Splits on &&, ||, ;, | and newlines; tokenizes each part with shlex (falling back to
    str.split on a shlex error); drops leading VAR=value assignments. A `cd <dir>` part changes
    the directory for the parts after it (relative to the current one, ~ expanded) and is not
    itself returned. Empty parts are dropped.
    """
    directory = cwd
    result = []
    for part in re.split(r"&&|\|\||;|\||\n", command):
        part = part.strip()
        if not part:
            continue
        tokens = _tokens_of(part)
        if len(tokens) >= 2 and tokens[0] == "cd":
            directory = os.path.join(directory, os.path.expanduser(tokens[1]))
            continue
        while tokens and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
            tokens = tokens[1:]
        if tokens:
            result.append((tokens, directory))
    return result


def git_target(tokens, directory):
    """For a `git ...` command: the directory it acts on and the arguments from the subcommand on.

    Applies every `-C <dir>` (relative to `directory`), skips `-c <key=value>` and other leading
    options. Returns None when tokens[0] is not `git`. Example:
    git_target(["git", "-C", "R", "commit", "-m", "x"], "/a") == ("/a/R", ["commit", "-m", "x"])
    """
    if not tokens or tokens[0] != "git":
        return None
    rest, i = tokens[1:], 0
    while i < len(rest) and rest[i].startswith("-"):
        if rest[i] == "-C" and i + 1 < len(rest):
            directory = os.path.join(directory, rest[i + 1])
            i += 1
        elif rest[i] == "-c":
            i += 1
        i += 1
    return directory, rest[i:]


_SEPARATOR_CHARS = set(";&|()")
_KEYWORDS = {"if", "then", "elif", "else", "while", "until", "do", "{", "!", "time"}
_DIRECTORY_COMMANDS = {"cd", "pushd", "popd"}


def _is_operator(token, lexer):
    return bool(token) and all(c in lexer.punctuation_chars for c in token)


def persistent_directory(command, cwd):
    """The directory a shell is left in after running `command` in `cwd`.

    Counts only a `cd` or `pushd` at the top level: one inside `( … )` or `$( … )` runs in a
    subshell and leaves the shell where it was. `cd` with no argument goes to ~. Returns None
    when a top-level change cannot be resolved without running the command: `popd`, `cd -`, or
    a target with `$` or a backquote. Quoting is respected; a heredoc body is not recognised.
    """
    lexer = shlex.shlex(command.replace("\n", " ; "), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:
        return None
    directory, depth, at_start, i = cwd, 0, True, 0
    while i < len(tokens):
        token = tokens[i]
        i += 1
        if _is_operator(token, lexer):
            depth += token.count("(") - token.count(")")
            at_start = any(c in _SEPARATOR_CHARS for c in token)
            continue
        if not at_start or depth > 0 or token not in _DIRECTORY_COMMANDS:
            at_start = at_start and token in _KEYWORDS
            continue
        at_start = False
        args = []
        while i < len(tokens) and not _is_operator(tokens[i], lexer):
            args.append(tokens[i])
            i += 1
        if token == "popd":
            return None
        targets = [a for a in args if not a.startswith("-") or a == "-"]
        target = targets[0] if targets else "~"
        if target == "-" or "$" in target or "`" in target:
            return None
        directory = os.path.normpath(os.path.join(directory, os.path.expanduser(target)))
    return directory
