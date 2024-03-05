import subprocess

args = [r'C:\Program Files\OpenVPN\bin\openvpn.exe',
        '--config',
        r'C:\Program Files\OpenVPN\config\UK_freeopenvpn_tcp.ovpn']
print(args)

shell = r'"C:\Program Files\OpenVPN\bin\openvpn.exe" --config "C:\Program Files\OpenVPN\config\UK_freeopenvpn_tcp.ovpn" --auth-user-pass "./auth_open_vpn.txt"'
r = subprocess.Popen(args, shell=True)
shell = r'"C:\Program Files\OpenVPN\bin\openvpn.exe" --config "C:\Program Files\OpenVPN\config\USA_freeopenvpn_tcp.ovpn" --auth-user-pass "./auth_open_vpn.txt"'
r1 = subprocess.run(shell)

