import gym
from gym import spaces
import numpy as np
from gym_climb.envs.pyclimb_2d import PyClimb2D

class ClimbEnv(gym.Env):
    metadata = {'render.modes' : ['human']}
    def __init__(self):
        print("init")
        self.action_space = spaces.Discrete(2)
        # degree, speed, body height, next mountain
        #self.observation_space = spaces.Box(np.array([0, -2, 0, 0, 0]), np.array([360, 5, 9, 5, 5]), dtype=np.int)
        self.observation_space = spaces.Box(np.array([0, -2]), np.array([360, 5]), dtype=np.int)
        self.is_view = True
        self.pyclimb = PyClimb2D(self.is_view)
        self.memory = []

    def reset(self):
        del self.pyclimb
        self.pyclimb = PyClimb2D(self.is_view)
        obs = self.pyclimb.observe()
        return obs

    def step(self, action):
        self.pyclimb.action(action)
        reward = self.pyclimb.evaluate()
        done = self.pyclimb.is_done()
        obs = self.pyclimb.observe()
        return obs, reward, done, {}

    def render(self, mode="human", close=False):
        if self.is_view:
            self.pyclimb.view()

    def set_view(self, flag):
        self.is_view = flag

    def save_memory(self, file):
        np.save(file, self.memory)
        print(file + " saved")

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
