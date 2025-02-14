import os
# Set environment variables to encourage TensorFlow to use multiple cores
os.environ["OMP_NUM_THREADS"] = "15"
os.environ["TF_NUM_INTEROP_THREADS"] = "15"
os.environ["TF_NUM_INTRAOP_THREADS"] = "15"
import threading
import time
import numpy as np
from queue import Queue
from collections import defaultdict

import gymnasium as gym
from machine_learning.ddpg import DDPGAgent, NOISE_ORNSTEIN
from utils.plotit import LivePlotter


# Global parameters
NUM_WORKERS = 150  # Number of worker threads (each with its own environment)
NUM_EPISODES = 400  # Number of episodes per worker
MAX_STEPS = 300  # Maximum steps per episode

# Create a global agent
agent = DDPGAgent(state_dim=8, action_dim=2, noise_type=NOISE_ORNSTEIN)
print(f'{agent.actor.summary()}')
print(f'{agent.critic.summary()}')

# agent.load_weights('weights/Lunar-multi-008-w.29')

name = "Lunar-multi-011"
scores = defaultdict(list)


class BatchedActionSelector:
    """Handles batched inference for action selection, reducing per-call overhead."""

    def __init__(self, agent, batch_interval=0.001):
        self.agent = agent
        self.requests = Queue()  # Incoming (request_id, state, noise) tuples
        self.results = {}  # Computed actions by request_id
        self.condition = threading.Condition()
        self.batch_interval = batch_interval
        self.running = True
        self.processor = threading.Thread(target=self._process_batches, daemon=True)
        self.processor.start()

    def request_action(self, state, request_id, noise=0.0):
        """Worker thread calls this to get an action based on a state."""
        self.requests.put((request_id, state, noise))
        with self.condition:
            while request_id not in self.results:
                self.condition.wait()
            return self.results.pop(request_id)

    def _process_batches(self):
        """Processes queued states in batches to minimize inference calls."""
        while self.running:
            batch = []
            while not self.requests.empty():
                batch.append(self.requests.get())
            if batch:
                req_ids, states, noises = zip(*batch)
                states_batch = np.array(states)
                actions_batch = self.agent.actor.predict(states_batch, verbose=0)  # Batched prediction
                actions_batch += np.array(noises).reshape(-1, 1)  # Apply noise
                with self.condition:
                    for rid, action in zip(req_ids, actions_batch):
                        self.results[rid] = action
                    self.condition.notify_all()
            else:
                time.sleep(self.batch_interval)

    def stop(self):
        """Stops the batch processing thread."""
        self.running = False
        self.processor.join()


# Create the global batched action selector
batched_action_selector = BatchedActionSelector(agent)


def worker_thread(worker_id, num_episodes):
    """Worker thread: runs its own environment and collects experiences."""
    env = gym.make("LunarLanderContinuous-v3")
    unique_counter = 0

    for ep in range(num_episodes):
        state, info = env.reset()
        total_reward = 0

        for _ in range(MAX_STEPS):
            noise = 0.35 * (num_episodes - ep) / num_episodes + 0.05
            if len(agent.memory) < 15_000:
                action = np.random.normal(0, 2, size=2)
            else:
                request_id = f"{worker_id}_{unique_counter}"
                unique_counter += 1
                action = batched_action_selector.request_action(state, request_id, noise)
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            agent.remember(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward
            if done:
                break

        print(f"Worker {worker_id} Episode {ep} Reward: {total_reward}")
        scores[ep].append(total_reward)

    agent.save_weights(f"weights/{name}-w.{worker_id}")
    env.close()


def training_thread():
    """A separate thread that continuously trains the agent from the replay buffer."""
    while True:
        agent.train_ddpg()
        time.sleep(0.001)  # Short sleep to yield CPU


if __name__ == "__main__":
    trainer = threading.Thread(target=training_thread, daemon=True)
    trainer.start()

    workers = []
    for i in range(NUM_WORKERS):
        t = threading.Thread(target=worker_thread, args=(i, NUM_EPISODES))
        t.start()
        workers.append(t)

    live_plot = LivePlotter("Live RL Progress multi", "rl_multi_plot.png")

    while True:
        live_plot.plot([sum(x) / (len(x) or 1) for x in scores.values()])
        time.sleep(1)

    for t in workers:
        t.join()

    batched_action_selector.stop()
    print("All workers finished. Training complete.")
