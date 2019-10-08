from gym.envs.registration import register

register(
    id='Pyclimb-v0',
    entry_point='gym_climb.envs:ClimbEnv',
    max_episode_steps=9999999,
)
