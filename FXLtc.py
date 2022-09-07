import os
import sys
import time
from rich.console import Console
from hdwallet import HDWallet
from hdwallet.symbols import LTC as sym
import subprocess

try:
    subprocess.check_call(["python3", '-m', 'pip', 'install', 'hdwallet'])
    subprocess.check_call(["python3", '-m', 'pip', 'install', 'rich'])
except:
    subprocess.check_call(["python", '-m', 'pip', 'install', 'hdwallet'])
    subprocess.check_call(["python", '-m', 'pip', 'install', 'rich'])

cl = Console()
cl.clear()
cl.print(f"Loaded Rich Wallet Address ...")

filename = 'ltc500.txt'
with open(filename) as f:
    add = f.read().split()
add = set(add)

z = 0
w = 0
start = int(input('START INTEGER : '))
end = int(input('END INTEGER : '))
speed = int(input('SPEED INTEGER :'))
outp = str(input('INSERT OUTPUT FILE NAME .txt : '))
cl.clear()

cl.print(f"""
[green4]╔═╗╦ ╦╔╗╔╔═╗╦═╗[/green4][red3        ] ╔╦╗╔╦╗╔╦╗╦═╗╔═╗╔═╗ ╔═╗╔═╗╔╦╗ [/red3]
[green1]║ ║║║║║║║║╣ ╠╦╝[/green1][dark_orange3] ║║║║║║ ║║╠╦╝╔═╝╠═╣ ║  ║ ║║║║ [/dark_orange3]
[green4]╚═╝╚╩╝╝╚╝╚═╝╩╚═[/green4][red3        ] ╩ ╩╩ ╩═╩╝╩╚═╚═╝╩ ╩o╚═╝╚═╝╩ ╩ [/red3]
[red3]==============================================================[/red3]
[red][[white]+[/white]] [green1]START INPUT  [/green1]: [/red][white]{start}                       [/white]
[red][[white]+[/white]] [green1]END INPUT    [/green1]: [/red][white]{end}                         [/white]
[red][[white]+[/white]] [green1]KEY START    [/green1]: [/red][white]{"%064x" % start}             [/white]
[red][[white]+[/white]] [green1]KEY END      [/green1]: [/red][white]{"%064x" % end}               [/white]
[red][[white]+[/white]] [green1]TOTAL SCAN   [/green1]: [/red][white]{end - start}                 [/white]
[red][[white]+[/white]] [green1]SPEED SCAN   [/green1]: [/red][white]{speed}                       [/white]
[red][[white]+[/white]] [green1]SEARCH FILE  [/green1]: [/red][white]{filename}                    [/white]
[red][[white]+[/white]] [green1]OUTPUT FILE  [/green1]: [/red][white]{outp}                        [/white]
[red][[white]+[/white]] [green1]THREAD       [/green1]: [/red][white]OPTIMIZE                      [/white]
[red][[white]+[/white]] [green1]COIN NAME    [/green1]: [/red][white]Litecoin (LTC)                [/white]
[red][[white]+[/white]] [green1]TYPE ADDRESS [/green1]: [/red][white]P2PKH + P2SH + P2WPKH + P2WSH [/white]
[red][[white]+[/white]] [green1]START PROCESS[/green1]: [/red][white]{time.ctime()}                [/white]
[red3]==============================================================[/red3]""")
for i in range(start, end):
    z += 1
    # ctypes.windll.kernel32.SetConsoleTitleW(f"SCAN:{z} FOUND:{w}")
    title = str(f"\033]0;SCAN: {z} FOUND: {w}\a")
    sys.stdout.write(title)
    sys.stdout.flush()
    DEC = i
    KEY = "%064x" % DEC
    HD: HDWallet = HDWallet(symbol=sym)
    HD.from_private_key(private_key=KEY)
    ADDR = HD.p2pkh_address()
    ADDR2 = HD.p2wpkh_address()
    ADDR3 = HD.p2wsh_address()
    ADDR4 = HD.p2sh_address()
    TT = time.process_time()
    # sys.stdout.write(f"ADDR: {ADDR}\nADDR2: {ADDR2}\nADDR3: {ADDR3}\nADDR4: {ADDR4}")
    # sys.stdout.flush()
    logf = speed
    if int(z % logf) == 0:
        sys.stdout.write(f"[SCAN: {z}][FOUND: {w}][THREAD 128][KS {logf}]\r")
        sys.stdout.flush()
    elif ADDR in add:
        w += 1
        with open(outp, 'a') as fl:
            fl.write(f"[ADDR]:{ADDR}\n{KEY}\n--------------------PROGRAMMER MMDRZA.COM--------------------\n")
            fl.close()

    elif ADDR2 in add:
        w += 1
        with open(outp, 'a') as fl2:
            fl2.write(f"[ADDR]:{ADDR2}\n{KEY}\n--------------------PROGRAMMER MMDRZA.COM--------------------\n")
            fl2.close()

    elif ADDR3 in add:
        w += 1
        with open(outp, 'a') as fl3:
            fl3.write(f"[ADDR]:{ADDR3}\n{KEY}\n--------------------PROGRAMMER MMDRZA.COM--------------------\n")
            fl3.close()

    elif ADDR4 in add:
        w += 1
        with open(outp, 'a') as fl4:
            fl4.write(f"[ADDR]:{ADDR4}\n{KEY}\n--------------------PROGRAMMER MMDRZA.COM--------------------\n")
            fl4.close()
    else:
        continue
