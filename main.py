import argparse
import sys
from agents.orchestrator import Orchestrator

def main():
    parser = argparse.ArgumentParser(description="Invoice AI Processing System")
    parser.add_argument("--invoice_path", required=True, help="Path to the invoice file (PDF, TXT, CSV, JSON)")
    args = parser.parse_args()

    orchestrator = Orchestrator()
    result = orchestrator.run(args.invoice_path)

    print("\n" + "=" * 40)
    print("FINAL STATUS: %s" % result["status"])
    print("=" * 40)

    if result.get("error"):
        print("Error: %s" % result["error"])

    if result.get("decision"):
        print("Reasoning: %s" % result["decision"].reasoning)

    if result.get("payment"):
        print("Payment Status: %s" % result["payment"].get("status"))
        if result["payment"].get("transaction_id"):
            print("Transaction ID: %s" % result["payment"].get("transaction_id"))

    if result["status"] == "REJECTED" and result.get("validation") and not result["validation"].is_valid:
        print("Validation Errors:")
        for err in result["validation"].errors:
            print("  - %s" % err)

    sys.exit(0 if result["status"] == "APPROVED" else 1)

if __name__ == "__main__":
    main()
