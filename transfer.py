#!/usr/bin/env python
import sys, socket

def write(filename, c):
    f = open(filename, 'rb')
    data = f.read(4096)
    while data:
        c.send(data)
        data = f.read(4096)
    f.close()

def main(port, ip_B = None, port_B = None):
    if ip_B is None and port_B is None:
        #now you acting like a server
        s = socket.socket()
        host = socket.gethostname()
        port = int(port)
        print('hostname:'host)
        s.bind((host,port))
        s.listen(5)
        while True:
            print('Waiting for a connection')
            (c, addr) = s.accept()
            print('Got connection from', addr)
            filename = input('Please type the file_name/path you want to transfer:\n')
            #tell the client what file you are going to cend
            c.send(bytes(filename,'UTF-8'))
            agreement = str(c.recv(10), 'UTF-8')
            if(agreement == 'Yes'):
                write(filename, c)
                print('Finished sending. Closing connection')
            c.close()
    elif ip_B is not None and port_B is not None:
        #now you are acting like a client
        s = socket.socket()
        print('trying to connect to', ip_B, int(port_B))
        s.connect((ip_B, int(port_B)))

        print('Connected to', ip_B)
        #assume the filename is within 100 bytes
        filename = str(s.recv(100), 'UTF-8')
        check = '{} is goint to send "{}". Are you going to receive it? [Y/N] '.format(ip_B, filename)
        agreement = input(check)
        while True:
            if(agreement == 'Y'):
                s.send(b'Yes')
                f = open(filename,'wb') #open in binary
                print('Downloading data.', end='')
                data = s.recv(4096)
                while (data):
                    print('.', end='')
                    f.write(data)
                    data = s.recv(4096)
                print()
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
    else:
        print('Impossible, Fatal logic error.')
if __name__ == '__main__':
    try:
        if len(sys.argv) != 2 and len(sys.argv) != 4:
            print('<usage: python {} <port> [ip_B] [port_B]>')
        elif len(sys.argv) == 2:
            main(sys.argv[1])
        else:
            main(sys.argv[1], sys.argv[2], sys.argv[3])
    except KeyboardInterrupt:
        pass