#!/usr/bin/env python
import os, sys, socket, json
import progress_bar as pb

BUFFER_SIZE = 4096

def write(filename, c):
    """this function write <filename> to socket <c>"""
    f = open(filename, 'rb')
    data = f.read(BUFFER_SIZE)
    while data:
        c.send(data)
        data = f.read(BUFFER_SIZE)
    f.close()

def file_info(filename):
    """write fileinfo into a JSON str"""
    info = dict(
        filename = filename,
        size = os.stat(filename).st_size
    )
    return json.dumps(info)

def server_mode(port):
    s = socket.socket()
    host = socket.gethostname()
    port = int(port)
    print('hostname:',host)
    s.bind(('10.0.0.213',port))
    s.listen(5)
    while True:
        print('Waiting for a connection')
        (c, addr) = s.accept()
        print('Got connection from', addr)
        filename = input('Please type the file_name/path you want to transfer:\n')
        #tell the client the file_info you are going to cend
        c.send(bytes(file_info(filename),'UTF-8'))
        agreement = str(c.recv(10), 'UTF-8')
        if(agreement == 'Yes'):
            write(filename, c)
            print('Finished sending. Closing connection')
        c.close()

def client_mode(ip_B, port_B):
    s = socket.socket()
    s.connect((ip_B, int(port_B)))
    print('Connected to', ip_B)
    #assume the fileinfo is within 1024 bytes
    fileinfo = str(s.recv(1024), 'UTF-8')
    j = json.loads(fileinfo)
    filename = j['filename']
    size = int(j['size'])
    check = '{} is goint to send "{}" with size {} bytes. Receive it? [Y/N] '.format(ip_B, filename, size)
    agreement = input(check)
    while True:
        if(agreement == 'Y'):
            s.send(b'Yes')
            f = open(filename,'wb') #open in binary
            print('Downloading data...')
            data = s.recv(BUFFER_SIZE)
            bytes_rev = 0
            while (data):
                f.write(data)
                bytes_rev += len(data)
                pb.printProgress(bytes_rev, size, prefix='Downloaded', barLength=80)
                data = s.recv(BUFFER_SIZE)
            print('Completed! Closing connection')
            f.close()
            s.close()
            break
        elif(agreement == 'N'):
            s.send(b'No')
            s.close()
            break
        else:
            agreement = input(check)

def main(port=None, ip_B = None, port_B = None):
    if ip_B is None and port_B is None:
        #now you acting like a server
        server_mode(port)
    else:
        #now you are acting like a client
        client_mode(ip_B, port_B)

if __name__ == '__main__':
    try:
        if len(sys.argv) != 2 and len(sys.argv) != 3:
            print('<To Create A Socket>: python <port>')
            print('<To Connect To Your Friend>: python <friend_ip> <friend_port>')
        elif len(sys.argv) == 2:
            main(port=sys.argv[1])
        else:
            main(ip_B=sys.argv[1], port_B=sys.argv[2])
    except KeyboardInterrupt:
        pass