from keras import Input, Model
from keras.src.layers import Dense, Concatenate
from keras.src.optimizers import Adam
import numpy as np
import tensorflow as tf
import gymnasium as gym
import random
from collections import deque

import time


from utils.plotit import LivePlotter

# Optional: Monkey-patch np.bool8 if missing
if not hasattr(np, 'bool8'):
    np.bool8 = np.bool_


BATCH_SIZE = 256


# ==== BUILD NEURAL NETWORKS ====
def build_actor(state_dim, action_dim):
    inputs = Input(shape=(state_dim,))
    x = build_insides(inputs)

    outputs = Dense(action_dim, activation="tanh")(x)  # Outputs in [-1, 1]
    return Model(inputs, outputs)


def build_critic(state_dim, action_dim):
    state_input = Input(shape=(state_dim,))
    action_input = Input(shape=(action_dim,))
    x = Concatenate()([state_input, action_input])
    x = build_insides(x)
    outputs = Dense(1, activation="linear")(x)  # Q-value output
    return Model([state_input, action_input], outputs)

def build_insides(input_layer):
    x = Dense(128, activation="relu")(input_layer)
    x = Dense(86, activation="relu")(x)
    x = Dense(64, activation="relu")(x)
    return x

# ==== DDPG AGENT CLASS ====
class DDPGAgent:
    def __init__(self, state_dim, action_dim, noise_chance=0.9):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.noise_chance = noise_chance

        # Actor network & its target
        self.actor = build_actor(state_dim, action_dim)
        self.actor.compile(optimizer=Adam(learning_rate=0.00015), loss="mse")
        self.target_actor = build_actor(state_dim, action_dim)

        # Critic network & its target
        self.critic = build_critic(state_dim, action_dim)
        self.critic.compile(optimizer=Adam(learning_rate=0.0003), loss="mse")
        self.target_critic = build_critic(state_dim, action_dim)

        # Initialize target networks
        self.target_actor.set_weights(self.actor.get_weights())
        self.target_critic.set_weights(self.critic.get_weights())

        # Replay memory for RL fine-tuning
        self.memory = deque(maxlen=150000)

    def update_target_networks(self, tau=0.0025):
        # Soft-update: target = tau * source + (1 - tau) * target
        actor_weights = self.actor.get_weights()
        target_actor_weights = self.target_actor.get_weights()
        new_target_actor_weights = [tau * w + (1 - tau) * tw
                                    for w, tw in zip(actor_weights, target_actor_weights)]
        self.target_actor.set_weights(new_target_actor_weights)

        critic_weights = self.critic.get_weights()
        target_critic_weights = self.target_critic.get_weights()
        new_target_critic_weights = [tau * w + (1 - tau) * tw
                                     for w, tw in zip(critic_weights, target_critic_weights)]
        self.target_critic.set_weights(new_target_critic_weights)

    def get_action(self, state, explore_noise=0.1):
        """
        Returns an action for a given state.
        - With probability bot_advice_prob, uses the bot's action.
        - Otherwise, uses the actor's prediction (plus exploration noise).
        Ensures the returned action is a flat NumPy array of shape (2,).
        """
        state_input = np.expand_dims(state, axis=0)
        predicted_action = self.actor.predict(state_input, verbose=0)[0]

        noise = np.random.normal(0, explore_noise, size=self.action_dim)
        action = np.clip(predicted_action + noise, -1, 1)# if random.random() < self.noise_chance else predicted_action
        return np.array(action, dtype=np.float32).flatten()

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def train_ddpg(self, gamma=0.99):
        if len(self.memory) < 5000:
            return

        batch = random.sample(self.memory, BATCH_SIZE)
        states, actions, rewards, next_states, dones = zip(*batch)
        states = np.array(states)
        actions = np.array(actions)
        rewards = np.array(rewards)
        next_states = np.array(next_states)
        dones = np.array(dones, dtype=np.float32)

        # Compute target Q-values using the target networks
        target_actions = self.target_actor.predict(next_states, verbose=0)
        target_q_values = self.target_critic.predict([next_states, target_actions], verbose=0)
        y = rewards + gamma * (1 - dones) * target_q_values.flatten()

        # Train the critic network on this batch
        self.critic.train_on_batch([states, actions], y)

        # Train the actor network using policy gradients.
        # Convert states to a tensor so both inputs to the critic are tensors.
        states_tensor = tf.convert_to_tensor(states, dtype=tf.float32)
        with tf.GradientTape() as tape:
            actions_pred = self.actor(states_tensor)
            q_values = self.critic([states_tensor, actions_pred])
            actor_loss = -tf.reduce_mean(q_values)
        grads = tape.gradient(actor_loss, self.actor.trainable_variables)
        self.actor.optimizer.apply_gradients(zip(grads, self.actor.trainable_variables))

        # Soft-update target networks
        self.update_target_networks()

    def save_weights(self, path):
        """Save weights of actor, critic, and their target networks."""
        self.actor.save_weights(f"{path}_actor.weights.h5")
        self.critic.save_weights(f"{path}_critic.weights.h5")
        self.target_actor.save_weights(f"{path}_target_actor.weights.h5")
        self.target_critic.save_weights(f"{path}_target_critic.weights.h5")
        print("Weights saved successfully.")

    def load_weights(self, path):
        """Load weights of actor, critic, and their target networks."""
        self.actor.load_weights(f"{path}_actor.weights.h5")
        self.critic.load_weights(f"{path}_critic.weights.h5")
        self.target_actor.load_weights(f"{path}_target_actor.weights.h5")
        self.target_critic.load_weights(f"{path}_target_critic.weights.h5")
        print("Weights loaded successfully.")

# ==== MAIN SCRIPT ====
if __name__ == "__main__":
    env = gym.make("LunarLanderContinuous-v3")

    agent = DDPGAgent(state_dim=env.observation_space.shape[0], action_dim=env.action_space.shape[0])

    def run():

        agent.load_weights('Lunar-004-ep.468')

        # # === STEP 1: Fine-Tuning with DDPG Reinforcement Learning ===
        num_episodes = 500
        print("Starting RL fine-tuning...")
        live_plot = LivePlotter("Live RL Training Progress", "rl_training_plot.png")
        max_reward = -99999999999999999
        rewards = []
        for episode in range(num_episodes):
            state, info = env.reset()
            total_reward = 0
            noise = 0.5 * (num_episodes - episode) / num_episodes
            for t in range(350):
                action = agent.get_action(state, explore_noise=noise)
                next_state, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated
                agent.remember(state, action, reward, next_state, done)
                if t % 10 == 0:
                    agent.train_ddpg()
                state = next_state
                total_reward += reward
                if done:
                    break
            # agent.train_ddpg()
            if total_reward > max_reward and episode > 20:
                max_reward = total_reward
                agent.save_weights(f"weights/Lunar-004-ep.{episode}")
            rewards.append(total_reward)
            if episode % 5 == 0:
                live_plot.plot(rewards)
            print(f"Episode {episode}, Reward: {total_reward}")
        live_plot.save_plot('training_plot.png')

    def test():
        # === STEP 2: Testing the Trained Agent ===
        print("Testing trained agent...")
        env = gym.make("LunarLanderContinuous-v3", render_mode="human")

        for episode in range(10):
            state, info = env.reset()
            total_reward = 0
            for t in range(500):
                env.render()
                action = agent.get_action(state, explore_noise=0.0)  # No exploration noise during testing
                next_state, reward, terminated, truncated, info = env.step(action)
                # print(f'{t}: {round(float(reward),2)} {list(action)=}')
                done = terminated or truncated
                total_reward += reward
                state = next_state
                if done:
                    break
            print(f"Test Episode {episode}, Reward: {total_reward}")
            time.sleep(1)
        env.close()

    run()
    test()