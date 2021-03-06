from keras.layers import Conv2D, MaxPooling2D, Dense, Flatten, Input, concatenate, Bidirectional, LSTM, Reshape, UpSampling2D, Activation, Conv2DTranspose, Conv1D, BatchNormalization, GlobalAveragePooling2D
from keras.models import Model, load_model
from keras.optimizers import Adam, Adagrad
from keras.callbacks import TensorBoard, LambdaCallback
from keras.utils.generic_utils import get_custom_objects
from keras.layers import ThresholdedReLU, PReLU, ReLU
import keras.backend as K
import tensorflow as tf
from data_utilities.generator import Native_DataGenerator_for_StructuralSimilarityModel_Autoencoder
from encoder import encode_number
import numpy as np
DIM = 9


def swish(x):
    return K.sigmoid(x) * x


get_custom_objects().update({'swish': Activation(swish)})


def create_network():
    input = Input(shape=(DIM,))

    def common_network():
        layers = [
                  Dense(1000, activation=ReLU(max_value=1.0)),
                  Dense(600, activation=ReLU(max_value=1.0)),
                  Dense(300, activation=ReLU(max_value=1.0)),
                  Dense(100, activation=ReLU(max_value=1.0)),
                  Dense(10, activation=ReLU(max_value=1.0)),
                  Dense(3, activation=ReLU(max_value=1.0)),
                  Dense(10, activation=ReLU(max_value=1.0)),
                  Dense(100, activation=ReLU(max_value=1.0)),
                  Dense(300, activation=ReLU(max_value=1.0)),
                  Dense(600, activation=ReLU(max_value=1.0)),
                  Dense(1000, activation=ReLU(max_value=1.0)),
                  Dense(9, activation=ReLU(max_value=1.0))
        ]

        def shared_layers(x):
            for layer in layers:
                x = layer(x)
            return x

        return shared_layers

    common_net = common_network()
    out = common_net(input)
    model = Model(inputs=[input], outputs=out)

    return model


def epoch_test(epoch, logs):
    st = np.random.randint(2, size=(1, 9)).astype(np.float)
    print(st)
    print(model.predict(st))

    st = np.random.randint(2, size=(1, 9)).astype(np.float)
    print(st)
    print(model.predict(st))


epoch_end_callback = LambdaCallback(on_epoch_end=epoch_test)


model = create_network()
model.summary()
model.compile(optimizer=Adam(lr=0.001, clipvalue=1.0), loss='mean_squared_error')
model_name = 'model_structuralsimilarity_autoencoder'
tensorboard = TensorBoard(log_dir='./logs/model_structuralsimilarity/' + model_name, histogram_freq=0, batch_size=200,
                          write_graph=True, write_grads=False, write_images=False, embeddings_freq=0,
                          embeddings_layer_names=None, embeddings_metadata=None, embeddings_data=None,
                          update_freq='batch')

data_generator = Native_DataGenerator_for_StructuralSimilarityModel_Autoencoder(batch_size=20)
model.fit_generator(generator=data_generator, shuffle=True, epochs=100, workers=4, use_multiprocessing=False, callbacks=[tensorboard, epoch_end_callback])
model.save(filepath='trained_models/'+model_name+'.h5')

