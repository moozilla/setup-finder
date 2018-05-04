"""Parse fumen specifications.

Based on reverse engineering source code from fumen v1.15a. This is only a partial implementation, will ignore mino placement and special functions (mirror, etc).
I only need to parse the field and comments for commmunicating with solution-finder/storing my own data.

(Todo: Look into --split option in sfinder, this might be useful later for determining pieces sequences that work for a paticular solution.
Might require parsing pieces as well.)
"""

FIELD_BLOCKS = 240  # number of blocks on field in fumen frame (24 rows of 10)
ENC_TABLE = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"  # used for pseudo-base64 decoding
ASC_TABLE = " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"  # for decoding comments


def data_to_field(field_data):
    """Convert raw field data into matrix representation."""
    # split into rows
    field = [field_data[i:i + 10] for i in range(0, FIELD_BLOCKS, 10)]
    BLANK_ROW = [0] * 10
    start = next((i for i, v in enumerate(field) if v != BLANK_ROW), None)
    if start is None:
        raise ValueError("Field is blank.")
    stripped = field[start:23]  # strip blank top rows and blank bottom row
    stripped.reverse()  # TetField stores rows in reverse order
    return [[1 if b > 0 else 0 for b in row] for row in stripped]
    """ return "\n".join([
        "".join(map(lambda b: "X" if b > 0 else "_", row)) for row in stripped
    ]) """


def parse(fumen_str):
    if fumen_str[:5] != "v115@":
        raise ValueError("Unsupported fumen version.")

    enc_data = fumen_str[5:]
    # need to strip ?, no clear reason why fumen even includes them (backwards compatibility maybe?)
    data = [ENC_TABLE.index(c) for c in enc_data.replace("?", "")]
    i = 0  # data pointer

    field = [0] * FIELD_BLOCKS
    j = 0
    while j < FIELD_BLOCKS:
        val = data[i] + (data[i + 1] * 64)
        i += 2
        run_len = (val % FIELD_BLOCKS) + 1
        block = ((val // FIELD_BLOCKS) % 17) - 8
        for _ in range(run_len):
            field[j] = block
            j += 1
        if block == 0 and run_len == (FIELD_BLOCKS - 1):
            raise NotImplementedError("Fumen includes repeated frames.")

    val = data[i] + (data[i + 1] * 64) + (data[i + 2] * 4096)
    i += 3
    # ignoring all piece/extra data parsing here
    tmp = val // (256 * FIELD_BLOCKS)
    comment_flag = tmp % 2
    # ignoring any sort of field copying (mirroring, rising, etc) - todo: raise exceptions

    if comment_flag == 1:
        comment_len = (data[i] + (data[i + 1] * 64)) % 4096
        i += 2
        comment = ""
        while len(comment) < comment_len:
            val = data[i] + (data[i + 1] * 64) + (data[i + 2] * 4096) + (
                data[i + 3] * 262144) + (data[i + 4] * 16777216)
            i += 5
            comment += ASC_TABLE[val % 96]
            val = val // 96
            comment += ASC_TABLE[val % 96]
            val = val // 96
            comment += ASC_TABLE[val % 96]
            val = val // 96
            comment += ASC_TABLE[val % 96]
            val = val // 96
        comment = comment[:comment_len]  # strip padding
        # note: fumen uses unescape to support unicode, but I'm not going to bother trying to simulate unescape
        # could potentially try urllib.parse.unquote + a regular expression to handle %uxxxx
    if len(data) - i > 0:
        raise NotImplementedError("Data remaining after first frame parsed.")
    return (data_to_field(field), comment)
