import subprocess
import sys
from pathlib import Path


DATA_FOLDER = Path("data")
INGEST_SCRIPT = Path("ingest.py")


def get_pdf_files() -> list[Path]:
    """
    Return all PDF files inside the data folder,
    sorted alphabetically.
    """

    if not DATA_FOLDER.exists():
        raise FileNotFoundError(
            f"Data folder not found: {DATA_FOLDER.resolve()}"
        )

    return sorted(
        file
        for file in DATA_FOLDER.iterdir()
        if file.is_file()
        and file.suffix.lower() == ".pdf"
    )


def ingest_pdf(pdf_path: Path) -> bool:
    """
    Run ingest.py for one PDF.

    Returns True if ingestion succeeds,
    otherwise False.
    """

    print()
    print("=" * 70)
    print(f"Ingesting: {pdf_path.name}")
    print("=" * 70)

    result = subprocess.run(
        [
            sys.executable,
            str(INGEST_SCRIPT),
            str(pdf_path),
        ]
    )

    if result.returncode == 0:
        print()
        print(f"✓ Successfully ingested: {pdf_path.name}")
        return True

    print()
    print(f"✗ Failed to ingest: {pdf_path.name}")

    return False


def main() -> None:

    if not INGEST_SCRIPT.exists():
        print(
            f"Could not find ingest script: "
            f"{INGEST_SCRIPT.resolve()}"
        )
        sys.exit(1)

    try:
        pdf_files = get_pdf_files()

    except FileNotFoundError as error:
        print(error)
        sys.exit(1)

    if not pdf_files:
        print(
            f"No PDF files found in "
            f"{DATA_FOLDER.resolve()}"
        )
        return

    print(
        f"Found {len(pdf_files)} PDF file(s):"
    )

    for pdf in pdf_files:
        print(f"  - {pdf.name}")

    successful = []
    failed = []

    for pdf in pdf_files:

        if ingest_pdf(pdf):
            successful.append(pdf.name)
        else:
            failed.append(pdf.name)

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("INGESTION SUMMARY")
    print("=" * 70)

    print(
        f"Total:      {len(pdf_files)}"
    )

    print(
        f"Successful: {len(successful)}"
    )

    print(
        f"Failed:     {len(failed)}"
    )

    if failed:
        print()
        print("Failed files:")

        for filename in failed:
            print(f"  - {filename}")

        sys.exit(1)

    print()
    print("All papers successfully ingested.")


if __name__ == "__main__":
    main()