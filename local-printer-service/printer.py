import os
import re
import platform
import subprocess
import tempfile


def extract_invoice_no(text):
    """
    Reads:
    Bill No: OOR-202606-0F6E81F8
    """
    match = re.search(r"Bill\s*No\s*:\s*([^\r\n]+)", text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def build_barcode(invoice_no):
    """
    ESC/POS CODE128 Barcode
    Compatible with ST-500 / EOS Santek
    """

    payload = b""

    # Center
    payload += b"\x1b\x61\x01"

    # Print text below barcode
    payload += b"\x1d\x48\x02"

    # Font A
    payload += b"\x1d\x66\x00"

    # Barcode Width
    payload += b"\x1d\x77\x03"

    # Barcode Height
    payload += b"\x1d\x68\x50"

    # CODE128
    barcode = b"{B" + invoice_no.encode("ascii", "ignore")

    payload += b"\x1d\x6b\x49"
    payload += bytes([len(barcode)])
    payload += barcode

    payload += b"\n"

    # Back to Left Align
    payload += b"\x1b\x61\x00"

    return payload


def insert_barcode(text):
    invoice = extract_invoice_no(text)

    if not invoice:
        return text.encode("utf-8")

    lines = text.splitlines()

    payload = b""

    inserted = False

    for line in lines:

        payload += (line + "\n").encode("utf-8")

        if (
            not inserted
            and line.lower().startswith("bill no")
        ):
            payload += build_barcode(invoice)
            inserted = True

    return payload


def print_bill(text: str, config: dict):

    mode = config.get("PRINT_MODE", "windows_raw")

    printer_name = config.get(
        "WINDOWS_PRINTER_NAME",
        config.get("PRINTER_NAME", "POS90"),
    )

    if config.get("DRY_RUN", False):
        print("--- DRY RUN PRINT ---")
        print(text)
        print("--- END PRINT ---")
        return

    if (
        platform.system().lower().startswith("win")
        and mode == "windows_raw"
    ):

        try:
            import win32print

            hprinter = win32print.OpenPrinter(printer_name)

            try:

                win32print.StartDocPrinter(
                    hprinter,
                    1,
                    ("Oorvashee Bill", None, "RAW"),
                )

                win32print.StartPagePrinter(hprinter)

                payload = insert_barcode(text)

                # Feed paper
                payload += b"\n\n\n"

                # Full Cut
                payload += b"\x1d\x56\x00"

                win32print.WritePrinter(hprinter, payload)

                win32print.EndPagePrinter(hprinter)

                win32print.EndDocPrinter(hprinter)

            finally:
                win32print.ClosePrinter(hprinter)

            return

        except ImportError:
            raise RuntimeError(
                "pywin32 missing. Run: pip install pywin32"
            )

    # Fallback Printing
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".txt",
        mode="w",
        encoding="utf-8",
    ) as f:
        f.write(text)
        path = f.name

    try:
        if platform.system().lower().startswith("win"):
            os.startfile(path, "print")
        else:
            subprocess.run(["lp", path], check=True)
    finally:
        pass
