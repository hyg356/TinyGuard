
from tinyguard.remediation import propose_remediation


proposal = propose_remediation(
    violation="api -> logic.orders -> database",
    source_code={
        "api.py": "import logic.orders\n",
        "logic/orders.py": "import database\n",
        "database.py": "# database access\n",
    },
)

print("Model proposal:")
print(proposal["explanation"])
print("Files to change:", proposal["files_to_change"])
print("Patch strategy:", proposal["patch_strategy"])

assert proposal["explanation"]
assert proposal["patch_strategy"]
print("\nPASS: Local remediation proposal received and validated.")
