from keras.layers import Conv2D, MaxPooling2D, Dense, Flatten, Input, concatenate, Bidirectional, LSTM, Reshape
from keras.models import Model, load_model
from keras.optimizers import Adam, Adagrad
from keras.callbacks import TensorBoard, LambdaCallback
from data_utilities.generator import Native_DataGenerator_for_StructuralSimilarityModel_SimilaritySpace3x3
import time
import keras.backend as K
import tensorflow as tf
DIM = 4


def create_network():

    input_a = Input(shape=(DIM,))
    input_b = Input(shape=(DIM,))


    def common_network():
        layers = [Reshape((1, 2, 2)),
                  Conv2D(filters=200, kernel_size=(2, 2), kernel_initializer='glorot_uniform',
                         input_shape=(1, 2, 2), data_format='channels_first',
                         use_bias=True, activation='relu', padding='valid')
                  ]

        def shared_layers(x):
            for layer in layers:
                x = layer(x)
            return x

        return shared_layers


    common_net = common_network()
    out_a = Flatten()(common_net(input_a))
    out_b = Flatten()(common_net(input_b))

    concat_out = concatenate([out_a, out_b])

    x = concat_out
    x = Dense(activation='relu', units=200, use_bias=True)(x)
    x = Dense(activation='relu', units=100, use_bias=True)(x)
    x = Dense(activation='relu', units=10, use_bias=True)(x)
    out = Dense(activation='relu', units=1, use_bias=True)(x)

    model = Model(inputs=[input_a, input_b], outputs=out)

    return model



model = create_network()
model.summary()
model.compile(optimizer=Adam(lr=0.001), loss='mean_squared_error')
model_name = 'model_structuralsimilarity_similarityspace3x3'
tensorboard = TensorBoard(log_dir='./logs/model_structuralsimilarity/' + model_name +time.strftime("%Y%m%d%H%M%S"), histogram_freq=0, batch_size=120,
                          write_graph=True, write_grads=False, write_images=False, embeddings_freq=0,
                          embeddings_layer_names=None, embeddings_metadata=None, embeddings_data=None,
                          update_freq='epoch')



data_generator = Native_DataGenerator_for_StructuralSimilarityModel_SimilaritySpace3x3(batch_size=20)
model.fit_generator(generator=data_generator, shuffle=True, epochs=300, workers=4, use_multiprocessing=False, callbacks=[tensorboard])
model.save(filepath='trained_models/'+model_name+'.h5')