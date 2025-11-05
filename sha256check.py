# Refs: https://gist.github.com/airtower-luna/a5df5d6143c8e9ffe7eb5deb5797a0e0
import hashlib
import os.path
import re

# This regular expression matches a line containing a hexadecimal
# hash, spaces, and a filename. Parentheses create capturing groups.
r = re.compile(r'(^[0-9A-Fa-f]+)\s+(\S.*)$')


def check(filename: str, expect: str, find_dir: str = ".") -> bool:
    """
    Compute the SHA-256 hash of a file and compare it to an expected hash value.

    This function reads the contents of the specified file in chunks, computes
    its SHA-256 hash, and verifies if the resulting hash matches the provided
    expected value. It ensures memory usage is efficient by reading the file in
    4KB chunks.

    :param filename: The name of the file to be hashed.
    :param expect: The expected SHA-256 hash value to compare against.
    :param find_dir: The directory where the file is located. Defaults to the
        current directory.
    :return: True if the computed hash matches the expected hash, False otherwise.
    """
    h = hashlib.sha256()
    # This will raise an exception if the file doesn't exist. Catching
    # and handling it is left as an exercise for the reader.
    with open(os.path.join(find_dir, filename), 'rb') as fh:
        # Read and hash the file in 4K chunks. Reading the whole
        # file at once might consume a lot of memory if it is
        # large.
        while True:
            data = fh.read(4096)
            if len(data) == 0:
                break
            else:
                h.update(data)
    return expect == h.hexdigest()


def hash_file_check(filename: str, find_dir: str = ".") -> bool:
    """
    Checks if a file contains valid hash entries and verifies the integrity of related files in a specified directory.

    This function reads a file line by line, expecting each line to match a specific format for hash values and file
    names. For each line, it validates the format and checks the hash of the corresponding file against the given hash.
    If any validation fails, the function returns False. If all validations succeed, it returns True.

    :param filename: The name of the file containing hash entries to be checked.
    :param find_dir: The directory to search for the file and validate the integrity of related files. Defaults to the 
        current directory (".").
    :return: A boolean value indicating whether all lines in the file are valid and all associated files pass the 
        checksum validation. Returns True if validation is successful, otherwise False.
    """
    with open(os.path.join(find_dir, filename), 'r') as fh:
        for line in fh:
            is_match = r.match(line)
            if not is_match:
                return False
            checksum = is_match.group(1)
            filename = is_match.group(2)
            if not check(filename, checksum, find_dir):
                return False
        return True
