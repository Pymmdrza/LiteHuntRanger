import os
import sys
import time
import json
import urllib.request
from urllib.error import URLError, HTTPError
from typing import Dict, Optional, Tuple
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
        current = cls._data.get('online_scanner', {})

        try:
            for key in keys:
                current = current[key]
            return current.format(**kwargs) if kwargs else current
        except:
            return f"Message not found: {path}"


class OnlineAddressChecker:
    """Online API checker for Litecoin addresses"""

    def __init__(self, delay_ms: int = 200):
        self.delay = delay_ms / 1000.0
        self.api_base = "https://litecoin.atomicwallet.io/api/v2/address"
        self.ua = UserAgent()
        self.consecutive_errors = 0
        self.max_consecutive_errors = 10

    def check_address_balance(self, address: str) -> Optional[Tuple[float, int]]:
        """
        Check address balance and transaction count online
        Returns: (balance_in_ltc, transaction_count) or None if error/empty
        """
        try:
            # Rate limiting to avoid API throttling
            time.sleep(self.delay)

            # Build API URL for balance check
            url = f"{self.api_base}/{address}?details=basic"

            # Create request with random user agent
            req = urllib.request.Request(url)
            req.add_header('User-Agent', self.ua.get_useragent(mode="desktop"))
            req.add_header('Accept', 'application/json')
            # Make API request
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status != 200:
                    self.consecutive_errors += 1
                    return None

                # Parse JSON response
                data = json.loads(response.read().decode('utf-8'))

                # Reset error counter on successful response
                self.consecutive_errors = 0

                # Extract balance (in satoshis) and transaction count
                balance_satoshis = data.get('balance', '0')
                txs = data.get('txs', 0)

                # Convert satoshis to LTC (1 LTC = 100,000,000 satoshis)
                balance_ltc = float(balance_satoshis) / 100000000 if balance_satoshis != '0' else 0.0

                # Return data if there's any activity (balance > 0 or transactions > 0)
                if balance_ltc > 0 or txs > 0:
                    return (balance_ltc, txs)

                return None

        except HTTPError as e:
            self.consecutive_errors += 1
            if e.code == 429:
                # Rate limit hit, wait longer
                time.sleep(3)
            return None

        except (URLError, json.JSONDecodeError, Exception):
            self.consecutive_errors += 1
            return None

    def is_healthy(self) -> bool:
        """Check if API connection is still healthy"""
        return self.consecutive_errors < self.max_consecutive_errors


class OnlineDisplayManager:
    """Display manager for online scanning with three panels"""

    def __init__(self, start: int, end: int, delay: int, output: str):
        self.console = Console()
        self.layout = Layout()
        self.start = start
        self.end = end
        self.delay = delay
        self.output = output
        self.start_time = time.time()

        # Counters
        self.keys_generated = 0
        self.addresses_checked = 0
        self.balances_found = 0
        self.api_errors = 0

        # Recent activity log
        self.recent_checks = []
        self.max_recent_display = 12

        self._setup_layout()

    def _setup_layout(self) -> None:
        """Setup three-panel layout"""
        self.layout.split_column(
            Layout(name="header", size=15),
            Layout(name="stats", size=6),
            Layout(name="activity")
        )

    def _create_header_panel(self) -> Panel:
        """Create scanner information header panel"""
        header_text = Messages.get("header",
                                   start=self.start,
                                   end=self.end,
                                   start_hex=f"{self.start:064x}",
                                   end_hex=f"{self.end:064x}",
                                   total=self.end - self.start,
                                   delay=self.delay,
                                   output=self.output,
                                   start_time=time.ctime()
                                   )

        return Panel(
            header_text,
            title="[bold blue]Online Scanner Configuration[/bold blue]",
            border_style="blue"
        )

    def _create_stats_panel(self) -> Panel:
        """Create live statistics panel"""
        elapsed = time.time() - self.start_time

        # Calculate rates
        key_rate = self.keys_generated / elapsed if elapsed > 0 else 0
        check_rate = self.addresses_checked / elapsed if elapsed > 0 else 0

        # Calculate progress
        progress = ((self.keys_generated / (self.end - self.start)) * 100) if self.end > self.start else 0

        stats_text = f"""[green]Keys Generated:[/green] [cyan]{self.keys_generated:,}[/cyan]     [green]Key Rate:[/green] [magenta]{key_rate:.1f}/sec[/magenta]
[green]Online Checks:[/green] [yellow]{self.addresses_checked:,}[/yellow]     [green]Check Rate:[/green] [magenta]{check_rate:.1f}/sec[/magenta]
[green]Balances Found:[/green] [green]{self.balances_found}[/green]     [green]API Errors:[/green] [red]{self.api_errors}[/red]
[green]Progress:[/green] [cyan]{progress:.2f}%[/cyan]     [green]Elapsed:[/green] [blue]{elapsed:.1f}s[/blue]"""

        return Panel(
            stats_text,
            title="[bold green]Live Online Statistics[/bold green]",
            border_style="green"
        )

    def _create_activity_panel(self) -> Panel:
        """Create recent online activity panel"""
        activity_text = ""

        # Show recent address checks
        for check in self.recent_checks[-self.max_recent_display:]:
            address, addr_type, balance, txs, status = check

            # Format balance display
            if balance > 0:
                balance_str = f"{balance:.8f}"
            else:
                balance_str = "0.00000000"

            # Status coloring
            if status == "BALANCE":
                status_display = "[green]BALANCE[/green]"
                line_color = "green"
            elif status == "ACTIVITY":
                status_display = "[yellow]ACTIVITY[/yellow]"
                line_color = "yellow"
            elif status == "EMPTY":
                status_display = "[white]EMPTY[/white]"
                line_color = "white"
            else:
                status_display = "[red]ERROR[/red]"
                line_color = "red"

            # Truncate long addresses
            short_addr = address[:28] + "..." if len(address) > 31 else address

            # Format activity line
            line = f"[{line_color}]{short_addr:<31} | {addr_type:<8} | {balance_str:<12} LTC | {txs:<4} TXs | {status_display}[/{line_color}]"
            activity_text += line + "\n"

        if not activity_text:
            activity_text = "[dim]Starting online address checking...[/dim]"

        return Panel(
            activity_text.rstrip(),
            title="[bold yellow]Live Online Activity Monitor[/bold yellow]",
            border_style="yellow"
        )

    def update_display(self) -> None:
        """Update all display panels"""
        self.layout["header"].update(self._create_header_panel())
        self.layout["stats"].update(self._create_stats_panel())
        self.layout["activity"].update(self._create_activity_panel())

        # Update terminal title with current stats
        title = f"GEN: {self.keys_generated:,} | CHK: {self.addresses_checked:,} | FOUND: {self.balances_found}"
        sys.stdout.write(f"\033]0;{title}\a")
        sys.stdout.flush()

    def log_check_result(self, address: str, addr_type: str, balance: float, txs: int, status: str) -> None:
        """Log a check result to recent activity"""
        self.recent_checks.append((address, addr_type, balance, txs, status))

        # Keep only recent checks to prevent memory bloat
        if len(self.recent_checks) > self.max_recent_display * 2:
            self.recent_checks = self.recent_checks[-self.max_recent_display:]

    def increment_generated(self) -> None:
        self.keys_generated += 1

    def increment_checked(self) -> None:
        self.addresses_checked += 1

    def increment_found(self) -> None:
        self.balances_found += 1

    def increment_errors(self) -> None:
        self.api_errors += 1


class OnlineScanner:
    """Main online scanner class"""

    def __init__(self, display: OnlineDisplayManager, delay_ms: int):
        self.display = display
        self.checker = OnlineAddressChecker(delay_ms)
        self.output_file = None
        self.console = Console()

    def scan_range_online(self, start: int, end: int, output_file: str) -> None:
        """Scan range and check each address online for balance"""
        self.output_file = output_file

        with Live(self.display.layout, console=self.display.console, refresh_per_second=2) as live:

            for key_index in range(start, end):
                # Generate key and increment counter
                self.display.increment_generated()

                # Create private key from index
                private_key = f"{key_index:064x}"
                wallet = Wallet(private_key)

                # Generate different address types
                address_types = [
                    ("P2PKH", wallet.get_address(coin="litecoin")),
                    ("P2WPKH", wallet.get_address(coin="litecoin", address_type="p2wpkh")),
                    ("P2SH", wallet.get_address(coin="litecoin", address_type="p2sh-p2wpkh"))
                ]

                # Check each address type online
                for addr_type, address in address_types:

                    # Check if the API is still healthy
                    if not self.checker.is_healthy():
                        self.console.print("[red]Too many API errors. Stopping scan.[/red]")
                        return

                    self.display.increment_checked()

                    # Check address balance online
                    result = self.checker.check_address_balance(address)

                    if result is not None:
                        balance, txs = result

                        # Determine status
                        if balance > 0:
                            status = "BALANCE"
                        else:
                            status = "ACTIVITY"

                        # Save found address
                        self._save_active_address(address, private_key, addr_type, balance, txs)
                        self.display.increment_found()
                        self.display.log_check_result(address, addr_type, balance, txs, status)

                    else:
                        # No balance or activity
                        self.display.log_check_result(address, addr_type, 0.0, 0, "EMPTY")

                    # Update display every few checks
                    if self.display.addresses_checked % 3 == 0:
                        self.display.update_display()
                        live.update(self.display.layout)

                # Small delay between keys to prevent overwhelming
                time.sleep(0.005)

    def _save_active_address(self, address: str, private_key: str, addr_type: str,
                             balance: float, txs: int) -> None:
        """Save the address with balance/activity to output a file"""
        try:
            with open(self.output_file, 'a', encoding='utf-8') as f:
                f.write(f"[FOUND]: {time.ctime()}\n")
                f.write(f"[ADDRESS]: {address}\n")
                f.write(f"[PRIVATE_KEY]: {private_key}\n")
                f.write(f"[ADDRESS_TYPE]: {addr_type}\n")
                f.write(f"[BALANCE_LTC]: {balance:.8f}\n")
                f.write(f"[TRANSACTIONS]: {txs}\n")
                f.write(f"[API_SOURCE]: Atomic Wallet API\n")
                f.write("=" * 60 + "\n\n")
        except Exception:
            self.display.increment_errors()


class LitecoinOnlineScanner:
    """Main application class for online scanning"""

    def __init__(self):
        self.console = Console()

    def get_scan_parameters(self) -> tuple:
        """Get scanning parameters from user"""
        self.console.print("[cyan]Litecoin Online Balance Scanner[/cyan]")
        self.console.print("[yellow]This scanner checks addresses online for balances[/yellow]\n")

        try:
            start = int(input(Messages.get("prompts.start_input")))
            end = int(input(Messages.get("prompts.end_input")))
            delay = int(input(Messages.get("prompts.delay_input")))
            output = input(Messages.get("prompts.output_input")).strip()

            if not output.endswith('.txt'):
                output += '.txt'

            return start, end, delay, output
        except ValueError as e:
            self.console.print(Messages.get("messages.invalid_input", error=str(e)))
            sys.exit(1)

    def run(self) -> None:
        """Main execution method"""
        self.console.clear()
        self.console.print(Messages.get("messages.loading"))

        # Get user input
        start, end, delay, output = self.get_scan_parameters()

        # Validate input
        if start >= end:
            self.console.print(Messages.get("messages.invalid_range"))
            return

        if delay < 100:
            self.console.print("[yellow]Warning: Delay less than 100ms may cause API rate limiting[/yellow]")
            time.sleep(3)

        # Initialize display manager
        display = OnlineDisplayManager(start, end, delay, output)

        # Initialize scanner
        scanner = OnlineScanner(display, delay)

        try:
            self.console.clear()
            scanner.scan_range_online(start, end, output)

        except KeyboardInterrupt:
            self.console.clear()
            self.console.print(Messages.get("messages.scan_interrupted"))

        finally:
            # Show final results
            self.console.clear()
            self.console.print(Messages.get("messages.scan_completed"))
            self.console.print(f"[green]Online Scan Results:[/green]")
            self.console.print(f"  Keys Generated: [cyan]{display.keys_generated:,}[/cyan]")
            self.console.print(f"  Addresses Checked: [yellow]{display.addresses_checked:,}[/yellow]")
            self.console.print(f"  Balances Found: [green]{display.balances_found}[/green]")
            self.console.print(f"  API Errors: [red]{display.api_errors}[/red]")

            if display.balances_found > 0:
                self.console.print(f"[green]Results saved to: {output}[/green]")


def main():
    """Entry point"""
    try:
        app = LitecoinOnlineScanner()
        app.run()
    except Exception as e:
        console = Console()
        console.print(Messages.get("messages.fatal_error", error=str(e)))
        sys.exit(1)


if __name__ == "__main__":
    main()