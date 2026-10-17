"""Word error accounting for complete, human-confirmed references only."""

import re


def tokens(text):
    # No slide/slides, phonetic, or digit substitutions: errors stay visible.
    return re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?", text.lower())


def word_errors(reference, hypothesis):
    ref, hyp = tokens(reference), tokens(hypothesis)
    if not ref:
        raise ValueError("WER requires a nonempty reference")
    # Cells hold distance, substitutions, deletions, insertions. Prefer
    # substitutions on ties so reporting is deterministic.
    previous = [(j, 0, 0, j) for j in range(len(hyp) + 1)]
    for i, expected in enumerate(ref, 1):
        current = [(i, 0, i, 0)]
        for j, actual in enumerate(hyp, 1):
            if expected == actual:
                current.append(previous[j - 1])
                continue
            d, s, delete, insert = previous[j - 1]
            sub = (d + 1, s + 1, delete, insert)
            d, s, delete, insert = previous[j]
            removal = (d + 1, s, delete + 1, insert)
            d, s, delete, insert = current[j - 1]
            addition = (d + 1, s, delete, insert + 1)
            current.append(min((sub, removal, addition), key=lambda cell: cell[0]))
        previous = current
    errors, substitutions, deletions, insertions = previous[-1]
    return {"reference_words": len(ref), "substitutions": substitutions,
            "deletions": deletions, "insertions": insertions,
            "errors": errors, "wer": errors / len(ref)}
