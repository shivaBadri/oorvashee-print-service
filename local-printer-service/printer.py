import os
import platform
import subprocess
import tempfile


def print_bill(text: str, config: dict):
    mode = config.get('PRINT_MODE', 'windows_raw')
    printer_name = config.get('WINDOWS_PRINTER_NAME', config.get('PRINTER_NAME', 'POS90'))

    if config.get('DRY_RUN', False):
        print('--- DRY RUN PRINT ---')
        print(text)
        print('--- END PRINT ---')
        return

    if platform.system().lower().startswith('win') and mode == 'windows_raw':
        try:
            import win32print
            hprinter = win32print.OpenPrinter(printer_name)
            try:
                job = win32print.StartDocPrinter(hprinter, 1, ('Oorvashee Bill', None, 'RAW'))
                win32print.StartPagePrinter(hprinter)
                payload = text.encode('utf-8') + b'\n\n\n\x1d\x56\x00'  # feed + cut
                win32print.WritePrinter(hprinter, payload)
                win32print.EndPagePrinter(hprinter)
                win32print.EndDocPrinter(hprinter)
            finally:
                win32print.ClosePrinter(hprinter)
            return
        except ImportError:
            raise RuntimeError('pywin32 missing. Run: pip install pywin32')

    # Fallback: write text file and send to OS print command
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8') as f:
        f.write(text)
        path = f.name
    try:
        if platform.system().lower().startswith('win'):
            os.startfile(path, 'print')
        else:
            subprocess.run(['lp', path], check=True)
    finally:
        pass
