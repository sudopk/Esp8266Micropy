import network
import time
import config_lib
import socket
import ESPWebServer
import relay_lib

sta_if = network.WLAN(network.STA_IF)
ap_if = network.WLAN(network.AP_IF)

config = config_lib.load_config()

ap_if.config(essid='myspot', password=config['ap_pwd'])


def info():
    sta_if.active(True)
    print(f'Station active: {sta_if.active()}')
    print(f'Station status: {sta_if.status()} {network.STAT_IDLE}')
    # perform_scan()
    # sta_if.connect('network', config['sta_network_pwd'])
    time.sleep_ms(500)
    print(f'Station status after connect: {sta_if.status()} {network.STAT_IDLE}, connected: {sta_if.isconnected()}')
    print(f'Station ifconfig: {sta_if.ifconfig()}')

    print(f'Access point active: {ap_if.active()}')
    for k in ['ssid', 'essid', 'psk', 'key', 'password', 'authmode']:
        try:
            print(f'Access point config for {k}: {ap_if.config(k)}')
        except ValueError as e:
            print(f'AP config not found for {k}: {e}')
    print(f'Access point ifconfig: {ap_if.ifconfig()}')

class ScanResult(object):
    def __init__(self, ssid: str, rssi: int, security: int) -> None:
        self.ssid = ssid
        self.rssi = rssi
        self.security = security

    def __str__(self) -> str:
        return f'Ssid: {self.ssid}, Rssi: {self.rssi}, Security: {self.security}'

    def __repr__(self) -> str:
        return str(self)


def perform_scan(): # List[ScanResult]
    results = []
    for s in sta_if.scan():
        ssid = s[0].decode('utf-8')
        if ssid:
            results.append(ScanResult(ssid, s[3], s[4]))
    print(f'Scan results: {results}')
    return results

class WebServerUsingSocket(object):
    def __init__(self) -> None:
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind(('', 80))
        self._socket.listen(5)

    def process_request(self):
        conn, addr = self._socket.accept()
        print(f'Got a connection from: {addr}')
        request = conn.recv(1024)
        request = str(request)
        print(f'Request content: {request} ({len(request)})')
        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Content-Type: text/html\n')
        conn.send('Connection: close\n\n')
        # conn.sendall(response)
        conn.close()


HTML_CONTENT = 'text/html'

scan_results = []

def handle_root(sock: socket.socket, args: dict):
    scan_html = '\n'.join(['<label><input type="radio" name="ssid" value="{}" />{} ({} %)</label>'.format(r.ssid, r.ssid, min(100, 2 * (r.rssi + 100))) for r in scan_results])
    connect_wifi_html = """
        <form action="connectwifi" method="get">
        <label>Ssid:</label> {}
        <label for="pwd">Password:</label>
        <input type="password" id="pwd" name="pwd">
        <input type="submit" value="Connect" />
        </form>
        """.format(scan_html) if scan_html else ''

    sta_table_row = f'<tr><td>Station</td> <td>{sta_if.config("essid")} ({sta_if.ifconfig()[0]})</td>' if sta_if.isconnected() else ''

    html = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://cdn.simplecss.org/simple.min.css">
            <title>Spot welder</title>
        </head>
        <body>

        <form action="relay" method="get">
            <button type="submit" name="cmd" value="on">Relay On</button>
            <button type="submit" name="cmd" value="off">Relay Off</button>
        </form>

        <form action="scanwifi" method="get">
            <button type="submit">Scan wifi</button>
            <button type="submit" name="clearonly" value="true">Clear scan data</button>
        </form>

        {connect_wifi_html}

        <form action="setpulse" method="get">
          <label for="ms">Pulse millisec:</label>
          <input type="text" id="ms" name="ms">
          <input type="submit" />
        </form>

        <form action="resetwifi" method="get">
          <input type="submit" value="Reset wifi" />
        </form>

        <table>
            <thead>
                <tr><th>Item</th> <th>Value</th></tr>
            </thead>
            <tbody>
                <tr><td>Relay state</td> <td>{"on" if relay_lib.is_relay_on() else "off"}</td>
                <tr><td>Ap</td> <td>{ap_if.config('essid')} ({ap_if.ifconfig()[0]})</td>
                {sta_table_row}
                <tr><td>Pulse</td> <td>{config[config_lib.PULSE_MS_KEY]} ms</td>
            </tbody>
        </table>
        </body>
        </html>
    """

    ESPWebServer.ok(sock, '200', {}, HTML_CONTENT, html)

def redirect_to_home(sock: socket.socket):
    ESPWebServer.ok(sock, '302', {'Location': '/'}, '')

def handle_relay(sock: socket.socket, args: dict):
    if args.get('cmd', 'off') == 'on':
        relay_lib.relay_pin.on()
    else:
        relay_lib.relay_pin.off()

    redirect_to_home(sock)

def handle_scanwifi(sock: socket.socket, args: dict):
    global scan_results
    if 'clearonly' in args:
        scan_results = []
    else:
        scan_results = perform_scan()

    redirect_to_home(sock)

def handle_connectwifi(sock: socket.socket, args: dict):
    ssid = args.get('ssid', '')
    if ssid:
        sta_if.connect(ssid, args.get('pwd', ''))
    redirect_to_home(sock)

def handle_setpulse(sock: socket.socket, args: dict):
    pulsems = int(args.get('ms', str(config[config_lib.PULSE_MS_KEY])))
    if pulsems < 2 or pulsems > 5000:
        ESPWebServer.err(sock, '400', f'Invalid pulse value: {pulsems}');
        return

    config[config_lib.PULSE_MS_KEY] = pulsems
    config_lib.save_config(config)

    redirect_to_home(sock)

def handle_post(sock: socket.socket, args: dict, content_type: str, content: bytes):
    print(f'Post Args: {args} {content_type}, {content}')

    ESPWebServer.ok(sock, '200', {}, HTML_CONTENT, '')

class WebServer(object):
    def __init__(self) -> None:
        print('Starting the web server')
        ESPWebServer.begin()

        ESPWebServer.onGetPath('/', handle_root)
        ESPWebServer.onPostPath('/post', handle_post)
        ESPWebServer.onGetPath('/relay', handle_relay)
        ESPWebServer.onGetPath('/setpulse', handle_setpulse)
        ESPWebServer.onGetPath('/scanwifi', handle_scanwifi)
        ESPWebServer.onGetPath('/connectwifi', handle_connectwifi)

    def __del__(self):
        self.close()

    def close(self):
        print('Closing the web server')
        ESPWebServer.close()

    def process_request(self):
        ESPWebServer.handleClient()
