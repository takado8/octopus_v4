import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'   # has to be before tf import

import keras
import tensorflow as tf


class CNN:
    CNN_TYPE_CLASSIC = 0
    CNN_TYPE_DUELING_DQN = 1

    def __init__(self, img_rows, img_cols, colors=3, nb_of_actions=4, model_path=None,
                 net_type=CNN_TYPE_CLASSIC):
        self.net_type = net_type
        self.img_rows = img_rows
        self.img_cols = img_cols
        self.colors = colors
        self.input_shape = (img_rows, img_cols, colors)
        self.nb_of_actions = nb_of_actions
        self.EXE_DIR_PATH = os.path.dirname(__file__)
        self.model_path = model_path
        if model_path:
            self.model = self.load_model()
            if not self.model:
                self.model = self.new_CNN()
        else:
            self.model = self.new_CNN()

    def new_CNN(self, compile_model=True):
        print('Creating new_CNN model.')
        if self.net_type == self.CNN_TYPE_CLASSIC:
            return self._new_classic_CNN(compile_model)
        elif self.net_type == self.CNN_TYPE_DUELING_DQN:
            return self._new_dueling_CNN(compile_model)

    def _new_classic_CNN(self, compile_model=True):
        model = keras.models.Sequential()
        model.add(keras.layers.Conv2D(32, (3, 3), padding='same', input_shape=self.input_shape))
        model.add(keras.layers.Activation('relu'))
        model.add(keras.layers.MaxPooling2D(pool_size=(3, 3), padding='same'))
        model.add(keras.layers.Dropout(0.2))

        model.add(keras.layers.Conv2D(64, (3, 3), padding='same'))
        model.add(keras.layers.Activation('relu'))
        model.add(keras.layers.MaxPooling2D(pool_size=(3, 3), padding='same'))
        model.add(keras.layers.Dropout(0.2))
        #
        model.add(keras.layers.Conv2D(64, (2, 2), padding='same'))
        model.add(keras.layers.Activation('relu'))
        model.add(keras.layers.MaxPooling2D(pool_size=(2, 2), padding='same'))
        model.add(keras.layers.Dropout(0.2))

        # model.add(keras.layers.Conv2D(256, (3, 3), padding='same'))
        # model.add(keras.layers.Activation('relu'))
        # model.add(keras.layers.MaxPooling2D(pool_size=(3, 3), padding='same'))
        # model.add(keras.layers.Dropout(0.2))

        #
        # model.add(keras.layers.Conv2D(512, (3, 3)))
        # model.add(keras.layers.Activation('relu'))
        # model.add(keras.layers.MaxPooling2D(pool_size=(2, 2)))
        # model.add(keras.layers.Dropout(0.2))
        model.add(keras.layers.Flatten())
        #
        model.add(keras.layers.Dense(256, activation='relu'))
        model.add(keras.layers.Dropout(0.2))

        model.add(keras.layers.Dense(256, activation='relu'))
        model.add(keras.layers.Dropout(0.2))

        model.add(keras.layers.Dense(self.nb_of_actions, activation='tanh'))
        if compile_model:
            opt = keras.optimizers.Adam()
            model.compile(optimizer=opt, loss='MSE', metrics=['accuracy'])
        print('New model created.')
        model.summary()
        return model

    # noinspection PyUnresolvedReferences
    def _new_dueling_CNN(self, compile_model=True):
        inputs = keras.layers.Input(shape=self.input_shape)

        net = keras.layers.Conv2D(32, (3, 3), padding='same')(inputs)
        net = keras.layers.Activation('relu')(net)
        net = keras.layers.MaxPooling2D(pool_size=(3, 3), padding='same')(net)
        # net = keras.layers.Dropout(0.2)(net)

        net = keras.layers.Conv2D(64, (3, 3), padding='same')(net)
        net = keras.layers.Activation('relu')(net)
        net = keras.layers.MaxPooling2D(pool_size=(3, 3), padding='same')(net)
        # net = keras.layers.Dropout(0.2)(net)

        net = keras.layers.Conv2D(128, (2, 2), padding='same')(net)
        net = keras.layers.Activation('relu')(net)
        net = keras.layers.MaxPooling2D(pool_size=(2, 2), padding='same')(net)
        # net = keras.layers.Dropout(0.2)(net)

        net = keras.layers.Flatten()(net)

        # net = keras.layers.Dense(128, activation='relu')(net)

        advantage = keras.layers.Dense(512, activation='relu')(net)
        advantage = keras.layers.Dense(self.nb_of_actions)(advantage)

        value = keras.layers.Dense(512, activation='relu')(net)
        value = keras.layers.Dense(1)(value)
        # now to combine the two streams
        advantage = keras.layers.Lambda(lambda advt: advt - tf.reduce_mean(advt, axis=-1, keepdims=True))(advantage)
        value = keras.layers.Lambda(lambda value: tf.tile(value, [1, self.nb_of_actions]))(value)
        final = keras.layers.Add()([value, advantage])
        model = keras.models.Model(inputs=inputs, outputs=final)
        if compile_model:
            opt = keras.optimizers.Adam()
            model.compile(optimizer=opt, loss='MSE', metrics=['accuracy'])
        print('New model created.')
        model.summary()
        return model

    def reshape_numpy_input(self, array):
        return array.reshape((-1, self.img_rows, self.img_cols, self.colors))

    def save_model(self):
        if self.model_path:
            if self.net_type == self.CNN_TYPE_CLASSIC:
                self.model.save(self.model_path)
            elif self.net_type == self.CNN_TYPE_DUELING_DQN:
                self.model.save_weights(self.model_path)
            print('Model saved at: {}'.format(self.model_path))
        else:
            print('model path not specified in object field. model_path = \'{}\''.format(self.model_path))

    def load_model(self):
        if self.model_path:
            import os
            if os.path.isfile(self.model_path):
                model = None
                if self.net_type == self.CNN_TYPE_CLASSIC:
                    model = keras.models.load_model(self.model_path)
                elif self.net_type == self.CNN_TYPE_DUELING_DQN:
                    model = self.new_CNN()
                    model.load_weights(self.model_path)
                    print('weights loaded')
                print('Model loaded: {}'.format(self.model_path))
                return model
            else:
                print('model file does not exist. model_path = \'{}\''.format(self.model_path))
        else:
            print('model path not specified in object field. model_path = \'{}\''.format(self.model_path))