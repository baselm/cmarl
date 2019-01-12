from subprocess import Popen, PIPE
import os
from tempfile import mkdtemp
from werkzeug import secure_filename
import requests
import gym
from gym import error, spaces, utils
from gym.utils import seeding
from gym import spaces, logger
import subprocess
from subprocess import Popen, PIPE
import numpy as np 
class FooEnv(gym.Env):
    metadata = {'render.modes': ['human']}
    def __init__(self):
        print('__init__')
        self.maxNode = 5 
        self.minNode =1 
        self.node = 1
        self.cpu_axis  = self.get_cpu_observation()
        self.mem_axis = self.get_mem_observation()
        self.disk_axis = self.get_disk_observation()
        self.net_axis  = self.get_net_observation()
        self.action_space = spaces.Discrete(9)
        high = np.array([
            self.get_cpu_observation(),
            self.get_mem_observation(),
            self.get_disk_observation(),
            self.get_net_observation()])
        low = np.array([
            np.zeros(5),
            np.zeros(5),
            np.zeros(5),
            np.zeros(5)])
        self.observation_space = spaces.Box(low, high, dtype=np.float32)
        self.seed()
        self.obs= 0
        self.obs = self.get_observation()
        self.viewer = None
        self.state = self.get_observation()
        self.attempt = 0 
        self.steps_beyond_done = None
        self.done = False
        self.adapte_cpu= False  
        self.adapte_mem= False 
        self.adapte_disk= False 
        self.adapte_net= False 
        
    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]
    
    def step(self, action):
        assert self.action_space.contains(action), "%r (%s) invalid"%(action, type(action))
        state = self.get_observation()
        #past_stat = self.state
        print(state)
        #Find the Utility Prefernces 
        # Select action 
        # get the reward value
       
        maxUtility = np.amax(self.obs[:,4])
        utilityType = np.argmax(self.obs[:,4])
        if utilityType== 0:
            self.adapte_cpu=True 
        elif utilityType== 1:
            self.adapte_mem = True
        elif utilityType== 2:
            self.adapte_disk = True
        elif utilityType== 3:
            self.adapte_net = True
        self.attempt += 1
        print('self.adapte_cpu: ', self.adapte_cpu, 'self.adapte_mem:', self.adapte_mem, 'self.adapte_disk:',self.adapte_disk,'self.adapte_net:', self.adapte_net )
        done=False
        reward=0
        #Here 
     
        if action == 0:
            print("Scale Down Move to State S1")
            #Reward = max of utility fitness

            response = requests.get(' http://192.168.99.100:5000/services/vscale/web/'+ str(self.attempt) + '/' + str(self.cpu_axis[0])+'/'+str(self.cpu_axis[3]))
            results = response.json()
            if results['result']=='Service converged':
                done=True       
                print(results)
            else:
                done= False
            self.obs = self.get_observation()
            reward= 1 - np.amax(self.obs[:,3])  
            print(reward)
            info = "Scale Down Move to State S5"
        elif action == 1:
            print("Stay in State S0")
            self.obs = self.get_observation()
            reward= 1 - np.amax(self.obs[:,3])  
            if (self.attempt>10):
                done = True
                reward= 1
            else:
                done= False 
            info = "Stay in State S0"
            print("reward: ",reward, np.amax(self.obs[:,4]))
        elif action == 2: 
            print("Scale Service UP S2")

            response = requests.get(' http://192.168.99.100:5000/services/vscale/web/'+ str(self.attempt) + '/' + str(self.cpu_axis[0])+'/'+str(self.cpu_axis[3]))
            results = response.json()
            if results['result']=='Service converged':
                done=True 
                self.obs = self.get_observation()
                reward= 1 - np.amax(self.obs[:,3])  
            else:
                done= False
                print(results)

                self.obs = self.get_observation()
                reward= 1 - np.amax(self.obs[:,3])  
                print(reward)

            info = "Scale Up Move to State S1"
            print("reward: ",reward, np.amax(self.obs[:,4]))

        elif action == 3: 
            print("Maintain Cluster State S0")
            self.obs = self.get_observation()
            reward= 1 - np.amax(self.obs[:,3])  
            print("reward: ",reward, np.amax(self.obs[:,4]))
            if (self.attempt>10):
                done = True
                info = "Maintain Cluster State S0"
                reward = 1
        elif action == 4: 

            current_state = self.obs

            if (self.node < self.maxNode and self.node >= self.minNode ):
                print("Add Node S4")
                cur_dir = os.getcwd()
                filepath = os.path.join(cur_dir, 'addNode.sh')
                print (filepath)
                res= subprocess.call(filepath, shell=True)
                print (res)
                info = "Add Node S4"
                self.obs = self.get_observation()
                reward= 1 - np.amax(self.obs[:,3])
                print("reward: ",reward, np.amax(self.obs[:,4]))
                done= True
                self.node +=1
                self.attempt = 0 
            else:
                print("Add Node with attempt: ", self.attempt)
                done= False
                self.obs = self.get_observation()
                reward= 1 - np.amax(self.obs[:,3])
                print("reward: ",reward, np.amax(self.obs[:,4]))

        elif action == 5: 

            self.obs = self.get_observation()
            if (self.attempt > 10 and self.node <= self.maxNode and self.node > self.minNode ):
                print("Delete Node S4")
                cur_dir = os.getcwd()
                filepath = os.path.join(cur_dir, 'deleteNode.sh')
                print (filepath)
                res= subprocess.call(filepath, shell=True)
                print (res)
                info = "Delete Node S4"
                reward= 1 - np.amax(self.obs[:,3])
                print("reward: ",reward, np.amax(self.obs[:,4]))
                done= True
                self.attempt = 0
                self.node -=1
            else:
                print("Delete Node with attempt: ", self.attempt, self.node, self.minNode, self.maxNode)
                done= False
                reward= 0
                print("reward: ",reward)

        elif action==6:
            print("freedisk Space S6")
            cur_dir = os.getcwd()
            filepath = os.path.join(cur_dir, 'freedisk.sh')
            print (filepath)
            res= subprocess.call(filepath, shell=True)
            print (res)
            info = "freedisk Node S1"
            reward= 1 - np.amax(self.obs[:,3])
            print("reward: ",reward, np.amax(self.obs[:,4]))
            done= True
            self.attempt = 0

        elif action == 7:
            print("Scale Down Move to State S1")
            #Reward = max of utility fitness

            response = requests.get(' http://192.168.99.100:5000/services/vscale/web/'+ str(self.attempt) + '/' + str(self.cpu_axis[0])+'/'+str(self.cpu_axis[3]))
            results = response.json()
            if results['result']=='Service converged':
                done=True       
                print(results)
            else:
                done= False
            self.obs = self.get_observation()
            reward= 1 - np.amax(self.obs[:,3])  
            print(reward)
            info = "Scale Down Move to State S5"

        elif action==8:

            if (self.node < self.maxNode and self.node >= self.minNode ):
                
                cur_dir = os.getcwd()
                filepath = os.path.join(cur_dir, 'manager.sh')
                print (filepath)
                res= subprocess.call(filepath, shell=True)
                print (res)
                info = "Add Manager node S7"
                self.node += 1
                reward= 1 - np.amax(self.obs[:,3])
                print("reward: ",reward, np.amax(self.obs[:,4]), "Node: ", self.node)
                done= True
                self.attempt = 0
            else:
                print("Add Manager node S7 failed", self.attempt)
                reward= 0
                done= False
                print("reward: ",reward, np.amax(self.obs[:,4]))
        else: 
            print ("action not defined")
            self.obs = self.get_observation()
            done= False
            reward= -1
            info = "action not defined"
        
        if done: 
            reward = 1.0
        elif self.steps_beyond_done is None:
            #Adaptation Failed 
            reward = 0.0 
            self.steps_beyond_done = 0
        else: 
            if self.steps_beyond_done == 1:
                logger.warn("You are calling 'step()' even though this environment has already returned done = True. You should always call 'reset()' once you receive 'done = True' -- any further steps are undefined behavior.")
                self.steps_beyond_done += 1
                reward = 0.0
         
        return self.obs, reward, done, {}
    def reset(self):
        self.state = self.get_observation()
        self.steps_beyond_done = None
        self.adapte_cpu= False  
        self.adapte_mem= False 
        self.adapte_disk= False 
        self.adapte_net= False 
        self.maxNode = 5 
        self.minNode =1 
        return np.array(self.state)
    def render(self, mode='human', close=False):
        logger.warn("View is not allowed in this environment")
        return 0 
    def close(self):
        if self.viewer:
            self.viewer.close()
            self.viewer = None
    def get_observation(self):
        self.disk_axis = self.get_disk_observation() 
        self.mem_axis = self.get_mem_observation()
        self.cpu_axis = self.get_cpu_observation()
        self.net_axis = self.get_net_observation()
        
        obs =np.vstack((self.cpu_axis,self.mem_axis, self.disk_axis, self.net_axis) )
        return obs 
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
                utility_disk = results['utility_disk']
                disk_axis=[disk, prediction, anomalyScore, anomalyLikelihood, utility_disk]
                 
        return np.array(disk_axis) 
  
    def get_current_state(self):
        current_state = self.state
         
        return current_state