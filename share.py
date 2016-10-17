#!/usr/bin/env python
import os, sys, socket, json, threading
import progress_bar as pb

BUFFER_SIZE = 4096
input_lock = threading.Lock()
process_lock = threading.Lock()
recv_lock = threading.Lock()
userinput = None
received = None

class sendTread(threading.Thread):
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.sock = client

    def run(self):
        filename = input('Please type the file_name/path you want to transfer:\n')
        filename = filename.strip().strip("'").strip('"')
        #tell the client the file_info you are going to cend
        self.sock.send(bytes(file_info(filename),'UTF-8'))
        agreement = str(self.sock.recv(10), 'UTF-8')
        if(agreement == 'Yes'):
            write(filename, self.sock)
            print('Finished sending. Closing connection')
        self.sock.close()

class recvThread(threading.Thread):
    def __init__(self, sock, ip):
        threading.Thread.__init__(self)
        self.sock = sock
        self.ip = ip

    def run(self):
        global userinput, received
        while True:
            #start receive data
            process_lock.acquire()
            process_lock.release()
            recv_lock.acquire()
            try:
                received = str(self.sock.recv(1024), 'UTF-8')
            finally:
                recv_lock.release()
            if process_lock.acquire(False):
                # this message is for you
                fileinfo = received
                j = json.loads(fileinfo)
                filename = j['filename']
                size = int(j['size'])
                check = '{} is goint to send "{}" with size {} bytes. Receive it? [Y/N] '.format(self.ip, filename, size)
                print(check)
                sys.stdout.flush()
                try:
                    while True:
                        if input_lock.acquire():
                            if userinput is None:
                                input_lock.release()
                            else:
                                input_lock.release()
                                break
                    agreement = userinput
                    while True:
                        if(agreement == 'Y'):
                            self.sock.send(b'Yes')
                            f = open(filename,'wb') #open in binary
                            print('Downloading data...')

                            bytes_rev = 0
                            pb.printProgress(bytes_rev, size, prefix='Downloaded', barLength=80)
                            while (bytes_rev < size):
                                data = self.sock.recv(BUFFER_SIZE)
                                f.write(data)
                                bytes_rev += len(data)
                                pb.printProgress(bytes_rev, size, prefix='Downloaded', barLength=80)
                            print('Completed!')
                            sys.stdout.flush()
                            f.close()
                            break
                        elif(agreement == 'N'):
                            self.sock.send(b'No')
                            break
                        else:
                            agreement = input(check)
                finally:
                    print('Receiver release control')
                    process_lock.release()
            else:
                #sombody else in under control, the data is not for you
                pass

def write(filename, c):
    """this function write <filename> to socket <c>"""
    f = open(filename, 'rb')
    data = f.read(BUFFER_SIZE)
    while data:
        c.send(data)
        data = f.read(BUFFER_SIZE)
    f.close()
    c.send()

def file_exist(filename):
    try:
        f = open(filename, 'rb')
        f.close()
        return True
    except FileNotFoundError:
        return False

def file_info(filename):
    """write fileinfo into a JSON str"""
    info = dict(
        filename = filename,
        size = os.stat(filename).st_size
    )
    return json.dumps(info)

def send_file(sock):
    global userinput, received
    # test if it's receiving data
    process_lock.acquire()
    # It's not receiving data
    process_lock.release()
    input_lock.acquire()
    try:
        userinput = input('Please type the file_name/path you want to transfer:\n')
    finally:
        input_lock.release()
    # finished reading input, checkif the input is for sending data
    if(process_lock.acquire(False)):
        try:
            print('Sender have the control')
            #now i'm sending data. I have the control
            filename = userinput.strip().strip("'").strip('"')
            #tell the client the file_info you are going to cend
            if file_exist(filename) == False:
                raise FileNotFoundError
            sock.send(bytes(file_info(filename),'UTF-8'))
            # listening thread will received data
            while True:
                if recv_lock.acquire():
                    if received is None:
                        recv_lock.release()
                    else:
                        recv_lock.release()
                        break
            agreement = received
            if agreement == 'Yes':
                write(filename, sock)
                print('Finished sending.')
            elif agreement == 'No':
                print('He/She rejected to receive the file.')
        except FileNotFoundError:
            print("Sorry. The file doesn't exist.")
        finally:
            print('sender released the control')
            process_lock.release()
    else:
        # the input is for receiver
        pass


def server_mode(port):
    s = socket.socket()
    host = socket.gethostname()
    port = int(port)
    print('hostname:',host)
    s.bind(('127.0.0.1',port))
    s.listen(5)
    print('Waiting for a connection')
    (c, addr) = s.accept()
    print('Got connection from', addr)
    print('-'*80)
    # Create new threads
    recv_thd = recvThread(c, addr[0])
    # Run the child thread to received any incoming message
    recv_thd.start()
    while True:
        #run the main sending thread
        send_file(c)

def client_mode(ip_B, port_B):
    s = socket.socket()
    s.connect((ip_B, int(port_B)))
    print('Connected to', ip_B)
    print('-'*80)
    #assume the fileinfo is within 1024 bytes
    recv_thd = recvThread(s, ip_B)
    # Start new child thread
    recv_thd.start()
    # Run the main sending thread
    while True:
        send_file(s)

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