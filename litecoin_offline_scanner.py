import os
import sys
import time
import json
import gzip
import shutil
import urllib.request
from urllib.error import URLError
from pathlib import Path
from typing import Dict, Set, Optional
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, FileSizeColumn, TotalFileSizeColumn, TransferSpeedColumn
from libcrypto import Wallet


class Messages:
    _data: Dict = None
    
    @classmethod
    def _load(cls) -> None:
        if cls._data is None:
            try:
                with open('messages.json', 'r', encoding='utf-8') as f:
                    cls._data = json.load(f)
            except:
                cls._data = {}
    
    @classmethod
    def get(cls, path: str, **kwargs) -> str:
        cls._load()
        keys = path.split('.')
        current = cls._data.get('offline_scanner', {})
        
        try:
            for key in keys:
                current = current[key]
            return current.format(**kwargs) if kwargs else current
        except:
            return f"Message not found: {path}"


class FileDownloader:
    def __init__(self, console: Console):
        self.console = console
        self.download_url = "https://github.com/Pymmdrza/Rich-Address-Wallet/releases/download/Litecoin/Latest_Rich_Litecoin_Addresses.txt.gz"
        self.temp_file = "temp_download.gz"
    
    def download_and_extract(self, target_filename: str) -> bool:
        try:
            self._show_file_not_found_messages(target_filename)
            
            if not self._ask_permission(target_filename):
                return False
            
            if not self._download_file():
                return False
            
            if not self._extract_and_rename(target_filename):
                return False
            
            self._cleanup()
            self.console.print(Messages.get("download.ready"))
            return True
            
        except Exception as e:
            self.console.print(Messages.get("errors.download.failed", error=str(e)))
            self._cleanup()
            return False
    
    def _show_file_not_found_messages(self, filename: str) -> None:
        error_keys = ['line1', 'line2', 'release', 'download', 'rename']
        for key in error_keys:
            self.console.print(Messages.get(f"errors.notfound.{key}", filename=filename))
        print()
    
    def _ask_permission(self, filename: str) -> bool:
        self.console.print(Messages.get("download.prompt_message", filename=filename))
        
        choice_text = Messages.get("download.prompt_choice")
        prompt_text = Messages.get("prompts.download_choice")
        
        self.console.print(choice_text, end="")
        response = input(prompt_text).lower().strip()
        
        if response not in ['y', 'yes', '1']:
            self.console.print(Messages.get("errors.download.cancelled"))
            return False
        
        return True
    
    def _download_file(self) -> bool:
        try:
            self.console.print(Messages.get("download.starting", url=self.download_url))
            
            with Progress(
                TextColumn("[bold blue]Downloading", justify="right"),
                BarColumn(bar_width=None),
                "[progress.percentage]{task.percentage:>3.1f}%",
                "•",
                FileSizeColumn(),
                "•",
                TotalFileSizeColumn(),
                "•",
                TransferSpeedColumn(),
                "•",
                TimeRemainingColumn(),
                console=self.console
            ) as progress:
                
                req = urllib.request.Request(self.download_url)
                req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                
                with urllib.request.urlopen(req) as response:
                    total_size = int(response.headers.get('Content-Length', 0))
                    
                    task = progress.add_task("Download", total=total_size)
                    
                    with open(self.temp_file, 'wb') as f:
                        downloaded = 0
                        chunk_size = 8192
                        
                        while True:
                            chunk = response.read(chunk_size)
                            if not chunk:
                                break
                            
                            f.write(chunk)
                            downloaded += len(chunk)
                            progress.update(task, completed=downloaded)
            
            self.console.print(Messages.get("download.completed"))
            return True
            
        except urllib.error.URLError as e:
            self.console.print(Messages.get("errors.download.network_error", error=str(e)))
            return False
        except Exception as e:
            self.console.print(Messages.get("errors.download.failed", error=str(e)))
            return False
    
    def _extract_and_rename(self, target_filename: str) -> bool:
        try:
            self.console.print(Messages.get("download.extracting"))
            
            with gzip.open(self.temp_file, 'rb') as f_in:
                extracted_content = f_in.read()
            
            temp_txt = "temp_extracted.txt"
            with open(temp_txt, 'wb') as f_out:
                f_out.write(extracted_content)
            
            self.console.print(Messages.get("download.extract_completed"))
            
            if not self._validate_txt_file(temp_txt):
                os.remove(temp_txt)
                return False
            
            if os.path.exists(target_filename):
                os.remove(target_filename)
            
            shutil.move(temp_txt, target_filename)
            
            self.console.print(Messages.get("download.txt_found", filename=temp_txt))
            self.console.print(Messages.get("download.renamed", new_name=target_filename))
            
            return True
            
        except Exception as e:
            self.console.print(Messages.get("errors.download.extract_failed", error=str(e)))
            return False
    
    def _validate_txt_file(self, filename: str) -> bool:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = [f.readline().strip() for _ in range(5)]
                
            valid_lines = [line for line in lines if line and len(line) > 20]
            
            if len(valid_lines) < 3:
                self.console.print(Messages.get("errors.download.no_txt_found"))
                return False
            
            return True
            
        except Exception:
            return False
    
    def _cleanup(self) -> None:
        for temp_file in [self.temp_file, "temp_extracted.txt"]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass


class AddressLoader:
    @staticmethod
    def load_from_file(filename: str, console: Console) -> Optional[Set[str]]:
        if not os.path.exists(filename):
            downloader = FileDownloader(console)
            if not downloader.download_and_extract(filename):
                return None
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                addresses = {addr.strip() for addr in f if addr.strip()}
            
            console.print(Messages.get("messages.loaded_addresses", 
                                     count=len(addresses), filename=filename))
            return addresses
            
        except Exception as e:
            console.print(Messages.get("messages.file_error", 
                                     filename=filename, error=str(e)))
            return None


class UserInterface:
    @staticmethod
    def get_scan_parameters() -> tuple:
        try:
            start = int(input(Messages.get("prompts.start_input")))
            end = int(input(Messages.get("prompts.end_input")))
            speed = int(input(Messages.get("prompts.speed_input")))
            output = input(Messages.get("prompts.output_input")).strip()
            
            if not output.endswith('.txt'):
                output += '.txt'
            
            return start, end, speed, output
        except ValueError as e:
            console = Console()
            console.print(Messages.get("messages.invalid_input", error=str(e)))
            sys.exit(1)
    
    @staticmethod
    def show_header(start: int, end: int, speed: int, filename: str, output: str) -> None:
        console = Console()
        header = Messages.get("header",
            start=start,
            end=end,
            start_hex=f"{start:064x}",
            end_hex=f"{end:064x}",
            total=f"{end - start:,}",
            speed=f"{speed:,}",
            filename=filename,
            output=output,
            current_time=time.ctime()
        )
        console.print(header)


class Scanner:
    def __init__(self, addresses: Set[str], console: Console):
        self.addresses = addresses
        self.console = console
        self.scan_count = 0
        self.found_count = 0
    
    def scan_range(self, start: int, end: int, speed: int, output: str) -> None:
        self.console.print(Messages.get("messages.scanning_start", 
                                       start=start, end=end))
        
        for i in range(start, end):
            self.scan_count += 1
            
            if self.scan_count % 100 == 0:
                self._update_title()
            
            private_key = f"{i:064x}"
            wallet = Wallet(private_key)
            
            addresses_to_check = [
                wallet.get_address(coin="litecoin"),
                wallet.get_address(coin="litecoin", address_type="p2wpkh"),
                wallet.get_address(coin="litecoin", address_type="p2sh-p2wpkh")
            ]
            
            for addr in addresses_to_check:
                if addr in self.addresses:
                    self._save_found_key(addr, private_key, output)
                    self.console.print(Messages.get("messages.found_key", address=addr))
                    self._update_title()
                    break
            
            if self.scan_count % speed == 0:
                self._show_progress(end - start, speed)
    
    def _update_title(self) -> None:
        title = f"SCAN: {self.scan_count:,} | FOUND: {self.found_count}"
        sys.stdout.write(f"\033]0;{title}\a")
        sys.stdout.flush()
    
    def _save_found_key(self, address: str, private_key: str, output_file: str) -> None:
        try:
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(f"[ADDR]: {address}\n")
                f.write(f"[KEY]:  {private_key}\n")
                f.write("--------------------PROGRAMMER MMDRZA.COM--------------------\n\n")
            self.found_count += 1
        except Exception as e:
            self.console.print(f"Error saving to file: {e}")
    
    def _show_progress(self, total_range: int, speed: int) -> None:
        progress = (self.scan_count / total_range) * 100
        sys.stdout.write(
            f"\r[SCAN: {self.scan_count:,}] [FOUND: {self.found_count}] "
            f"[PROGRESS: {progress:.2f}%] [SPEED: {speed} k/s]"
        )
        sys.stdout.flush()
    
    def show_statistics(self, elapsed_time: float) -> None:
        self.console.print(Messages.get("messages.scan_completed"))
        self.console.print(Messages.get("messages.stats_header"))
        self.console.print(Messages.get("messages.stats_scanned", count=self.scan_count))
        self.console.print(Messages.get("messages.stats_found", count=self.found_count))
        self.console.print(Messages.get("messages.stats_time", time=elapsed_time))
        
        if self.scan_count > 0:
            rate = self.scan_count / elapsed_time
            self.console.print(Messages.get("messages.stats_speed", speed=rate))


class LitecoinScanner:
    def __init__(self):
        self.console = Console()
        self.filename = 'ltc500.txt'
    
    def run(self) -> None:
        self.console.clear()
        self.console.print(Messages.get("messages.loading"))
        
        addresses = AddressLoader.load_from_file(self.filename, self.console)
        if addresses is None:
            sys.exit(1)
        
        start, end, speed, output = UserInterface.get_scan_parameters()
        
        if start >= end:
            self.console.print(Messages.get("messages.invalid_range"))
            return
        
        self.console.clear()
        UserInterface.show_header(start, end, speed, self.filename, output)
        
        scanner = Scanner(addresses, self.console)
        start_time = time.time()
        
        try:
            scanner.scan_range(start, end, speed, output)
        except KeyboardInterrupt:
            self.console.print(Messages.get("messages.scan_interrupted"))
        finally:
            elapsed = time.time() - start_time
            scanner.show_statistics(elapsed)


def main():
    try:
        app = LitecoinScanner()
        app.run()
    except Exception as e:
        console = Console()
        console.print(Messages.get("messages.fatal_error", error=str(e)))
        sys.exit(1)


if __name__ == "__main__":
    main()