from collections import deque
import random, time
import multiprocessing


class Client:
    def __init__(self) -> None:
        self.index = 0           # index인 동시에 seed로서의 기능을 함.
        self.signal_strength = 0 # AP 기준이므로 1 ~ 5로 고정된다. (5가 가장 좋은 신호 상태이다.)
        self.request_size = 0    # TCP 패킷을 기준으로 100 ~ 1500 범위로 제한.

        self._CHECK = False
    
    def info(self) -> tuple:
        return (self.index, self.signal_strength, self.request_size)
    
    def generate(self, index:int, fix:bool=True, *args) -> None:
        if not self._CHECK:
            if not args:
                if fix: random.seed(index)
    
                self.index = index
                self.signal_strength = random.choice([i for i in range(1, 6)])
                self.request_size = random.choice([i for i in range(100, 1501)])
            else:
                self.index = index
                try:
                    self.signal_strength = args[0]
                    self.request_size = args[1]
                except Exception as e:
                    print(f"Catch Err: {e}")
                    if input("[ClientGen] Break Thread? (y/n):").lower()[0] == "y": exit()
            
            self._CHECK = True


class Server:
    def __init__(self) -> None:
        self.index = 0
        self.performance = 0 # 처리 용량으로 계산하는 것이 맞지만 1 ~ 5의 등급으로 구분한다. (5가 최대 성능)
        self.clients = 0

        self._CHECK = False
        self._SIMULATE_DELAY_SETTING = 2 # default: 5

        #manager = multiprocessing.Manager()
        self.queue = deque()

        self.check = True # proceeding의 while loop를 종료하는데에 의미가 있다.
    
    def setCheck(self):
        self.check = False

    def info(self) -> tuple: return self.index, self.performance

    def getConns(self) -> int: return self.clients
    
    def addClient(self, client:Client) -> None:
        self.queue.append(client)
        self.clients += 1

    def generate(self, index:int, fix:bool=True, performance:int=None) -> None:
        if not self._CHECK:
            self.index = index
            if not performance:
                if fix: random.seed(self.index)
                self.performance = random.choice([i for i in range(1, 6)])
            else:
                try:
                    self.performance = performance
                except Exception as e:
                    print(f"Catch Err: {e}")
                    if input("[ServerGen] Break Thread? (y/n):").lower()[0] == "y": exit()
            
            self.capacity = self.performance * 100
            self._CHECK = True
    
    def proceeding(self):
        while self.check:
            if not self.queue:
                continue
    
            task = self.queue.popleft()
            
            if task[0] == -1:
                print(f"{self.index} Server is done.")
                break

            self.clients -= 1
            
            """
            일반적으로는 패킷을 용량으로 나눈 만큼의 딜레이를 time함수로 구현해야한다.
            그러나 multiprocessing을 통해 각 서버에서 클라이언트의 요청을 처리한다는 가정하에
            CPU코어에서 multiprocessing이 지원되지 않는다면 시뮬레이션 실행결과에
            유의미한 오차가 발생할 염려가 있다.
            때문에 이상적으로 시간을 계산한 뒤, 리턴 값들중 최대값을 전체 걸린시간으로 측정하는 기법을 사용한다.
    
            sleep을 실제로 시뮬레이션 하는 옵션을 추가함.
            """
    
            delay = round(task[2]/(self.capacity * task[1]) * self._SIMULATE_DELAY_SETTING, 3)
    
            time.sleep(delay)
            print(f"[{task[3]:03d}] Client -> [{self.index}] Server")