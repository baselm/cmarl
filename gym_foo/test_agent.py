import requests
import gym
from gym import error, spaces, utils
from gym.utils import seeding
from gym import spaces, logger
import numpy as np 



class FooEnv(gym.Env):
    metadata = {'render.modes': ['human']}
    def __init__(self):
        self.cpu_axis  = self.get_cpu_observation()
        self.mem_axis = self.get_mem_observation()
        self.disk_axis = self.get_disk_observation()
        self.net_axis  = self.get_net_observation()
        self.action_space = spaces.Discrete(6)
        high = np.array([
            self.cpu_axis,
            self.mem_axis,
            self.disk_axis,
            self.net_axis])
        
        self.observation_space = spaces.Box(-high, high, dtype=np.float32)
        self.seed()
        self.viewer = None
        self.state = None
        self.steps_beyond_done = None
        
    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]
    
    def step(self, action):
        assert self.action_space.contains(action), "%r (%s) invalid"%(action, type(action))
        state = self.state
        past_stat = self.state
        #cpu_axis, mem_axis, disk_axis, net_axis = state
        if action == 5:
            print("Scale Down Move to State S1")
            #Reward = max of utility fitness 
            r = requests.get('http://192.168.99.100:5000/services/web/2')
            current_state = self.state
            reward= current_state - past_stat
            done= False 
            info = "Scale Down Move to State S1"
        elif action == 0:
            print("Stay in State S0")
            current_state = self.state
            reward= current_state - past_stat
            done= True 
            info = "Stay in State S0"
        elif action == 1: 
            print("Scale Service UP S2")
            r = requests.get('http://192.168.99.100:5000/services/web/4')
            current_state = self.state
            reward= current_state - past_stat
            done= False 
            info = "Stay in State S0"
        elif action == 2: 
            print("Remove Node S3")
            current_state = self.state
            reward= current_state - past_stat
            done= False
            info = "Remove Node S3"
        elif action == 3: 
            print("Mantain Cluster State S0")
            current_state = self.state
            reward= current_state - past_stat
            done= False
            info = "Mantain Cluster State S0"
        elif action == 4: 
            print("Add Node S4")
            current_state = self.state
            reward= current_state - past_stat
            done= False
            info = "Add Node S4"
        else: 
            print ("action not defined")
            current_state = self.state
            reward= -1
            info = "action not defined"
        if done: 
            reward = 1.0
        elif self.steps_beyond_done is None:
            #Adaptation Failed 
            reward = 1.0 
            self.steps_beyond_done = 0
        else: 
            if self.steps_beyond_done == 0:
                logger.warn("You are calling 'step()' even though this environment has already returned done = True. You should always call 'reset()' once you receive 'done = True' -- any further steps are undefined behavior.")
                self.steps_beyond_done += 1
                reward = 0.0
         
        return np.array(self.state), reward, done, {}
    def reset(self):
        self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
        self.steps_beyond_done = None
        return np.array(self.state)
    def render(self, mode='human', close=False):
        logger.warn("View is not allowed in this environment")
        return 0 
    def close(self):
        if self.viewer:
            self.viewer.close()
            self.viewer = None
    def get_cpu_observation(self):
        response = requests.get('http://192.168.99.100:8888/cpu', timeout=5)
        results = response.json()
        if len(results) > 0:
                cpu = results['cpu']
                prediction = results['prediction']
                anomalyScore = results['anomalyScore']
                anomalyLikelihood = results['anomalyLikelihood']
                utility_cpu = results['utility_cpu']
                cpu_axis=[cpu, prediction, anomalyScore, anomalyLikelihood, utility_cpu]
        return np.array(cpu_axis) 
    def get_mem_observation(self):
        response = requests.get('http://192.168.99.100:8888/mem', timeout=5)
        results = response.json()
        if len(results) > 0:
            mem = results['mem']
            prediction = results['prediction']
            anomalyScore = results['anomalyScore']
            anomalyLikelihood = results['anomalyLikelihood']
            utility_mem = results['utility_mem']
            #mem_axis=[mem, prediction, anomalyScore, anomalyLikelihood, utility_mem]    
        mem_axis=[mem, prediction, anomalyScore, anomalyLikelihood, utility_mem]
        return np.array(mem_axis) 
    def get_net_observation(self):
        response = requests.get('http://192.168.99.100:8888/net', timeout=5)
        results = response.json()
        if len(results) > 0:
            net = results['net']
            prediction = results['prediction']
            anomalyScore = results['anomalyScore']
            anomalyLikelihood = results['anomalyLikelihood']
            utility_net = results['utility_net']

        net_axis=[net, prediction, anomalyScore, anomalyLikelihood, utility_net]
        return np.array(net_axis) 
    def get_disk_observation(self):
        response = requests.get('http://192.168.99.100:8888/disk', timeout=5)
        if response is not None:
            results = response.json()
            if len(results) > 0:
                disk = results['disk']
                prediction = results['prediction']
                anomalyScore = results['anomalyScore']
                anomalyLikelihood = results['anomalyLikelihood']
                utility_mem = results['utility_disk']
                disk_axis=[disk, prediction, anomalyScore, anomalyLikelihood, utility_mem]
        return np.array(disk_axis) 
  
    def get_current_state(self):
        current_state = self.state
         
        return current_state
     

