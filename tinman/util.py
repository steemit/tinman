
# Utility functions

import itertools
from tinman.simple_steem_client.simple_steem_client.client import SteemRemoteBackend, SteemInterface

def tag_escape_sequences(s, esc):
    """
    Example usage:

    >>> list(tag_escape_sequences('now "is" the time; "the hour" has "come"', '"'))
    [('now ', False), ('is', True), (' the time; ', False), ('the hour', True), (' has ', False), ('come', True), ('', False)]
    """
    return zip(s.split(esc), itertools.cycle([False, True]))

def batch(it, size=1):
    """
    Change iterable into batches

    Example usage:

    >>> list(util.batch("spamspam", 3))
    [['s', 'p', 'a'], ['m', 's', 'p'], ['a', 'm']]
    """
    b = []
    for e in it:
        b.append(e)
        if len(b) >= size:
            yield b
            b = []
    if len(b) > 0:
        yield b
    return

def find_non_substr(s, alphabet="abcdefghijklmnopqrstuvwxyz", start=""):
    """
    Find a string composed of characters from alphabet that does not occur in s.

    The strategy is a greedy algorithm, it initializes the result `r` to the least
    common character.  Then while `r` is in the string, iterate over each substring
    of the form `rx` where `x` is any single character.  Extend `r` by the least
    common value of `x` and continue until `r` is not in the string.
    """

    if start == "":
        # Initialize result to the least common character
        hist = {c : 0 for c in alphabet}
        for c in s:
            count = hist.get(c)
            if count is not None:
                hist[c] = count+1
        result = min(alphabet, key=lambda c : hist[c])
        # We might get lucky and find the message doesn't contain some character at all
        if hist[result] == 0:
            return result
    else:
        result = start

    m = len(result)
    n = len(s)
    while True:
        hist = {c : 0 for c in alphabet}
        current_pos = -1
        while True:
            found_pos = s.find(result, current_pos+1)
            # Look at the next character
            if found_pos < 0:
                break
            current_pos = found_pos
            # In the case where we found the string at the end of the string, the above
            # assignment will keep us from breaking out of the outer loop, but the
            # following check will avoid adding the next character to the histogram
            # (because there is no next character)
            if found_pos == n-m:
                break
            c = s[current_pos + m]
            count = hist.get(c)
            if count is not None:
                hist[c] = count+1
        if current_pos < 0:
           break
        result += min(alphabet, key=lambda c : hist[c])
        m += 1

    return result

def iterate_operations_from(node_server, is_appbase, min_block_number, max_block_number):
    """ Yields operations iterated from provided node's blocks """
    assert isinstance(node_server, str)
    assert isinstance(is_appbase, bool)
    assert isinstance(min_block_number, int)
    assert isinstance(max_block_number, int)
    backend = SteemRemoteBackend(nodes=[node_server], appbase=is_appbase)
    steemd = SteemInterface(backend)
    for block_num in range(min_block_number, max_block_number):
        print("Processing block no "+str(block_num))
        if is_appbase:
            another_block = steemd.block_api.get_block(block_num=block_num)
            if not another_block:
                print("No block retrieved when requested block no "+str(block_num))
                return
            actual_block = another_block["block"]
            block_transactions = actual_block["transactions"]
        else:
            another_block = steemd.block_api.get_block(block_num)
            if not another_block:
                print("No block retrieved when requested block no "+str(block_num))
                return
            block_transactions = another_block["transactions"]
        for another_transaction in block_transactions:
            transaction_operations = another_transaction["operations"]
            for another_operation in transaction_operations:
                yield another_operation
    return
