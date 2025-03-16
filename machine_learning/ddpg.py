from keras import Input, Model
from keras.src.layers import Dense, Concatenate
from keras.src.optimizers import Adam
import numpy as np
import tensorflow as tf
import random
from collections import deque


TRAINING_BATCH_SIZE = 64
REPLAY_MEMORY_MIN_SIZE = 50000
REPLAY_MEMORY_MAX_SIZE = 50_000_000
TAU = 0.0025
THETA = 0.2
MU = 0
DT = 0.001
STD = 0.2
GAMMA = 0.99
VERBOSE = 0
NOISE_GAUSSIAN = 0
NOISE_ORNSTEIN = 1


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
    x = Dense(512, activation="relu")(input_layer)
    x = Dense(384, activation="relu")(x)
    x = Dense(256, activation="relu")(x)
    return x


class DDPGAgent:
    def __init__(self, state_dim, action_dim, batch=TRAINING_BATCH_SIZE, replay_memory_size=REPLAY_MEMORY_MAX_SIZE, noise_type=NOISE_GAUSSIAN):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.batch_size = batch
        self.noises = {}
        self.noise_type = noise_type
        # Actor network & its target
        self.actor = build_actor(state_dim, action_dim)
        self.actor.compile(optimizer=Adam(), loss="mse")
        self.target_actor = build_actor(state_dim, action_dim)

        # Critic network & its target
        self.critic = build_critic(state_dim, action_dim)
        self.critic.compile(optimizer=Adam(), loss="mse")
        self.target_critic = build_critic(state_dim, action_dim)

        # Initialize target networks
        self.target_actor.set_weights(self.actor.get_weights())
        self.target_critic.set_weights(self.critic.get_weights())

        # Replay memory for RL fine-tuning
        self.memory = deque(maxlen=replay_memory_size)

    def update_target_networks(self, tau=TAU):
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

    def ornstein_uhlenbeck_process(self, x, theta=THETA, mu=MU, dt=DT, std=STD):
        return x + theta * (mu - x) * dt + std * np.sqrt(dt) * np.random.normal(size=2)

    def get_action(self, state, explore_noise=STD, worker_id=0):
        state_input = np.expand_dims(state, axis=0)
        predicted_action = self.actor.predict(state_input, verbose=0)[0]
        if self.noise_type == NOISE_GAUSSIAN:
            noise = np.random.normal(0, explore_noise, size=self.action_dim)
        else:
            noise = self.ornstein_uhlenbeck_process(self.noises.get(worker_id, np.random.normal(0, explore_noise, size=self.action_dim)), std=explore_noise)
            self.noises[worker_id] = noise

        action = np.clip(predicted_action + noise, -1, 1)
        return np.array(action, dtype=np.float32).flatten()

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def train_ddpg(self, gamma=GAMMA):
        if len(self.memory) < REPLAY_MEMORY_MIN_SIZE:
            return

        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        states = np.array(states)
        actions = np.array(actions)
        rewards = np.array(rewards)
        next_states = np.array(next_states)
        dones = np.array(dones, dtype=np.float32)

        # Compute target Q-values using the target networks
        target_actions = self.target_actor.predict(next_states, verbose=VERBOSE)
        target_q_values = self.target_critic.predict([next_states, target_actions], verbose=VERBOSE)
        y = rewards + gamma * (1 - dones) * target_q_values.flatten()

        loss = self.critic.train_on_batch([states, actions], y, return_dict=True)
        if VERBOSE:
            print(loss)

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
        return True

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
