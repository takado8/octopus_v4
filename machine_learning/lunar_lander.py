
import gymnasium as gym

import time

from machine_learning.ddpg import DDPGAgent
from utils.plotit import LivePlotter


if __name__ == "__main__":
    env = gym.make("LunarLanderContinuous-v3")

    agent = DDPGAgent(state_dim=env.observation_space.shape[0], action_dim=env.action_space.shape[0], batch=32)
    print(f'{agent.actor.summary()}')
    print(f'{agent.critic.summary()}')
    # agent.load_weights('weights/Lunar-007-ep.1350')
    # agent.load_weights('weights/Lunar-multi-005-ep.1406')
    agent.load_weights('weights/Lunar-multi-008-w.60')
    # agent.load_weights('weights/Lunar-multi-010-w.6 ')
    def train(name):

        time_consumed_net = 0
        time_consumed_alg = 0

        # # === STEP 1: Fine-Tuning with DDPG Reinforcement Learning ===
        num_episodes = 10000
        max_steps = 500
        print("Starting RL fine-tuning...")
        live_plot = LivePlotter("Live RL Training Progress", "rl_training_plot.png")
        max_reward = -99999999999999999
        rewards = []
        for episode in range(num_episodes):

            state, info = env.reset()
            total_reward = 0
            noise = 0.25 * (num_episodes - episode) / num_episodes
            for t in range(max_steps):
                start = time.perf_counter()
                action = agent.get_action(state, explore_noise=noise)
                end =  time.perf_counter()
                time_consumed_net += end - start
                next_state, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated
                # reward = reward / 100
                agent.remember(state, action, reward, next_state, done)

                # if t % 2 == 0:
                start = time.perf_counter()
                agent.train_ddpg()
                end = time.perf_counter()
                time_consumed_alg += end - start
                state = next_state
                total_reward += reward
                if done:
                    break
            if total_reward > max_reward and episode > 20 or episode % 100 == 0 and episode != 0:
                max_reward = total_reward
                agent.save_weights(f"weights/{name}-ep.{episode}")
            rewards.append(total_reward)
            if episode % 5 == 0:
                live_plot.plot(rewards)
                print(f'{time_consumed_net=}\n{time_consumed_alg=}')

            print(f"Episode {episode}, Reward: {total_reward}")
        live_plot.save_plot('training_plot.png')
        agent.save_weights(f"weights/{name}-final")

    def test():
        print("Testing trained agent...")
        env = gym.make("LunarLanderContinuous-v3", render_mode="human")
        # env = gym.make("LunarLanderContinuous-v3", render_mode="human", enable_wind=True, wind_power=20.0, turbulence_power=2.0)

        for episode in range(10):
            state, info = env.reset()
            total_reward = 0
            for t in range(250):
                # print(t)
                env.render()
                action = agent.get_action(state, explore_noise=0.0)
                next_state, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated
                total_reward += reward
                state = next_state
                if done:
                    break
            print(f"Test Episode {episode}, Reward: {total_reward}")
            time.sleep(1)
        env.close()

    # train('Lunar-007')
    test()