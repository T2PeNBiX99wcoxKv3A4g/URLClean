# Refs: https://gist.github.com/airtower-luna/a5df5d6143c8e9ffe7eb5deb5797a0e0
import hashlib
import re

# This regular expression matches a line containing a hexadecimal
# hash, spaces, and a filename. Parentheses create capturing groups.
r = re.compile(r'(^[0-9A-Fa-f]+)\s+(\S.*)$')


def check(filename: str, expect: str) -> bool:
    """Check if the file with the name "filename" matches the SHA-256 sum
    in "expect"."""
    h = hashlib.sha256()
    # This will raise an exception if the file doesn't exist. Catching
    # and handling it is left as an exercise for the reader.
    with open(filename, 'rb') as fh:
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


def hash_file_check(filename: str) -> bool:
    with open(filename, 'r') as fh:
        for line in fh:
            is_match = r.match(line)
            if not is_match:
                return False
            checksum = is_match.group(1)
            filename = is_match.group(2)
            if not check(filename, checksum):
                return False
        return True
