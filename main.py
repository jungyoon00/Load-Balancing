from components import Client, Server
from collections import deque
import threading, heapq, time, os

class LoadBalancer:
    def __init__(self) -> None:
        self.process = []
        self.servers = []

        self.SIGNAL_STR_WEIGHT = 300

    def push(self, clients:list[Client]) -> None:
        """ generator """
        { heapq.heappush(self.process, self.setWeight(client.info())) for client in clients }
        
    def setWeight(self, get:tuple) -> tuple:
        return ((6 - get[1]) * self.SIGNAL_STR_WEIGHT + get[2], get[1], get[2], get[0])
    
    def updateServer(self, server=None) -> None:
        if server:
            self.servers.append(server)

        """ Server 목록을 성능에 따라 정렬 """
        self.servers = sorted(self.servers, key=lambda get: (6 - get.info()[1]) * (get.clients * 2))
    
    def distribution(self) -> None:
        while self.process:
            self.updateServer()
            
            client_info = heapq.heappop(self.process)

            server:Server = self.servers[0]
            server.addClient(client_info)


class CompareLB(LoadBalancer):
    def __init__(self) -> None:
        super().__init__()

        self.process = deque()
    
    def setWeight(self, get: tuple) -> tuple:
        return (0, get[1], get[2], get[0])
    
    def push(self, clients: list[Client]) -> None:
        { self.process.append(self.setWeight(client.info())) for client in clients }
    
    def updateServer(self, server:Server) -> None:
        self.servers.append(server)

    def distribution(self) -> None:
        index = 0
        limit = len(self.servers)
        while self.process:

            """ server를 정렬하지 않고 클라이언트와 순서대로 매칭 """
            if index == limit: index = 0
            client_info = self.process.popleft()

            server:Server = self.servers[index]
            server.addClient(client_info)

            index += 1


class serverWork(threading.Thread):
    def __init__(self, index:int, server:Server):
        super().__init__()

        self.index = index
        self.server = server

        self.daemon = True
    
    def run(self):
        print(f"{self.index} Server is on.")
        self.server.proceeding()


class Flow:
    def __init__(self, balancer, tasks:int=100) -> None:
        self.servers:list[Server] = []
        self.clients = deque()

        self.loadbalancer = balancer()
        self.tasks = tasks

        self._CLIENT_PUSH_DELAY = 0.5

    def generate(self, server_opt:tuple=(10, None), client_opt:tuple=(300, None, None)) -> None:

        """ option validation check """
        if server_opt[1]:
            if len(server_opt[1]) != server_opt[0]:
                raise Exception("Custom Error: #Line 96 < The length of the second element of server_opt is invalid.")
        if client_opt[1]:
            if len(client_opt[1]) != client_opt[0]:
                raise Exception("Custom Error: #Line 99 < The length of the second element of client_opt is invalid.")
        if client_opt[2]:
            if len(client_opt[2]) != client_opt[0]:
                raise Exception("Custom Error: #Line 102 < The length of the third element of client_opt is invalid.")
        
        
        """ generate Server data """
        if not server_opt[1]:
            for index in range(server_opt[0]):
                server = Server()
                server.generate(index)
                self.servers.append(server)
        else:
            for index, performance in zip(range(server_opt[0]), server_opt[1]):
                server = Server()
                server.generate(index, True, performance)
                self.servers.append(server)
        

        """ generate Client data """
        if not client_opt[1]:
            for index in range(client_opt[0]):
                client = Client()
                client.generate(index)
                self.clients.append(client)
        else:
            for index, signal_str, request_size in zip(range(client_opt[0]), client_opt[1], client_opt[2]):
                client = Client()
                client.generate(index, True, signal_str, request_size)
                self.clients.append(client)

    def clientPush(self, step:int=10) -> None:
        start = 0
        while start < len(self.clients):
            if len(self.clients) >= step:
                slicing = list(self.clients)[start:start+step]
            else:
                slicing = list(self.clients)[start:]
            
            start += step

            self.loadbalancer.push(slicing)
            self.loadbalancer.distribution()

            time.sleep(self._CLIENT_PUSH_DELAY)

        for server in self.servers:
            server.addClient((-1, 0, 0, 0))
    
    def run(self) -> float:
        """ initializing """
        self.generate(client_opt=(self.tasks, None, None))
        for server in self.servers:
            self.loadbalancer.updateServer(server)

        """ set start time """
        START_TIME = time.time()

        threads = []

        clientWork = threading.Thread(target=self.clientPush)
        clientWork.start()
        threads.append(clientWork)

        for index, server in enumerate(self.servers):
            thread = serverWork(index, server)
            thread.start()
            threads.append(thread)
        
        for thread in threads:
            thread.join()

        """ set end time """
        END_TIME = time.time()

        return END_TIME - START_TIME


def killprocess(target:int=0) -> None:
    try:
        if target == 0:
            os.system('taskkill /f /im python.exe')
        else:
            os.system(f'taskkill /f /pid {target}')
    except:
        pass

if __name__ == "__main__":
    os.system("cls")

    """
    # self._SIMULATE_DELAY_SETTING = 5
    LoadBalancer --> Process excution time: 158.374559s
    CompareLB --> Process excution time: 187.737068s

    # self._SIMULATE_DELAY_SETTING = 2
    LoadBalancer --> Process excution time: 43.300739s
    CompareLB --> Process excution time: 75.106835s
    """

    mainflow = Flow(CompareLB, 100) # LoadBalancer(Weighted Round Robin + Least Response Time Method) | CompareLB(Round Robin Method)
    sec = mainflow.run()

    print("=" * 35)
    print(f'Process excution time: {sec:5f}s')
    print("=" * 35)

    killprocess()