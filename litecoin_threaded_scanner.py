import os
import sys
import time
import json
import urllib.request
import threading
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional, Tuple, List
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from libcrypto import Wallet
from real_useragent import UserAgent


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
        current = cls._data.get('threaded_scanner', {})
        
        try:
            for key in keys:
                current = current[key]
            return current.format(**kwargs) if kwargs else current
        except:
            return f"Message not found: {path}"


class AddressChecker:
    def __init__(self, delay_ms: int = 100):
        self.delay = delay_ms / 1000.0
        self.api_base = "https://litecoin.atomicwallet.io/api/v2/address"
        self.ua = UserAgent()
        self.lock = threading.Lock()
    
    def check_address(self, address: str) -> Optional[Tuple[float, int]]:
        try:
            time.sleep(self.delay)
            
            url = f"{self.api_base}/{address}?details=basic"
            req = urllib.request.Request(url)
            
            with self.lock:
                user_agent = self.ua.get_useragent(mode="desktop")
            
            req.add_header('User-Agent', user_agent)
            req.add_header('Accept', 'application/json')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status != 200:
                    return None
                
                data = json.loads(response.read().decode('utf-8'))
                balance_str = data.get('balance', '0')
                txs = data.get('txs', 0)
                balance = float(balance_str) / 100000000 if balance_str != '0' else 0.0
                
                if balance > 0 or txs > 0:
                    return (balance, txs)
                
                return None
        except:
            return None


class ThreadSafeDisplayManager:
    def __init__(self, start: int, end: int, delay: int, threads: int, output: str):
        self.console = Console()
        self.layout = Layout()
        self.start = start
        self.end = end
        self.delay = delay
        self.threads = threads
        self.output = output
        self.start_time = time.time()
        
        self.lock = threading.RLock()
        self.generated_count = 0
        self.checked_count = 0
        self.found_count = 0
        self.error_count = 0
        self.recent_checks = []
        self.max_recent_checks = 15
        self.active_threads = 0
        
        self._setup_layout()
    
    def _setup_layout(self) -> None:
        self.layout.split_column(
            Layout(name="header", size=16),
            Layout(name="stats", size=9),
            Layout(name="checks")
        )
    
    def _create_header_panel(self) -> Panel:
        header_text = Messages.get("header",
            start=self.start,
            end=self.end,
            start_hex=f"{self.start:064x}",
            end_hex=f"{self.end:064x}",
            total=self.end - self.start,
            delay=self.delay,
            threads=self.threads,
            output=self.output,
            start_time=time.ctime()
        )
        
        return Panel(
            header_text,
            title="[bold blue]Scanner Information[/bold blue]",
            border_style="blue"
        )
    
    def _create_stats_panel(self) -> Panel:
        with self.lock:
            elapsed = time.time() - self.start_time
            gen_rate = self.generated_count / elapsed if elapsed > 0 else 0
            check_rate = self.checked_count / elapsed if elapsed > 0 else 0
            progress = ((self.generated_count / (self.end - self.start)) * 100) if self.end > self.start else 0
            
            stats_text = f"""[green]Keys Generated:[/green] [cyan]{self.generated_count:,}[/cyan]     [green]Generation Rate:[/green] [magenta]{gen_rate:.1f}/sec[/magenta]
[green]Addresses Checked:[/green] [yellow]{self.checked_count:,}[/yellow]     [green]Check Rate:[/green] [magenta]{check_rate:.1f}/sec[/magenta]
[green]Balances Found:[/green] [green]{self.found_count}[/green]     [green]Network Errors:[/green] [red]{self.error_count}[/red]
[green]Active Threads:[/green] [blue]{self.active_threads}[/blue]     [green]Progress:[/green] [cyan]{progress:.2f}%[/cyan]
[green]Elapsed Time:[/green] [yellow]{elapsed:.1f}s[/yellow]"""
        
        return Panel(
            stats_text,
            title="[bold green]Live Statistics[/bold green]",
            border_style="green"
        )
    
    def _create_checks_panel(self) -> Panel:
        with self.lock:
            checks_text = ""
            
            for check in self.recent_checks[-self.max_recent_checks:]:
                address, addr_type, balance, txs, status, thread_id = check
                balance_str = f"{balance:.8f}" if balance > 0 else "0.00000000"
                
                if status == "FOUND":
                    status_color = "[green]FOUND[/green]"
                    line_color = "green"
                elif status == "EMPTY":
                    status_color = "[white]EMPTY[/white]"
                    line_color = "white"
                else:
                    status_color = "[red]ERROR[/red]"
                    line_color = "red"
                
                short_address = address[:25] + "..." if len(address) > 28 else address
                line = f"[{line_color}]T{thread_id:02d} | {short_address:<25} | {addr_type:<8} | {balance_str:<12} LTC | {txs:<4} TXs | {status_color}[/{line_color}]"
                checks_text += line + "\n"
            
            if not checks_text:
                checks_text = "[dim]No addresses checked yet...[/dim]"
        
        return Panel(
            checks_text.rstrip(),
            title="[bold yellow]Recent Address Checks (Thread-Safe)[/bold yellow]",
            border_style="yellow"
        )
    
    def update_display(self) -> None:
        self.layout["header"].update(self._create_header_panel())
        self.layout["stats"].update(self._create_stats_panel())
        self.layout["checks"].update(self._create_checks_panel())
        
        with self.lock:
            title = f"GEN: {self.generated_count:,} | CHK: {self.checked_count:,} | FOUND: {self.found_count} | THR: {self.active_threads}"
        
        sys.stdout.write(f"\033]0;{title}\a")
        sys.stdout.flush()
    
    def add_check_result(self, address: str, addr_type: str, balance: float, txs: int, status: str, thread_id: int) -> None:
        with self.lock:
            self.recent_checks.append((address, addr_type, balance, txs, status, thread_id))
            
            if len(self.recent_checks) > self.max_recent_checks * 2:
                self.recent_checks = self.recent_checks[-self.max_recent_checks:]
    
    def increment_generated(self) -> None:
        with self.lock:
            self.generated_count += 1
    
    def increment_checked(self) -> None:
        with self.lock:
            self.checked_count += 1
    
    def increment_found(self) -> None:
        with self.lock:
            self.found_count += 1
    
    def increment_errors(self) -> None:
        with self.lock:
            self.error_count += 1
    
    def set_active_threads(self, count: int) -> None:
        with self.lock:
            self.active_threads = count


class ThreadedChecker:
    def __init__(self, checker: AddressChecker, display: ThreadSafeDisplayManager, output_file: str):
        self.checker = checker
        self.display = display
        self.output_file = output_file
        self.file_lock = threading.Lock()
    
    def check_address_batch(self, addresses_data: List[Tuple[str, str, str, int]]) -> None:
        thread_id = threading.current_thread().ident % 100
        
        for private_key, address, addr_type, key_index in addresses_data:
            self.display.increment_checked()
            
            result = self.checker.check_address(address)
            
            if result is not None:
                balance, txs = result
                self._save_found_address(address, private_key, addr_type, balance, txs)
                self.display.increment_found()
                self.display.add_check_result(address, addr_type, balance, txs, "FOUND", thread_id)
            else:
                self.display.add_check_result(address, addr_type, 0.0, 0, "EMPTY", thread_id)
    
    def _save_found_address(self, address: str, private_key: str, addr_type: str, 
                          balance: float, txs: int) -> None:
        try:
            with self.file_lock:
                with open(self.output_file, 'a', encoding='utf-8') as f:
                    f.write(f"[ADDR]: {address}\n")
                    f.write(f"[KEY]:  {private_key}\n")
                    f.write(f"[TYPE]: {addr_type}\n")
                    f.write(f"[BALANCE]: {balance:.8f} LTC\n")
                    f.write(f"[TRANSACTIONS]: {txs}\n")
                    f.write(f"[TIME]: {time.ctime()}\n")
                    f.write("--------------------PROGRAMMER MMDRZA.COM--------------------\n\n")
        except:
            pass


class ThreadedOnlineScanner:
    def __init__(self, display: ThreadSafeDisplayManager, delay_ms: int, thread_count: int):
        self.display = display
        self.checker = AddressChecker(delay_ms)
        self.thread_count = thread_count
        self.stop_event = threading.Event()
    
    def generate_addresses_worker(self, start: int, end: int, address_queue: Queue) -> None:
        for i in range(start, end):
            if self.stop_event.is_set():
                break
                
            self.display.increment_generated()
            
            private_key = f"{i:064x}"
            wallet = Wallet(private_key)
            
            addresses_to_check = [
                (private_key, wallet.get_address(coin="litecoin"), "P2PKH", i),
                (private_key, wallet.get_address(coin="litecoin", address_type="p2wpkh"), "P2WPKH", i),
                (private_key, wallet.get_address(coin="litecoin", address_type="p2sh-p2wpkh"), "P2SH", i)
            ]
            
            for addr_data in addresses_to_check:
                address_queue.put(addr_data)
            
            time.sleep(0.001)
    
    def scan_range(self, start: int, end: int, output: str) -> None:
        address_queue = Queue(maxsize=self.thread_count * 10)
        threaded_checker = ThreadedChecker(self.checker, self.display, output)
        
        with Live(self.display.layout, console=self.display.console, refresh_per_second=3) as live:
            
            generator_thread = threading.Thread(
                target=self.generate_addresses_worker,
                args=(start, end, address_queue),
                daemon=True
            )
            generator_thread.start()
            
            with ThreadPoolExecutor(max_workers=self.thread_count, thread_name_prefix="AddressChecker") as executor:
                
                active_futures = set()
                batch_size = 3
                
                try:
                    while generator_thread.is_alive() or not address_queue.empty() or active_futures:
                        
                        self.display.set_active_threads(len(active_futures))
                        
                        while len(active_futures) < self.thread_count and not address_queue.empty():
                            batch = []
                            
                            for _ in range(batch_size):
                                try:
                                    addr_data = address_queue.get_nowait()
                                    batch.append(addr_data)
                                except Empty:
                                    break
                            
                            if batch:
                                future = executor.submit(threaded_checker.check_address_batch, batch)
                                active_futures.add(future)
                        
                        completed_futures = []
                        for future in active_futures:
                            if future.done():
                                completed_futures.append(future)
                                try:
                                    future.result()
                                except Exception:
                                    self.display.increment_errors()
                        
                        for future in completed_futures:
                            active_futures.remove(future)
                        
                        self.display.update_display()
                        live.update(self.display.layout)
                        
                        time.sleep(0.1)
                        
                except KeyboardInterrupt:
                    self.stop_event.set()
                    raise
                
                finally:
                    for future in active_futures:
                        try:
                            future.result(timeout=1)
                        except:
                            pass


class LitecoinThreadedScanner:
    def __init__(self):
        self.console = Console()
    
    def get_scan_parameters(self) -> tuple:
        self.console.print("[cyan]Litecoin Online Scanner Configuration (Threaded)[/cyan]\n")
        
        try:
            start = int(input(Messages.get("prompts.start_input")))
            end = int(input(Messages.get("prompts.end_input")))
            delay = int(input(Messages.get("prompts.delay_input")))
            threads = int(input(Messages.get("prompts.threads_input")))
            output = input(Messages.get("prompts.output_input")).strip()
            
            if not output.endswith('.txt'):
                output += '.txt'
            
            if threads < 1:
                threads = 1
            elif threads > 20:
                threads = 20
                self.console.print("[yellow]Warning: Thread count limited to 20 for stability[/yellow]")
            
            return start, end, delay, threads, output
        except ValueError as e:
            self.console.print(Messages.get("messages.invalid_input", error=str(e)))
            sys.exit(1)
    
    def run(self) -> None:
        self.console.clear()
        self.console.print(Messages.get("messages.loading"))
        
        start, end, delay, threads, output = self.get_scan_parameters()
        
        if start >= end:
            self.console.print(Messages.get("messages.invalid_range"))
            return
        
        if delay < 30:
            self.console.print("[yellow]Warning: Delay less than 30ms may cause rate limiting with threading[/yellow]")
        
        display = ThreadSafeDisplayManager(start, end, delay, threads, output)
        scanner = ThreadedOnlineScanner(display, delay, threads)
        
        try:
            self.console.clear()
            scanner.scan_range(start, end, output)
        except KeyboardInterrupt:
            self.console.clear()
            self.console.print(Messages.get("messages.scan_interrupted"))
        finally:
            self.console.clear()
            self.console.print(Messages.get("messages.scan_completed"))
            self.console.print(f"[green]Final Statistics:[/green]")
            self.console.print(f"  Generated: [cyan]{display.generated_count:,}[/cyan]")
            self.console.print(f"  Checked: [yellow]{display.checked_count:,}[/yellow]")
            self.console.print(f"  Found: [green]{display.found_count}[/green]")
            self.console.print(f"  Errors: [red]{display.error_count}[/red]")
            self.console.print(f"  Threads Used: [blue]{threads}[/blue]")


def main():
    try:
        app = LitecoinThreadedScanner()
        app.run()
    except Exception as e:
        console = Console()
        console.print(Messages.get("messages.fatal_error", error=str(e)))
        sys.exit(1)


if __name__ == "__main__":
    main()