#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from __future__ import division, print_function, unicode_literals
import csv
import shutil
import os
import time
import requests
import subprocess
from subprocess import call
import numpy as np
import tensorflow as tf
from rl.callbacks import FileLogger, ModelIntervalCheckpoint
import pandas as pd 


from keras import backend as K



import numpy as np
import gym

from keras.models import Sequential
from keras.layers import Dense, Activation, Flatten
from keras.optimizers import Adam

from rl.agents.dqn import DQNAgent
from rl.policy import BoltzmannQPolicy
from rl.memory import SequentialMemory 
from keras.callbacks import TensorBoard

def reset_graph(seed=42):
    tf.reset_default_graph()
    tf.set_random_seed(seed)
    np.random.seed(seed)

def save_fig(fig_id, tight_layout=True):
    path = os.path.join(PROJECT_ROOT_DIR, "images", CHAPTER_ID, fig_id + ".png")
    print("Saving figure", fig_id)
    if tight_layout:
        plt.tight_layout()
    plt.savefig(path, format='png', dpi=300)


# #   MDP 
# 

# ## Deep Q-Learning
# 

# In[1]:


import gym
import gym_foo

env = gym.make('foo-v16')


# In[2]:


env.observation_space.shape


# In[3]:


nb_actions= env.action_space.n



# In[4]:





# In[ ]:





# In[ ]:


reset_graph()


# In[ ]:


# Next, we build a very simple model.
model = Sequential()
model.add(Flatten(input_shape=(1,) + env.observation_space.shape))
model.add(Dense(16))
model.add(Activation('relu'))
model.add(Dense(16))
model.add(Activation('relu'))
model.add(Dense(16))
model.add(Activation('relu'))
model.add(Dense(nb_actions))
model.add(Activation('linear'))


# In[ ]:


model.summary()


# In[ ]:


memory = SequentialMemory(limit=2000, window_length=1)
policy = BoltzmannQPolicy(tau=1.)
#dqn = DQNAgent(model=model, nb_actions=nb_actions, memory=memory, nb_steps_warmup=100,
#               target_model_update=1e-2, policy=policy)
dqn = DQNAgent(model=model, nb_actions=nb_actions, policy=policy, memory=memory,
                nb_steps_warmup=1000, gamma=.99, target_model_update=10000,
               train_interval=4, delta_clip=1.)
dqn.compile(Adam(lr=1e-3), metrics=['mae'])


# In[ ]:



ENV_NAME="aftersubmissionv19"
weights_filename = 'dqn_{}_weights.h5f'.format(ENV_NAME)
checkpoint_weights_filename = 'dqn_' + ENV_NAME + '_weights_{step}.h5f'
 
log_filename = 'dqn_{}_log.json'.format(ENV_NAME)
callbacks = [ModelIntervalCheckpoint(checkpoint_weights_filename, interval=25000)]
callbacks += [FileLogger(log_filename, interval=100)]
callbacks += [TensorBoard(log_dir='./dqn_logsv6/', histogram_freq=0, write_graph=False)]
dqn.fit(env, callbacks=callbacks, nb_steps=5000, log_interval=25000,verbose=1)


# In[ ]:


dqn.save_weights(weights_filename, overwrite=True)


# In[ ]:




# In[ ]:



dqn.test(env, nb_episodes=10,  visualize=False)

env.close()

# In[ ]:




