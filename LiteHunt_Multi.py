import time, random, json
import bitcoin
import requests
from lxml import html
from hdwallet import HDWallet
from hdwallet.symbols import LTC as sym
from rich.console import Console
import subprocess
from threading import Thread as worker

try:
    subprocess.check_call(["python3", '-m', 'pip', 'install', 'hdwallet'])
    subprocess.check_call(["python3", '-m', 'pip', 'install', 'rich'])
    subprocess.check_call(["python3", '-m', 'pip', 'install', 'lxml'])
    subprocess.check_call(["python3", '-m', 'pip', 'install', 'bitcoin'])
except:
    subprocess.check_call(["python", '-m', 'pip', 'install', 'hdwallet'])
    subprocess.check_call(["python", '-m', 'pip', 'install', 'rich'])
    subprocess.check_call(["python", '-m', 'pip', 'install', 'lxml'])
    subprocess.check_call(["python", '-m', 'pip', 'install', 'bitcoin'])

cl = Console()


def task():
    cl.clear()
    start = int(input('RANGE START [INTEGER] : '))
    end = int(input('RANGE END [INTEGER] : '))
    outp = str(input('OUTFile Name : '))
    cl.print(f"""
    [red][[gold1]+[/gold1]][green1] Thread Time    :[/green1][white] {time.thread_time()}[/white] [/red]
    [red][[gold1]+[/gold1]][green1] Start Range    :[/green1][white] {start}                    [/white] [/red]
    [red][[gold1]+[/gold1]][green1] END Range      :[/green1][white] {end}                    [/white] [/red]
    [red][[gold1]+[/gold1]][green1] Start RangeKey :[/green1][white] {"%064x" % start}   [/white] [/red]
    [red][[gold1]+[/gold1]][green1] END RangeKey   :[/green1][white] {"%064x" % end}     [/white] [/red]
    [red][[gold1]+[/gold1]][green1] Total Generate :[/green1][white] {end - start}       [/white] [/red]
    [red][[gold1]+[/gold1]][green1] Thread (CORE)  :[/green1][white] Optimize            [/white] [/red]
    [red][[gold1]+[/gold1]][green1] Target Coin    :[/green1][gold1] Litecoin [LTC]      [/gold1] [/red]
    [red][[gold1]+[/gold1]][green1] Method Hunter  :[/green1][white] HDWallet [[white on red3]P2WPKH[/white on red3]]    [/white] [/red]
    [red][[gold1]+[/gold1]][green1] Output File    :[/green1][white] {outp}              [/white] [/red]
    [red]=======================================================[/red]
    [cyan]Programmer : Mmdrza.Com [red] ~[/red] Channel CryptoAttacker.t.me [/cyan]
    [red]=======================================================[/red]


    PLEASE WAITE ...

    """)
    time.sleep(8)
    cl.clear()
    cl.print(f"""
    [red][[gold1]+[/gold1]][green1] Thread Time    :[/green1][white] {time.thread_time()}[/white] [/red]
    [red][[gold1]+[/gold1]][green1] Start Range    :[/green1][white] {start}                    [/white] [/red]
    [red][[gold1]+[/gold1]][green1] END Range      :[/green1][white] {end}                    [/white] [/red]
    [red][[gold1]+[/gold1]][green1] Start RangeKey :[/green1][white] {"%064x" % start}   [/white] [/red]
    [red][[gold1]+[/gold1]][green1] END RangeKey   :[/green1][white] {"%064x" % end}     [/white] [/red]
    [red][[gold1]+[/gold1]][green1] Total Generate :[/green1][white] {end - start}       [/white] [/red]
    [red][[gold1]+[/gold1]][green1] Thread (CORE)  :[/green1][white] Optimize            [/white] [/red]
    [red][[gold1]+[/gold1]][green1] Target Coin    :[/green1][gold1] Litecoin [LTC]      [/gold1] [/red]
    [red][[gold1]+[/gold1]][green1] Method Hunter  :[/green1][white] HDWallet [[white on red3]P2WPKH[/white on red3]]    [/white] [/red]
    [red][[gold1]+[/gold1]][green1] Output File    :[/green1][white] {outp}              [/white] [/red]
    [red]=======================================================[/red]
    [cyan]Programmer : Mmdrza.Com [red] ~[/red] Channel CryptoAttacker.t.me [/cyan]
    [red]=======================================================[/red]

    """)

    def gettxid(addr):
        urlb = "https://litecoin.atomicwallet.io/address/" + addr
        reqb = requests.get(urlb)
        bybs = reqb.content
        srcb = html.fromstring(bybs)
        xptb = '/html/body/main/div/div[2]/div[1]/table/tbody/tr[4]/td[2]'
        tree = srcb.xpath(xptb)
        txid = str(tree[0].text_content())
        tran = str(txid)
        return tran

    def getbal(addr):
        xurlb = "https://litecoin.atomicwallet.io/address/" + addr
        xreqb = requests.get(xurlb)
        xbybs = xreqb.content
        xsrcb = html.fromstring(xbybs)
        xxptb = '/html/body/main/div/div[2]/div[1]/table/tbody/tr[3]/td[2]'
        xtree = xsrcb.xpath(xxptb)
        xvalu = str(xtree[0].text_content())
        return xvalu

    z = 0
    w = 0
    wx = 0
    for x in range(start, end):
        z += 1
        tt = time.ctime()
        dec = x
        key = "%064x" % dec
        hd: HDWallet = HDWallet(symbol=sym)
        hd.from_private_key(private_key=key)
        add = hd.p2wpkh_address()
        addr = hd.p2pkh_address()
        # ---------------------------------------------------------------- #
        tran = gettxid(add)
        tran2 = gettxid(addr)
        # ---------------------------------------------------------------- #
        if int(tran) > 0 or int(tran2) > 0:
            w += 1
            # ---------------------------------------------------------------- #
            bal: str = getbal(add)
            bal2: str = getbal(addr)
            iffer = '0 LTC'
            amf = '0 LTC'
            # ---------------------------------------------------------------- #
            cl.print(f"""
    [red][+][green1] FOUND :[/green1][white] {time.thread_time()}[/white][/red]
    [red][+][green1] KEY   :[/green1][white] {key.upper()}       [/white][/red]
    [red][+][green1] ADDR  :[/green1][white] {add}               [/white][/red]
    [red][+][green1] Method:[/green1][white] BLOCK               [/white][/red]
    [red]----------------------------------------------------------------------[/red]
    [white on red3][SCAN: {z}][F:{w}][RICH:{wx}][TXID: {tran}][{tt}]          [/white on red3]
    [red]----------------------------------------------------------------------[/red]
            """)
            if str(bal) != str(iffer) or str(bal2) != str(iffer):
                wx += 1
                with open(outp, 'a') as rc:
                    rc.write(
                        f"[{tt}]:{add}   TXID:{tran}   BALANCE:{bal}\n[{tt}]:{addr}  BALANCE:{bal2}\n[{tt}]:{key}\n----------------====[MMDRZA.COM ~ CryptoAttacker.T.Me]====----------------\n")
                    rc.close()
                cl.print(f"\n"
                         f"[red][+][green1] FOUND :[/green1][white] {time.thread_time()}[/white][/red]\n"
                         f"[red][+][green1] KEY   :[/green1][white] {key.upper()}       [/white][/red]\n"
                         f"[red][+][green1] ADDR P2WPKH :[/green1][white] {add}               [/white][/red]\n"
                         f"[red][+][green1] ADDR P2PKH :[/green1][white] {addr}               [/white][/red]\n"
                         f"[red][+][green1] Method:[/green1][white] BLOCK               [/white][/red]\n"
                         f"[red]----------------------------------------------------------------------[/red]\n"
                         f"[white on blue3][SCAN: {z}][F:{w}][RICH:{wx}][BALANCE: {bal}][BALANCE2: {bal2}][TXID: {tran}][TXID2: {tran2}]          [/white on blue3]\n"
                         f"[red]----------------------------------------------------------------------[/red]\n")


        else:
            print(f"[T:{z}][F:{w}][RICH:{wx}]:[{add}]:[{addr}]", end="\r")


x = worker(target=task)
x.start()
x.join()
