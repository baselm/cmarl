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
import time 
import csv
import pandas as pd 
class FooEnv(gym.Env):
    metadata = {'render.modes': ['human']}
    def __init__(self):
        print('__init__')
        tstart = time.time()
        filename1="dqn_logsv4.csv"
        self.fileHandle = open(filename1,"w")
        self.writer = csv.writer(self.fileHandle)
        self.maxNode = 5 
        self.minNode = 1 
        self.node = 1
        self.ip = '192.168.99.100'
        self.cluster= False
        #self.ip = subprocess.check_output(["docker-machine", "ip", "new-mgr"])
        self.cpu_axis  = self.get_cpu_observation()
        self.mem_axis = self.get_mem_observation()
        self.disk_axis = self.get_disk_observation()
        self.net_axis  = self.get_net_observation()
        self.action_space = spaces.Discrete(10)
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
        self.state_name = 's0'
        self.attempt = 0 
        self.steps_beyond_done = None
        self.done = False
        self.adapte_cpu= False  
        self.adapte_mem= False 
        self.adapte_disk= False 
        self.adapte_net= False 
        self.writer.writerow(["timestamp","state", "action", "reward", "maxUtility", "duration", "info", "# node"])
    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]
    
    def step(self, action):
        assert self.action_space.contains(action), "%r (%s) invalid"%(action, type(action))
        state = self.get_observation()
        #past_stat = self.state
        #print(state)
        #Find the Utility Prefernces 
        # Select action 
        # get the reward value
        tstart = time.time()
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
        #print('self.adapte_cpu: ', self.adapte_cpu, 'self.adapte_mem:', self.adapte_mem, 'self.adapte_disk:',self.adapte_disk,'self.adapte_net:', self.adapte_net )
        done=False
        reward=0
        info=''
        print ("Starting Action: ", action)
        if action==0:
            #print("Stay in State S0")
            self.obs = self.get_observation()
            reward=  np.amax(self.obs[:,3])
            self.state_name='s0'
        elif action == 1:
            #print("Stay in State S1")
            self.obs = self.get_observation()
            done = True
            self.state_name='s1'
            reward=  1
        elif action == 2:
            self.obs = self.get_observation()
            try:
                response = requests.get('http://'+self.ip+':8888/services/vscale/web/'+ str(self.attempt) + '/' + str(self.cpu_axis[0])+'/'+str(self.cpu_axis[3]))
                results = response.json()
                if results['result']=='Service converged':
                    done=True 
                    self.obs = self.get_observation()
                    reward= 1 - np.amax(self.obs[:,3]) 
                    self.state_name='s2'
                    info = "Scale Up Move to State S2"
                else:
                    done= False
                    print(results)
                    self.obs = self.get_observation()
                    reward= 1- np.amax(self.obs[:,3])  
                    print("reward: ",reward, np.amax(self.obs[:,4]))
                    self.state_name='s0'
                    info = "S2 => No Scale Move back to State S0"
            except:
                pass
            finally:
                
                pass

        elif action == 3: 
            #print("Maintain Cluster State S4 and delete dangling docker containers")
            self.obs = self.get_observation()
            reward= 1 - np.amax(self.obs[:,3])
            #print("reward: ",reward, np.amax(self.obs[:,4]))
            done= False
            self.state_name='s0'
            info = "delete dangling docker containers S3"
            cur_dir = os.getcwd()
            filepath = os.path.join(cur_dir, 'cleancontainers.sh')
            print (filepath)
            res= subprocess.call(filepath, shell=True)
            #print (res)
            reward = 1
            self.state_name='s3'
            done = True
        elif action == 4:
            self.obs = self.get_observation()
            if (self.node <= self.maxNode):
                #print("Add Node s4")
                cur_dir = os.getcwd()
                filepath = os.path.join(cur_dir, 'addNode.sh')
                print (filepath)
                res= subprocess.call(filepath, shell=True)
                #print (res)
                info = "Add Node S4"
                self.obs = self.get_observation()
                reward= 1 - np.amax(self.obs[:,3])
                self.state_name='s4'
                print("reward: ",reward, np.amax(self.obs[:,4]))
                done= True
                self.node +=1
            elif self.node==5:
                    done=True 
                    reward= 1 
                    self.state_name='s4'
            else:
                #print("go back to Cluster State at S0: ", self.attempt)
                done= False
                self.obs = self.get_observation()
                reward= 1 - np.amax(self.obs[:,3])
                print("reward: ",reward, np.amax(self.obs[:,4]))
                self.state_name='s0'
        elif action == 5:
            self.obs = self.get_observation()
            if (self.node <= self.maxNode and self.node > self.minNode ):
                #print("Delete Node S5")
                self.state_name='s5'
                cur_dir = os.getcwd()
                filepath = os.path.join(cur_dir, 'deleteNode.sh')
                #print (filepath)
                res= subprocess.call(filepath, shell=True)
                #print (res)
                
                info = "Delete Node S5"
                reward= 1
                #print("reward: ",reward, np.amax(self.obs[:,4]))
                done= True
                self.node -=1
            else:
                #print("Maintain Cluster State at S0: ", self.attempt, self.node, self.minNode, self.maxNode)
                done= False
                reward= 1 - np.amax(self.obs[:,3])
                #print("reward: ",reward)
                self.state_name='s0'
                if self.node==1:
                    done=True 
                    reward= 1
                    self.state_name='s5'
        elif action==6:
            self.obs = self.get_observation()
            #print("freedisk Space S6")
            cur_dir = os.getcwd()
            filepath = os.path.join(cur_dir, 'freedisk.sh')
            #print (filepath)
            res= subprocess.call(filepath, shell=True)
            #print (res)
            info = "freedisk Node S6"
            self.state_name='s6'
            reward= 1
            #print("reward: ",reward, np.amax(self.obs[:,4]))
            done= True
        
        elif action == 7:
            self.obs = self.get_observation()
            if (self.node <= self.maxNode and self.node >= self.minNode ):
                self.state_name='s7'
                cur_dir = os.getcwd()
                filepath = os.path.join(cur_dir, 'promoteNode.sh')
                #print (filepath)
                res= subprocess.call(filepath, shell=True)
                #print (res)
                info = "Promote Worker node to Manager S7"
                reward= 1
                #print("reward: ",reward, np.amax(self.obs[:,4]), "Node: ", self.node)
                done= True
            elif (self.node >= self.maxNode):
                info = "Maintain Manager nodes S0"
                self.state_name='s0'
                reward= 1 - np.amax(self.obs[:,3])
                #print("reward: ",reward, np.amax(self.obs[:,4]), "Node: ", self.node)
                done= True 
        elif action==8:
            self.obs = self.get_observation()
            if (self.node <= self.maxNode):
                self.state_name='s8'
                cur_dir = os.getcwd()
                filepath = os.path.join(cur_dir, 'manager.sh')
                #print (filepath)
                res= subprocess.call(filepath, shell=True)
                #print (res)
                info = "Add Manager node S8"
                self.node += 1
                reward= 1
                #print("reward: ",reward, np.amax(self.obs[:,4]), "Node: ", self.node)
                done= True
            elif (self.node >= self.maxNode):
                info = "Maintain Manager nodes S0"
                self.state_name='s8'
                reward= 1 - np.amax(self.obs[:,3])
                #print("reward: ",reward, np.amax(self.obs[:,4]), "Node: ", self.node)
                done= True 
            else:
                #print("Maintain Cluster State S0", self.attempt, self.node )
                self.state_name='s0'
                reward= 1 - np.amax(self.obs[:,3])
                done= False
                info = "from S8 to S0 "
                
        elif action == 9:
            self.obs = self.get_observation()
            if not self.cluster:
                #add new cluster one time only
                try:         
                    print("rollback and enforce new cluster")
                    cur_dir = os.getcwd()
                    filepath = os.path.join(cur_dir, 'nupicnewcluster.sh')
                    print (filepath)
                    res= subprocess.call(filepath, shell=True)
                     
                    self.state_name='s9'
                    info = "rollback and enforce new  cluster S9"
                    #time.sleep(300)
                    myip = subprocess.check_output(["docker-machine", "ip", "nupic"])
                    self.ip=myip.decode('utf-8').strip()
                    reward= 1
                    #print("reward: ",reward, np.amax(self.obs[:,4]))
                    done= True
                    self.cluster = True
                    #print(reward)
                    info = "rollback and enforce new cluster"
                except:
                    pass
                finally:
                    pass
            
        else: 
            print ("action not defined")
            self.state_name='s0'
            self.obs = self.get_observation()
            done= False
            reward= -1  
            info = "action not defined"
        if done: 
            reward = 1
        elif self.steps_beyond_done is None:
            #Adaptation Failed 
            reward = 0.0 
            self.steps_beyond_done = 0
        else: 
            if self.steps_beyond_done == 1:
                logger.warn("You are calling 'step()' even though this environment has already returned done = True. You should always call 'reset()' once you receive 'done = True' -- any further steps are undefined behavior.")
                self.steps_beyond_done += 1
                reward = 0.0
        tend = tstart - time.time()
        print ("\nState: ", self.state_name, "action: ", action, "reward: ", reward, "# nodes:", self.node, "cluster: ", self.cluster )
        #writer1.writerow(["timestamp","state", "action", "reward", "maxUtility", "duration"])
        self.obs = self.get_observation()
        self.writer.writerow([tstart,self.state_name, action, reward, np.amax(self.obs[:,4]), tend, info, self.node])
        return self.obs, reward, done, {}
    def reset(self):
        #self.fileHandle.close()
        self.state = self.get_observation()
        self.steps_beyond_done = None
        self.adapte_cpu= False  
        self.adapte_mem= False 
        self.adapte_disk= False 
        self.adapte_net= False
        cur_dir = os.getcwd()
        filepath = os.path.join(cur_dir, 'deleteallnodes.sh')
        print (filepath)
        self.maxNode = 5 
        self.minNode = 1 
        #self.node = 1
        #self.cluster= False
        return np.array(self.state)
    def render(self, mode='human', close=False):
        logger.warn("View is not allowed in this environment")
        return 0 
    def close(self):
        self.fileHandle.close()
        if self.viewer:
            self.viewer.close()
            self.viewer = None
    def get_observation(self):
        try:
            self.disk_axis = self.get_disk_observation() 
            self.mem_axis = self.get_mem_observation()
            self.cpu_axis = self.get_cpu_observation()
            self.net_axis = self.get_net_observation()
            obs = np.vstack((self.cpu_axis,self.mem_axis, self.disk_axis, self.net_axis) )
            return obs
        except:
            pass
        finally: 
            pass 
    def get_cpu_observation(self):
        try: 
            response = requests.get('http://'+self.ip+':8888/cpu', timeout=5)
            results = response.json()
            if len(results) > 0:
                    cpu = results['cpu']
                    prediction = results['prediction']
                    anomalyScore = results['anomalyScore']
                    anomalyLikelihood = results['anomalyLikelihood']
                    utility_cpu = results['utility_cpu']
                    cpu_axis=[cpu, prediction, anomalyScore, anomalyLikelihood, utility_cpu]
        except:
            cpu_axis=[-1, -1, -1, -1, -1]
            pass    
        finally: 
            pass
        return np.array(cpu_axis)
    def get_mem_observation(self):
        try:
            response = requests.get('http://'+self.ip+':8888/mem', timeout=5)
            results = response.json()
            if len(results) > 0:
                mem = results['mem']
                prediction = results['prediction']
                anomalyScore = results['anomalyScore']
                anomalyLikelihood = results['anomalyLikelihood']
                utility_mem = results['utility_mem']
                mem_axis=[mem, prediction, anomalyScore, anomalyLikelihood, utility_mem]
        except:
            mem_axis=[-1, -1, -1, -1, -1]
            pass     
        finally: 
            #mem_axis=[0, 0, 0, 0, 0]
            pass
        return np.array(mem_axis)
    def get_net_observation(self):
        try:
            response = requests.get('http://'+self.ip+':8888/net', timeout=5)
            results = response.json()
            if len(results) > 0:
                net = results['net']
                prediction = results['prediction']
                anomalyScore = results['anomalyScore']
                anomalyLikelihood = results['anomalyLikelihood']
                utility_net = results['utility_net']
                net_axis=[net, prediction, anomalyScore, anomalyLikelihood, utility_net]
        except:
            net_axis=[-1, -1, -1, -1, -1]
            pass
        finally:
            pass 
        return np.array(net_axis)
    def get_disk_observation(self):
        try:
            response = requests.get('http://'+self.ip+':8888/disk', timeout=5)
            if response is not None:
                results = response.json()
                if len(results) > 0:
                    disk = results['disk']
                    prediction = results['prediction']
                    anomalyScore = results['anomalyScore']
                    anomalyLikelihood = results['anomalyLikelihood']
                    utility_disk = results['utility_disk']
            disk_axis=[disk, prediction, anomalyScore, anomalyLikelihood, utility_disk]
        except:
            disk_axis=[-1, -1, -1, -1, -1]
            pass
        finally:
            
            pass
        return np.array(disk_axis)

    def get_current_state(self):
        current_state = self.state
         
        return current_state
    def closeFile(self):
        self.fileHandle.close()
    def getNumberofNode(self):
        try:
            prometheus= self.ip
            tstart = time.time()
            end = str(tstart+360)
            start = str(tstart)
            node = 1
            q = 'count(node_meta%20*%20on(instance)%20group_left(node_name)%20node_meta%7Bnode_id%3D~".%2B"%7D)'
            q1 = 'count(node_meta * on(instance) group_left(node_name) node_meta{node_id=~"$node_id"})'
            response = requests.get('http://admin:admin@'+prometheus+':9090/api/v1/query_range?query='+q+'&start='+start+'&end='+ end + '&step=120', timeout=10)
            if response is not None:
                results = response.json()
                Data = results['data']['result']
                print(len(Data))
                if len(Data)> 0:
                    Value = Data[0]['values']
                    node = Value[0][1]
            else:
                node=1
            return int(node)
        except:
            node=1
        finally:
           
            pass
        return node