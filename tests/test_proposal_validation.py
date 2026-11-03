
from copy import deepcopy

from tinyguard.remediation import validate_proposal


VALID_PROPOSAL = {
    "explanation": "The orders module depends on the database module.",
    "files_to_change": ["logic/orders.py"],
    "patch_strategy": "Remove the forbidden database dependency.",
    "confidence": 0.8,
    "missing_context": [],
    "file_contents": {
        "logic/orders.py": "def get_orders():\n    return []\n",
    },
}


def test_valid_proposal():
    result = validate_proposal(deepcopy(VALID_PROPOSAL))
    assert result["confidence"] == 0.8
    print("PASS: Valid proposal accepted.")


def test_missing_key_rejected():
    proposal = deepcopy(VALID_PROPOSAL)
    del proposal["confidence"]

    try:
        validate_proposal(proposal)
    except ValueError:
        pass
    else:
        raise AssertionError("Proposal missing confidence was accepted.")

    print("PASS: Missing required key rejected.")


def test_invalid_confidence_rejected():
    for confidence in (True, -0.1, 1.1, float("nan"), float("inf")):
        proposal = deepcopy(VALID_PROPOSAL)
        proposal["confidence"] = confidence

        try:
            validate_proposal(proposal)
        except ValueError:
            continue

        raise AssertionError(
            f"Invalid confidence {confidence!r} was accepted."
        )

    print("PASS: Invalid confidence values rejected.")


def test_unsafe_paths_rejected():
    for filepath in ("../outside.py", "/tmp/outside.py", r"..\outside.py"):
        proposal = deepcopy(VALID_PROPOSAL)
        proposal["files_to_change"] = [filepath]
        proposal["file_contents"] = {filepath: "print('unsafe')\n"}

        try:
            validate_proposal(proposal)
        except ValueError:
            continue

        raise AssertionError(f"Unsafe path {filepath!r} was accepted.")

    print("PASS: Unsafe file paths rejected.")


def test_empty_file_list_rejected():
    proposal = deepcopy(VALID_PROPOSAL)
    proposal["files_to_change"] = []
    proposal["file_contents"] = {}

    try:
        validate_proposal(proposal)
    except ValueError:
        pass
    else:
        raise AssertionError("Empty file list was accepted.")

    print("PASS: Empty file list rejected.")


def test_mismatched_file_contents_rejected():
    proposal = deepcopy(VALID_PROPOSAL)
    proposal["file_contents"] = {"api.py": "print('wrong target')\n"}

    try:
        validate_proposal(proposal)
    except ValueError:
        pass
    else:
        raise AssertionError("Mismatched file contents were accepted.")

    print("PASS: Mismatched file contents rejected.")


if __name__ == "__main__":
    test_valid_proposal()
    test_missing_key_rejected()
    test_invalid_confidence_rejected()
    test_unsafe_paths_rejected()
    test_empty_file_list_rejected()
    test_mismatched_file_contents_rejected()
    print("\nAll proposal validation tests passed.")
